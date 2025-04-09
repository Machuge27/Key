from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path("task/tasks/", views.create_task, name="create_task"),
    path("task/manage_task/<int:task_id>/", views.manage_task, name="manage_task"),
    path("note/create_note/", views.create_note),
    path("note/manage_note/<int:note_id>/", views.manage_note),
]
