from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()

class Task(models.Model):
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    content = models.TextField()
    completed = models.BooleanField(default=False)
    deadline = models.DateTimeField()
    description = models.TextField()
    status = models.CharField(max_length=50, default="In Progress")
    title = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Task: {self.title[:30]}"


class Note(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Note: {self.content[:30]}"
