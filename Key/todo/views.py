from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from .models import Task, Note
import json
from datetime import datetime

# Hardcoded credentials
HARD_CODED_USERNAME = 'Mutai'  
HARD_CODED_PASSWORD = 'mutai2127'  

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    data = json.loads(request.body)
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return JsonResponse({'error': 'Please provide both username and password'}, status=400)

    # Check against hardcoded credentials
    if username == HARD_CODED_USERNAME and password == HARD_CODED_PASSWORD:
        # If credentials are correct, return a success message along with the tasks
        tasks = list(Task.objects.all().values('id', 'title', 'description', 'completed', 'deadline', 'status'))
        notes = list(
            Note.objects.all().values(
                "id", "title", "content", "created_at", "updated_at"
            )
        )
        return JsonResponse(
            {
                "success": True,
                "tasks": tasks if tasks else [],
                "notes": notes if notes else [],
            }
        )
    else:
        return JsonResponse({'error': 'Invalid credentials'}, status=401)

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])  # In production, restrict this!
def logout(request):
    # Handle logout - in a real app you might invalidate a session or token
    return JsonResponse({'success': True}, status=200)

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])  # In production, restrict this!
def create_task(request):
    try:
        # Check if the user has hardcoded credentials
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        if username != HARD_CODED_USERNAME or password != HARD_CODED_PASSWORD:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)

        title = data.get('title')
        content = data.get('description')  # Assuming content is now description
        completed = data.get('completed', False)
        deadline = data.get('deadline')
        status = data.get('status', 'In Progress')

        if not title or not content or not deadline:
            return JsonResponse({'error': 'Title, description, and deadline are required'}, status=400)

        # Convert the deadline to a datetime object
        try:
            deadline = datetime.strptime(deadline, "%Y-%m-%dT%H:%M:%S.%f")
        except ValueError:
            return JsonResponse({'error': 'Invalid deadline format, should be YYYY-MM-DDTHH:MM:SS.sss'}, status=400)

        # Hardcoded user assignment (No authentication needed)
        # Assuming the user with the hardcoded credentials exists in the database
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(username=HARD_CODED_USERNAME)

        # Create the task
        task = Task.objects.create(
            user=user,
            title=title,
            content=content,
            completed=completed,
            deadline=deadline,
            description=content,  # Set content as description for backward compatibility
            status=status
        )

        return JsonResponse({
            'id': task.id,
            'title': task.title,
            'content': task.content,
            'completed': task.completed,
            'deadline': task.deadline,
            'description': task.description,
            'status': task.status,
        }, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

from dateutil import parser as date_parser  # Add this at the top

@csrf_exempt
@api_view(['PUT', 'DELETE'])
@permission_classes([AllowAny])
def manage_task(request, task_id):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        if username != HARD_CODED_USERNAME or password != HARD_CODED_PASSWORD:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)

        task = Task.objects.get(id=task_id)

        if request.method == 'DELETE':
            task.delete()
            return JsonResponse({}, status=204)

        elif request.method == 'PUT':
            title = data.get('title')
            content = data.get('description')
            completed = data.get('completed')
            deadline = data.get('deadline')
            status = data.get('status')

            # ✅ Convert deadline using dateutil (handles Z, timezone, etc.)
            if isinstance(deadline, str):
                try:
                    deadline = date_parser.isoparse(deadline)
                except Exception:
                    return JsonResponse(
                        {"error": "Invalid deadline format"}, status=400
                    )

            if title:
                task.title = title
            if content:
                task.description = content
            if completed is not None:
                task.completed = completed
            if deadline:
                task.deadline = deadline
            if status:
                task.status = status

            task.save()

            return JsonResponse({
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'completed': task.completed,
                'deadline': task.deadline,
                'status': task.status,
            })

    except Task.DoesNotExist:
        return JsonResponse({'error': 'Task not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def create_note(request):
    try:
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")

        if username != HARD_CODED_USERNAME or password != HARD_CODED_PASSWORD:
            return JsonResponse({"error": "Invalid credentials"}, status=401)

        title = data.get("title")
        content = data.get("content")

        if not title:
            return JsonResponse({"error": "Title is required"}, status=400)

        # Create the note
        note = Note.objects.create(
            title=title,
            content=content or "",
        )

        return JsonResponse(
            {
                "id": note.id,
                "title": note.title,
                "content": note.content,
                "created_at": note.created_at,
                "updated_at": note.updated_at,
            },
            status=201,
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@api_view(["PUT", "DELETE"])
@permission_classes([AllowAny])
def manage_note(request, note_id):
    try:
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")

        if username != HARD_CODED_USERNAME or password != HARD_CODED_PASSWORD:
            return JsonResponse({"error": "Invalid credentials"}, status=401)

        note = Note.objects.get(id=note_id)

        if request.method == "DELETE":
            note.delete()
            return JsonResponse({}, status=204)

        elif request.method == "PUT":
            title = data.get("title")
            content = data.get("content")

            if title:
                note.title = title
            if content is not None:
                note.content = content

            note.save()

            return JsonResponse(
                {
                    "id": note.id,
                    "title": note.title,
                    "content": note.content,
                    "created_at": note.created_at,
                    "updated_at": note.updated_at,
                }
            )

    except Note.DoesNotExist:
        return JsonResponse({"error": "Note not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
