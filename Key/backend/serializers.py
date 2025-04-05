from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Student, EntryLog, LostCardScan

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_student', 'is_admin', 'is_security')
        read_only_fields = ('id', 'is_student', 'is_admin', 'is_security')


class StudentSerializer(serializers.ModelSerializer):
    qr_code_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = ['id', 'name', 'email', 'admission_number','status', 'qr_code_url', 'created_at']
        read_only_fields = ['id', 'qr_code_url', 'created_at']
    
    def get_qr_code_url(self, obj):
        if obj.qr_code:
            return self.context['request'].build_absolute_uri(obj.qr_code.url)
        return None


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        try:
            token = super().get_token(user)
            
            # Add custom claims
            token['username'] = user.username
            token['is_student'] = user.is_student
            token['is_admin'] = user.is_admin
            token['is_security'] = user.is_security
            
            if hasattr(user, 'student_profile'):
                token['student_id'] = str(user.student_profile.id)
                token['admission_number'] = user.student_profile.admission_number
            
            return token
        except Exception as e:
            raise serializers.ValidationError(f"Error generating token: {str(e)}")
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add extra response data
        user = self.user
        data['user_id'] = user.id
        data['username'] = user.username
        data['is_student'] = user.is_student
        data['is_admin'] = user.is_admin
        data['is_security'] = user.is_security
        
        
        if hasattr(user, 'student_profile'):
            data['student_id'] = str(user.student_profile.id)
            data['name'] = user.student_profile.name
            data['admission_number'] = user.student_profile.admission_number
            # data['email'] = user.student_profile.email
            # data['status'] = user.student_profile.status
            # if user.student_profile.qr_code:
            #     data['qr_code_url'] = self.context['request'].build_absolute_uri(user.student_profile.qr_code.url)
            # else:
            #     data['qr_code_url'] = None
                
        # print(data)
        return data


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    # password2 = serializers.CharField(write_only=True, required=True)
    name = serializers.CharField(required=True)
    admission_number = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ('admission_number', 'password', 'name', 'email')
    
    def validate(self, attrs):
        # if attrs['password'] != attrs['password2']:
        #     raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        # Check if admission number is unique
        admission_number = attrs['admission_number']
        if User.objects.filter(username=admission_number).exists():
            raise serializers.ValidationError({"admission_number": "Student with this admission number already exists."})
        
        return attrs
    
    def create(self, validated_data):
        # Use admission number as username
        username = validated_data.pop('admission_number')
        # validated_data.pop('password2')
        name = validated_data.pop('name')
        email = validated_data.pop('email')
        
        # Create user with admission number as username
        user = User.objects.create_user(
            username=username,
            email=email,
            **validated_data
        )
        user.is_student = True
        user.save()
        
        # Prepare data for student creation
        student_data = {
            'name': name,
            'email': email,
            'admission_number': username,
            'user': user
        }
        
        # Create student profile
        student = Student.objects.create(**student_data)
        
        return user


class EntryLogSerializer(serializers.ModelSerializer):
    student_name = serializers.ReadOnlyField(source='student.name')
    
    class Meta:
        model = EntryLog
        fields = ['id', 'student', 'student_name', 'timestamp', 'location', 'successful']
        read_only_fields = ['id', 'timestamp']


class LostCardScanSerializer(serializers.ModelSerializer):
    student_name = serializers.ReadOnlyField(source='student.name')
    
    class Meta:
        model = LostCardScan
        fields = ['id', 'student', 'student_name', 'timestamp', 'location']

