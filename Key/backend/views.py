from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Student, EntryLog, LostCardScan
from .serializers import (
    StudentSerializer, 
    EntryLogSerializer, 
    LostCardScanSerializer,
    UserSerializer,
    CustomTokenObtainPairSerializer,
    RegisterSerializer
)
import uuid

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class StudentRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Get the student profile
        student = Student.objects.get(user=user)
        
        # Return student data along with tokens
        refresh = RefreshToken.for_user(user)
        
        student_serializer = StudentSerializer(student, context={'request': request})
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'status': user.status,
                'qr_code_url': student_serializer.data['qr_code_url'],
                'created_at': student.created_at,
                'is_student': user.is_student,
            },
            'student': student_serializer.data
        }, status=status.HTTP_201_CREATED)


class LogoutView(views.APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StudentListView(generics.ListAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


class StudentDetailView(generics.RetrieveUpdateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    def get_object(self):
        # If student is requesting their own profile
        if self.request.user.is_student and hasattr(self.request.user, 'student_profile'):
            if 'id' not in self.kwargs:
                return self.request.user.student_profile
            elif str(self.request.user.student_profile.id) == self.kwargs['id']:
                return self.request.user.student_profile
        
        # If admin or other authorized user is requesting
        if self.request.user.is_admin or self.request.user.is_security:
            return super().get_object()
        
        # Deny access if student tries to access another student's profile
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("You do not have permission to access this resource.")


class ReportLostCardView(views.APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk=None):
        # If no ID provided, use the student's own ID
        if pk is None and hasattr(request.user, 'student_profile'):
            student = request.user.student_profile
        else:
            student = get_object_or_404(Student, id=pk)
            
            # Check permissions: Only the owner or admin can report a card lost
            if not request.user.is_admin and (not hasattr(request.user, 'student_profile') or 
                                              request.user.student_profile.id != student.id):
                return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        
        student.report_lost()
        
        # Send email notification
        try:
            send_mail(
                subject=f'ID Card Reported Lost',
                message=f'Your ID card has been reported as lost. If this was not done by you, please contact the security office immediately.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[student.email],
                fail_silently=False,
            )
        except Exception as e:
            # Continue even if email fails
            pass
        
        return Response({
            'status': 'success',
            'message': f'Card for {student.name} has been reported as lost'
        })


class VerifyQRCodeView(views.APIView):
    """
    API endpoint for scanning QR codes at entry points
    """
    permission_classes = [IsAuthenticated]  # Usually restricted to security personnel or scanning devices
    
    def post(self, request):
        try:
            # Get the QR code data from the request
            qr_data = request.data.get('qr_data')
            location = request.data.get('location', 'Unknown')
            
            if not qr_data:
                return Response({
                    'status': 'error',
                    'message': 'QR code data is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Convert the QR data to UUID and find the student
            student_uuid = uuid.UUID(qr_data)
            student = Student.objects.get(id=student_uuid)
            
            # Check if the card is reported as lost
            if student.status == 'lost':
                # Record the lost card scan
                LostCardScan.objects.create(
                    student=student,
                    location=location
                )
                
                # Send email notification
                try:
                    send_mail(
                        subject=f'Alert: Lost ID Card Used',
                        message=f'Your ID card that was reported as lost has been scanned at {location}. Please contact security immediately.',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[student.email],
                        fail_silently=False,
                    )
                except Exception as e:
                    # Continue even if email fails
                    pass
                
                return Response({
                    'status': 'error',
                    'message': 'This ID card has been reported as lost',
                    'student': {
                        'id': str(student.id),
                        'name': student.name,
                        'admission_number': student.admission_number
                    }
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Check if the card is expired
            if student.status == 'expired':
                return Response({
                    'status': 'error',
                    'message': 'This ID card has expired',
                    'student': {
                        'id': str(student.id),
                        'name': student.name,
                        'admission_number': student.admission_number
                    }
                }, status=status.HTTP_403_FORBIDDEN)
            
            # If card is active, log the entry
            entry_log = EntryLog.objects.create(
                student=student,
                location=location,
                successful=True
            )
            
            return Response({
                'status': 'success',
                'message': 'Access granted',
                'student': {
                    'id': str(student.id),
                    'name': student.name,
                    'admission_number': student.admission_number
                },
                'entry': {
                    'id': entry_log.id,
                    'timestamp': entry_log.timestamp,
                    'location': entry_log.location
                }
            })
            
        except ValueError:
            return Response({
                'status': 'error',
                'message': 'Invalid QR code format'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Student.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Student not found'
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EntryLogListView(generics.ListAPIView):
    serializer_class = EntryLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Students can only see their own logs
        if self.request.user.is_student and hasattr(self.request.user, 'student_profile'):
            return EntryLog.objects.filter(student=self.request.user.student_profile).order_by('-timestamp')
        
        # Admins and security can see all logs
        if self.request.user.is_admin or self.request.user.is_security:
            return EntryLog.objects.all().order_by('-timestamp')
        
        # Return empty queryset for unauthorized users
        return EntryLog.objects.none()


class LostCardScansListView(generics.ListAPIView):
    serializer_class = LostCardScanSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Students can only see their own lost card scans
        if self.request.user.is_student and hasattr(self.request.user, 'student_profile'):
            return LostCardScan.objects.filter(student=self.request.user.student_profile).order_by('-timestamp')
        
        # Admins and security can see all lost card scans
        if self.request.user.is_admin or self.request.user.is_security:
            return LostCardScan.objects.all().order_by('-timestamp')
        
        # Return empty queryset for unauthorized users
        return LostCardScan.objects.none()


class UserDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class RequestNewCardView(views.APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk=None):
        # If no ID provided, use the student's own ID
        if pk is None and hasattr(request.user, 'student_profile'):
            student = request.user.student_profile
        else:
            student = get_object_or_404(Student, id=pk)
            
            # Check permissions: Only the owner or admin can request a new card
            if not request.user.is_admin and (not hasattr(request.user, 'student_profile') or 
                                              request.user.student_profile.id != student.id):
                return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        
        # Reset the student's QR code
        student.qr_code = None
        
        # If the card was lost, make it active again
        if student.status == 'lost':
            student.status = 'active'
        
        # Save to generate a new QR code
        student.save()
        
        # Send email notification
        try:
            send_mail(
                subject=f'New ID Card Generated',
                message=f'A new ID card has been generated for you. Please visit the security office to collect it.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[student.email],
                fail_silently=False,
            )
        except Exception as e:
            # Continue even if email fails
            pass
        
        # Return the updated student data with new QR code
        serializer = StudentSerializer(student, context={'request': request})
        
        return Response({
            'status': 'success',
            'message': f'New card generated for {student.name}',
            'student': serializer.data
        })


class AdminDashboardStatsView(views.APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        # Get counts for dashboard stats
        total_students = Student.objects.count()
        active_students = Student.objects.filter(status='active').count()
        lost_cards = Student.objects.filter(status='lost').count()
        expired_cards = Student.objects.filter(status='expired').count()
        
        # Recent entry logs
        recent_entries = EntryLog.objects.all().order_by('-timestamp')[:10]
        recent_entries_data = EntryLogSerializer(recent_entries, many=True).data
        
        # Recent lost card scans
        recent_lost_scans = LostCardScan.objects.all().order_by('-timestamp')[:10]
        recent_lost_scans_data = LostCardScanSerializer(recent_lost_scans, many=True).data
        
        return Response({
            'total_students': total_students,
            'active_students': active_students,
            'lost_cards': lost_cards,
            'expired_cards': expired_cards,
            'recent_entries': recent_entries_data,
            'recent_lost_scans': recent_lost_scans_data
        })


class BulkImportStudentsView(views.APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    @transaction.atomic
    def post(self, request):
        students_data = request.data.get('students', [])
        created_count = 0
        errors = []
        
        if not students_data:
            return Response({
                'status': 'error',
                'message': 'No student data provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        for student_data in students_data:
            try:
                # Check if student already exists
                admission_number = student_data.get('admission_number')
                if Student.objects.filter(admission_number=admission_number).exists():
                    errors.append({
                        'admission_number': admission_number,
                        'error': 'Student with this admission number already exists'
                    })
                    continue
                
                # Create user with admission number as username
                user = User.objects.create_user(
                    username=admission_number,
                    email=student_data.get('email'),
                    password=User.objects.make_random_password()  # Generate random password
                )
                user.is_student = True
                user.save()
                
                # Create student profile
                student = Student.objects.create(
                    name=student_data.get('name'),
                    email=student_data.get('email'),
                    admission_number=admission_number,
                    user=user
                )
                
                created_count += 1
                
            except Exception as e:
                errors.append({
                    'admission_number': student_data.get('admission_number', 'Unknown'),
                    'error': str(e)
                })
        
        return Response({
            'status': 'success',
            'message': f'Created {created_count} students',
            'created_count': created_count,
            'errors': errors
        })


class ExpireStudentIDView(views.APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def post(self, request, pk):
        student = get_object_or_404(Student, id=pk)
        student.status = 'expired'
        student.save()
        
        # Send email notification
        try:
            send_mail(
                subject=f'ID Card Expired',
                message=f'Your ID card has been marked as expired. Please contact the administration to renew your ID card.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[student.email],
                fail_silently=False,
            )
        except Exception as e:
            # Continue even if email fails
            pass
        
        return Response({
            'status': 'success',
            'message': f'Card for {student.name} has been expired'
        })