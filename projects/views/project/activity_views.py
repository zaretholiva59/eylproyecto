from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.views import View
from projects.models import Projects, ProjectActivity
from projects.services.earned_value.activity_calculator import ActivityCalculator
from projects.services.earned_value.calculator import EarnedValueCalculator
from decimal import Decimal

def project_activities(request, project_id):
    """Vista principal de gestión de actividades PMI"""
    project = get_object_or_404(Projects, cod_projects_id=project_id)
    activities = ProjectActivity.objects.filter(project=project, is_active=True).order_by('-calculated_weight', 'name')
    
    # Calcular avance físico y EV
    physical_progress = ActivityCalculator.calculate_physical_progress(project)
    bac = EarnedValueCalculator.get_bac_real(project)
    ev_calculated = float(bac * (physical_progress / Decimal('100.00')))
    
    context = {
        'project': project,
        'activities': activities,
        'physical_progress': float(physical_progress),
        'ev_calculated': ev_calculated,
        'pmi_detail': EarnedValueCalculator.get_physical_progress_detail(project_id)
    }
    
    return render(request, 'task/activity_list.html', context)

@require_http_methods(["POST"])
def add_project_activity(request, project_id):
    """Vista para agregar nueva actividad al proyecto"""
    project = get_object_or_404(Projects, cod_projects_id=project_id)
    
    try:
        # Obtener datos del formulario
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        total_units = int(request.POST.get('total_units', 0))
        unit_of_measure = request.POST.get('unit_of_measure', '').strip()
        complexity = int(request.POST.get('complexity', 3))
        effort = int(request.POST.get('effort', 3))
        impact = int(request.POST.get('impact', 3))
        
        # Validaciones
        if not name or not unit_of_measure or total_units <= 0:
            messages.error(request, 'Todos los campos son obligatorios y las unidades deben ser mayor a 0')
            return redirect('pmi_activity_management', project_id=project_id)
        
        if not (1 <= complexity <= 5 and 1 <= effort <= 5 and 1 <= impact <= 5):
            messages.error(request, 'Los criterios deben estar entre 1 y 5')
            return redirect('pmi_activity_management', project_id=project_id)
        
        # Crear actividad
        activity = ProjectActivity.objects.create(
            project=project,
            name=name,
            description=description,
            total_units=total_units,
            unit_of_measure=unit_of_measure,
            complexity=complexity,
            effort=effort,
            impact=impact,
            completed_units=0,
            created_by=request.user if request.user.is_authenticated else None
        )
        
        # Recalcular pesos automáticamente
        ActivityCalculator.calculate_activity_weights(project)
        
        messages.success(request, f'Actividad "{name}" agregada exitosamente')
        
    except (ValueError, TypeError) as e:
        messages.error(request, 'Error en los datos proporcionados')
    except Exception as e:
        messages.error(request, f'Error al crear la actividad: {str(e)}')
    
    return redirect('pmi_activity_management', project_id=project_id)

@require_http_methods(["POST"])
def update_activity_units(request, activity_id):
    """Vista para actualizar unidades completadas de una actividad"""
    activity = get_object_or_404(ProjectActivity, id=activity_id)
    
    try:
        completed_units = int(request.POST.get('completed_units', 0))
        
        # Validar que no exceda el total
        if completed_units < 0:
            completed_units = 0
        elif completed_units > activity.total_units:
            completed_units = activity.total_units
        
        activity.completed_units = completed_units
        activity.save()  # El save() automáticamente recalcula el porcentaje
        
        messages.success(request, f'Unidades actualizadas para "{activity.name}"')
        
    except (ValueError, TypeError):
        messages.error(request, 'Error en el número de unidades')
    except Exception as e:
        messages.error(request, f'Error al actualizar: {str(e)}')
    
    return redirect('pmi_activity_management', project_id=activity.project.cod_projects_id)

@require_http_methods(["POST"])
def delete_activity(request, activity_id):
    """Vista para eliminar una actividad"""
    activity = get_object_or_404(ProjectActivity, id=activity_id)
    project_id = activity.project.cod_projects_id
    
    try:
        activity_name = activity.name
        activity.delete()
        
        # Recalcular pesos después de eliminar
        ActivityCalculator.calculate_activity_weights(activity.project)
        
        messages.success(request, f'Actividad "{activity_name}" eliminada exitosamente')
        
    except Exception as e:
        messages.error(request, f'Error al eliminar la actividad: {str(e)}')
    
    return redirect('activity_list', project_id=project_id)

@require_http_methods(["POST"])
def recalculate_weights(request, project_id):
    """Vista para recalcular pesos de todas las actividades"""
    project = get_object_or_404(Projects, cod_projects_id=project_id)
    
    try:
        success = ActivityCalculator.calculate_activity_weights(project)
        
        if success:
            messages.success(request, 'Pesos recalculados exitosamente')
        else:
            messages.warning(request, 'No hay actividades activas para recalcular')
            
    except Exception as e:
        messages.error(request, f'Error al recalcular pesos: {str(e)}')
    
    return redirect('activity_list', project_id=project_id)

