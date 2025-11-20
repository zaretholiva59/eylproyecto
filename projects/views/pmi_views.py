from django.shortcuts import render, get_object_or_404 
from projects.models import Projects 
from projects.services.earned_value.calculator import EarnedValueCalculator 
from projects.services.earned_value.activity_calculator import ActivityCalculator 
from decimal import Decimal 
 

def pmi_dashboard(request, project_id): 
    """Dashboard PMI integrado con métricas financieras y físicas""" 
    project = get_object_or_404(Projects, cod_projects_id=project_id) 
    
    # Obtener datos PMI 
    evm_data = EarnedValueCalculator.calculate_earned_value(project_id) 
    physical_detail = EarnedValueCalculator.get_physical_progress_detail(project_id) 
    
    # Integrar datos para dashboard 
    context = { 
        'project': project, 
        'pmi_metrics': { 
            'bac': evm_data['bac_calculated'], 
            'ac': evm_data['curve_data']['ac'][-1] if evm_data['curve_data']['ac'] else 0, 
            'ev': evm_data['curve_data']['ev'][-1] if evm_data['curve_data']['ev'] else 0, 
            'pv': evm_data['curve_data']['pv'][-1] if evm_data['curve_data']['pv'] else 0, 
            'cpi': evm_data['metrics']['cpi'], 
            'spi': evm_data['metrics']['spi'], 
            'eac': evm_data['metrics']['eac'], 
            'physical_progress': evm_data['physical_progress'], 
            'pmi_compliant': evm_data['pmi_compliant'] 
        }, 
        'physical_detail': physical_detail
    } 
    
    return render(request, 'projects/pmi_dashboard.html', context)

def project_activities(request, project_id):
    """Vista para gestionar actividades del proyecto"""
    project = get_object_or_404(Projects, cod_projects_id=project_id)
    
    # Calcular avance físico y EV
    physical_progress = ActivityCalculator.calculate_physical_progress(project)
    bac = EarnedValueCalculator.get_bac_real(project)
    ev_calculated = float(bac * (physical_progress / Decimal('100.00')))
    
    context = {
        'project': project,
        'activities': ActivityCalculator.get_project_activities(project),
        'physical_progress': float(physical_progress),
        'ev_calculated': ev_calculated,
        'pmi_detail': EarnedValueCalculator.get_physical_progress_detail(project_id)
    }
    
    return render(request, 'projects/activity_list.html', context)