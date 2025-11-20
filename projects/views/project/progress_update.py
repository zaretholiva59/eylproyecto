from django.shortcuts import render, get_object_or_404
from projects.models import Projects
from django.http import JsonResponse
from datetime import date

def update_physical_progress(request, project_id):
    """Vista para actualizar % avance físico según PMI"""
    
    if request.method == 'POST':
        project = get_object_or_404(Projects, cod_projects_id=project_id)
        
        try:
            progress = float(request.POST.get('physical_progress', 0))
            
            # Validar rango
            if 0 <= progress <= 100:
                project.physical_percent_complete = progress
                project.last_progress_update = date.today()
                project.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Avance físico actualizado a {progress}%',
                    'pmi_compliant': True
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Porcentaje debe estar entre 0 y 100'
                }, status=400)
                
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'Porcentaje inválido'
            }, status=400)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)







