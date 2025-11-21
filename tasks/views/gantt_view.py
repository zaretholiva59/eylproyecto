from multiprocessing import context
from urllib import request
from django.shortcuts import render
from django.db.models import Sum, Q, Count
from tasks.forms.task_forms import TaskForm
from ..models import Task
from projects.models import Projects

def gantt_view(request, project_id=None):
    """Vista del diagrama de Gantt para un proyecto"""
    
    # Obtener TODOS los proyectos para el dropdown del modal
    all_projects = Projects.objects.all()
    # Agregar nombre sin monto
    for proj in all_projects:
        cod_str = str(proj.cod_projects)
        nombre_sin_monto = cod_str.split('(')[0].strip() if '(' in cod_str else cod_str
        proj.display_name = f"{proj.cod_projects_id} - {nombre_sin_monto.split(' - ', 1)[-1]}"
    
    if project_id:
        project = Projects.objects.get(cod_projects_id=project_id)
        tasks = Task.objects.filter(project=project)
    else:
        project = None
        tasks = Task.objects.all()

    # ✨ NUEVO: Inicializar el Form Django
    task_form = TaskForm()
    
    # ✨ NUEVO: Calcular stats reales
    total_tasks = tasks.count()
    in_progress_tasks = tasks.filter(status='IN_PROGRESS').count()
    done_tasks = tasks.filter(status='DONE').count()
    
    # Calcular avance global (promedio ponderado)
    if total_tasks > 0:
        total_progress = 0
        for task in tasks:
            if task.units_planned > 0:
                task_progress = (float(task.units_completed) / float(task.units_planned)) * 100
                total_progress += task_progress
        global_progress = round(total_progress / total_tasks, 1)
    else:
        global_progress = 0
    
    # Preparar datos para el Gantt
    gantt_data = []
    for task in tasks:
        # ✨ NUEVO: Definir color según status
        color_map = {
            'BACKLOG': '#93C5FD',      # Azul claro
            'IN_PROGRESS': '#FCD34D',  # Amarillo
            'IN_REVIEW': '#C084FC',    # Morado
            'DONE': '#6EE7B7',         # Verde
        }
        task_color = color_map.get(task.status, '#E5E7EB')  # Gris por defecto
        
        task_dict = {
            'id': task.id,
            'text': f"{task.title} | 👤{task.assigned_to.username if task.assigned_to else 'Sin asignar'} | 📊{task.units_completed}/{task.units_planned}",
            'start_date': task.planned_start.strftime('%Y-%m-%d %H:%M') if task.planned_start else '',
            'end_date': task.planned_end.strftime('%Y-%m-%d %H:%M') if task.planned_end else '',
            'progress': float(task.units_completed) / float(task.units_planned) if task.units_planned > 0 else 0,
            'color': task_color,  # ✨ NUEVO: Color de la barra
        }
        
        # Agregar parent si existe (para jerarquías)
        if task.parent:
            task_dict['parent'] = task.parent.id
        
        gantt_data.append(task_dict)
    
    context = {
        'project': project,
        'projects': all_projects,
        'gantt_data': gantt_data,
        # ✨ NUEVO: Stats reales
        'total_tasks': total_tasks,
        'in_progress_tasks': in_progress_tasks,
        'done_tasks': done_tasks,
        'global_progress': global_progress,
        'form': task_form,  
    }
    return render(request, 'tasks/gantt/index.html', context)