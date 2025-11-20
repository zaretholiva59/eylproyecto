from django.urls import path
from tasks.views.gantt_view import gantt_view

urlpatterns = [
    path('gantt/', gantt_view, name='gantt'),
    path('gantt/<str:project_id>/', gantt_view, name='gantt_project'),
]