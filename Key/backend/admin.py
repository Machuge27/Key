from django.contrib import admin
from .models import Student, User  # Adjust the import path according to your project structure

# Register your models here.
admin.site.register(User)
admin.site.register(Student)
