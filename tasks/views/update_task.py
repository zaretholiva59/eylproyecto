from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from ..models import Task
from projects.models import Projects
from django.contrib.auth.models import User
import json
from datetime import datetime

@require_http_methods(["POST"])
def update_task_view(request, task_id):
    """Actualizar una tarea existente"""
    try:
        task = Task.objects.get(id=task_id)
        
        # Obtener datos del POST
        task.title = request.POST.get('title', task.title)
        task.units_planned = float(request.POST.get('units_planned', task.units_planned))
        
        # Fechas
        planned_start = request.POST.get('planned_start')
        if planned_start:
            task.planned_start = datetime.strptime(planned_start, '%Y-%m-%dT%H:%M')
        
        planned_end = request.POST.get('planned_end')
        if planned_end:
            task.planned_end = datetime.strptime(planned_end, '%Y-%m-%dT%H:%M')
        
        # Asignar trabajador (si viene)
        assigned_to_id = request.POST.get('assigned_to')
        if assigned_to_id:
            task.assigned_to = User.objects.get(id=assigned_to_id)
        
        task.save()
        
        return JsonResponse({'success': True, 'message': 'Tarea actualizada'})
    
    except Task.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Tarea no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)