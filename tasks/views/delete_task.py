from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from ..models import Task

@require_http_methods(["POST"])
def delete_task_view(request, task_id):
    """Eliminar una tarea"""
    try:
        task = Task.objects.get(id=task_id)
        task.delete()
        return JsonResponse({'success': True, 'message': 'Tarea eliminada'})
    except Task.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Tarea no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)