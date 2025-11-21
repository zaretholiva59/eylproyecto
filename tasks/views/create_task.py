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
            
            # Pre-procesar datos: convertir cod_projects_id a objeto Project si es necesario
            post_data = request.POST.copy()
            project_id = post_data.get('project')
            
            if project_id:
                try:
                    # Verificar si es un cod_projects_id (string) y obtener el objeto
                    project = Projects.objects.get(cod_projects=project_id)
                    post_data['project'] = project.pk  # Convertir a ID para el formulario
                    print(f"DEBUG: Proyecto encontrado: {project.cod_projects}")
                except Projects.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': f'Proyecto con código "{project_id}" no existe',
                        'error_details': {'project': ['Proyecto no encontrado']}
                    })
                except Exception as e:
                    print(f"DEBUG: Error al obtener proyecto: {e}")
            
            # ✨ NUEVO: Usar el Form Django en lugar de procesar manualmente
            form = TaskForm(post_data)
            
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
                
                print(f"DEBUG: Tarea creada con ID = {task.id}")
                
                return JsonResponse({
                    'success': True,
                    'task_id': task.id,
                    'message': '✅ Tarea creada exitosamente con validación Django'
                })
            else:
                # ✨ NUEVO: El form muestra errores automáticamente
                print(f"DEBUG: Errores del form = {form.errors}")
                # Formatear errores de forma más legible
                error_messages = []
                for field, errors in form.errors.items():
                    for error in errors:
                        error_messages.append(f"{field}: {error}")
                
                return JsonResponse({
                    'success': False,
                    'error': 'Errores de validación',
                    'errors': form.errors.get_json_data(),  # ← Errores en formato JSON para frontend
                    'error_messages': error_messages,  # ← Mensajes legibles
                    'error_details': dict(form.errors)  # ← Errores como diccionario
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