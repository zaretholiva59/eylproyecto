from django.urls import path
from tasks.views.update_task import update_task_view
from tasks.views.delete_task import delete_task_view

urlpatterns = [
    path('tasks/editar/<int:task_id>/', update_task_view, name='update_task') ,
    path('tasks/eliminar/<int:task_id>/', delete_task_view, name='delete_task'),
]