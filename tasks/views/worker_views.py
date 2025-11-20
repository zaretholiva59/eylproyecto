# tasks/views/worker_views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from ..models import Task

@login_required
def worker_dashboard(request):
    # Obtener tareas asignadas al usuario actual
    assigned_tasks = Task.objects.filter(assigned_to=request.user)
    
    context = {
        'assigned_tasks': assigned_tasks,
        'assigned_count': assigned_tasks.count(),
        'completed_count': assigned_tasks.filter(status='done').count()
    }
    return render(request, 'tasks/worker/dashboard.html', context)