@require_http_methods(["GET"])
def get_activity_progress_api(request, project_id):
    """API para obtener progreso de actividades (JSON)"""
    project = get_object_or_404(Projects, cod_projects_id=project_id)
    
    try:
        progress_detail = EarnedValueCalculator.get_physical_progress_detail(project_id)
        
        return JsonResponse({
            'success': True,
            'data': progress_detail
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["POST"])
def edit_activity(request, activity_id):
    """Editar detalles de una actividad (nombre, descripción, unidades y criterios)."""
    activity = get_object_or_404(ProjectActivity, id=activity_id)
    project_id = activity.project.cod_projects_id

    try:
        name = request.POST.get('name', activity.name).strip()
        description = request.POST.get('description', activity.description).strip()
        total_units = int(request.POST.get('total_units', activity.total_units))
        unit_of_measure = request.POST.get('unit_of_measure', activity.unit_of_measure).strip()
        complexity = int(request.POST.get('complexity', activity.complexity))
        effort = int(request.POST.get('effort', activity.effort))
        impact = int(request.POST.get('impact', activity.impact))

        # Validaciones básicas
        if not name or not unit_of_measure or total_units <= 0:
            messages.error(request, 'Todos los campos son obligatorios y las unidades deben ser mayor a 0')
            return redirect('pmi_activity_management', project_id=project_id)

        if not (1 <= complexity <= 5 and 1 <= effort <= 5 and 1 <= impact <= 5):
            messages.error(request, 'Los criterios deben estar entre 1 y 5')
            return redirect('pmi_activity_management', project_id=project_id)

        # Asegurar que las unidades completadas no excedan el nuevo total
        if activity.completed_units > total_units:
            activity.completed_units = total_units

        # Actualizar campos
        activity.name = name
        activity.description = description
        activity.total_units = total_units
        activity.unit_of_measure = unit_of_measure
        activity.complexity = complexity
        activity.effort = effort
        activity.impact = impact
        activity.save()

        # Recalcular pesos automáticamente
        ActivityCalculator.calculate_activity_weights(activity.project)

        messages.success(request, f'Actividad "{activity.name}" actualizada correctamente')

    except (ValueError, TypeError):
        messages.error(request, 'Error en los datos proporcionados')
    except Exception as e:
        messages.error(request, f'Error al actualizar la actividad: {str(e)}')

    return redirect('pmi_activity_management', project_id=project_id)

def pmi_physical_progress_api(request, project_id):
    """API para obtener avance físico PMI"""
    from projects.services.earned_value.activity_calculator import ActivityCalculator

    try:
        physical_detail = ActivityCalculator.get_physical_progress_detail(project_id)

        return JsonResponse({
            'success': True,
            'physical_progress': physical_detail['total_physical_progress'],
            'activities_count': len(physical_detail['activities']),
            'weights_valid': physical_detail['weights_valid'],
            'activities': physical_detail['activities']
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# =============================================================================
# VISTAS PMI - EARNED VALUE MANAGEMENT
# =============================================================================

def pmi_dashboard(request, project_id):
    """Dashboard PMI integrado con Earned Value Management"""
    from projects.services.earned_value.calculator import EarnedValueCalculator
    from projects.services.earned_value.activity_calculator import ActivityCalculator

    project = get_object_or_404(Projects, cod_projects_id=project_id)

    # Obtener datos PMI
    evm_data = EarnedValueCalculator.calculate_earned_value(project_id)
    physical_detail = ActivityCalculator.get_physical_progress_detail(project_id)

    context = {
        'project': project,
        'evm_data': evm_data,
        'physical_detail': physical_detail,
        'pmi_metrics': evm_data['metrics'],
        'physical_progress': evm_data['physical_progress'],
        'bac_calculated': evm_data['bac_calculated'],
    }

    return render(request, 'projects/pmi_dashboard.html', context)


def pmi_activity_management(request, project_id):
    """Gestión de actividades PMI - Vista especializada"""
    from projects.services.earned_value.activity_calculator import ActivityCalculator

    project = get_object_or_404(Projects, cod_projects_id=project_id)
    activities_detail = ActivityCalculator.get_physical_progress_detail(project_id)
    activities = ProjectActivity.objects.filter(project=project, is_active=True)

    # Configuración de ponderaciones de criterios (puede ajustarse a tu política)
    weights_config = {
        'complexity': 0.4,
        'effort': 0.3,
        'impact': 0.3,
    }

    # Cálculo de pesos esperados según criterios (vista previa)
    preview_rows = []
    total_score = 0.0
    for a in activities:
        score = (
            (a.complexity or 0) * weights_config['complexity'] +
            (a.effort or 0) * weights_config['effort'] +
            (a.impact or 0) * weights_config['impact']
        )
        preview_rows.append({
            'activity': a,
            'score': float(score),
        })
        total_score += float(score)

    for row in preview_rows:
        row['expected_weight'] = round((row['score'] / total_score) * 100.0, 2) if total_score > 0 else 0.0

    context = {
        'project': project,
        'activities_detail': activities_detail,
        'activities': activities,
        'weights_config': weights_config,
        'activities_weight_preview': preview_rows,
    }

    return render(request, 'projects/pmi/activities.html', context)


def update_activity_progress_pmi(request, activity_id):
    """Actualizar progreso de actividad - Versión PMI"""
    if request.method == 'POST':
        activity = get_object_or_404(ProjectActivity, id=activity_id)
        completed_units = request.POST.get('completed_units')

        try:
            activity.completed_units = int(completed_units)
            activity.save()

            # Recalcular pesos automáticamente
            from projects.services.earned_value.activity_calculator import ActivityCalculator
            ActivityCalculator.calculate_activity_weights(activity.project)

            messages.success(request, f'✅ Progreso de {activity.name} actualizado: {activity.completed_units}/{activity.total_units}')

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # Respuesta AJAX para actualización en tiempo real
                return JsonResponse({
                    'success': True,
                    'percentage_completed': float(activity.percentage_completed),
                    'contribution': float((activity.calculated_weight * activity.percentage_completed) / 100)
                })

        except Exception as e:
            messages.error(request, f'❌ Error al actualizar: {str(e)}')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)})

    return redirect('pmi_activity_management', project_id=activity.project.cod_projects_id)

