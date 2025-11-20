# tasks/views/create_task.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import datetime
from tasks.forms.task_forms import TaskForm
from tasks.models import Task
from projects.models import Projects

@csrf_exempt
def create_task_view(request):  
    if request.method == 'POST':
        try:
            print(f"DEBUG: Datos recibidos = {dict(request.POST)}")
            
            # ✨ NUEVO: Usar el Form Django en lugar de procesar manualmente
            form = TaskForm(request.POST)
            
            if form.is_valid():
                # ✨ EL FORM YA VALIDÓ Y LIMPIÓ LOS DATOS AUTOMÁTICAMENTE
                task = form.save(commit=False)
                
                # ✨ AGREGAR CAMPOS ADICIONALES (que no están en el form)
                task.units_completed = 0
                task.status = 'BACKLOG'
                
                # Si no hay usuario asignado, mantener null
                if not task.assigned_to:
                    task.assigned_to = None
                
                # ✨ GUARDAR LA TAREA
                task.save()
                
                print(f"DEBUG: Tarea creada con ID = {task.id}, Parent = {task.parent}")
                
                return JsonResponse({
                    'success': True,
                    'task_id': task.id,
                    'message': '✅ Tarea creada exitosamente con validación Django'
                })
            else:
                # ✨ NUEVO: El form muestra errores automáticamente
                print(f"DEBUG: Errores del form = {form.errors}")
                return JsonResponse({
                    'success': False,
                    'error': 'Errores de validación',
                    'errors': form.errors.get_json_data()  # ← Errores en formato JSON
                })
            
        except Exception as e:
            import traceback
            print(f"ERROR: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})