from django.shortcuts import render, get_object_or_404 
import json 
from projects.models import Projects 
from projects.services.excel_reports.executive_reporter import ExecutiveReporter 
from projects.services.earned_value.calculator import EarnedValueCalculator
 
def excel_executive_view(request, project_id): 
    """Vista SOLO para Excel Ejecutivo""" 
    proyecto = get_object_or_404(Projects, cod_projects_id=project_id) 
 
    # SOLO EXCEL EJECUTIVO 
    executive_reporter = ExecutiveReporter() 
    executive_data = executive_reporter.generate_executive_data(project_id) 

    # Obtener BAC real desde Curva S para consistencia
    calculadora = EarnedValueCalculator()
    evm_data = calculadora.calculate_earned_value(project_id)
    bac_real = evm_data['bac_calculated']
    # BAC planeado desde presupuesto de costos
    bac_planeado = executive_data.get('bac_presupuestado', bac_real) 
    duracion_real = executive_data.get('duracion_real', 3) 
    duracion_planeada = executive_data.get('duracion_planeada', 8) 
 
    context = { 
        'proyecto': proyecto, 
        'executive_data': executive_data, 
        'bac_real': bac_real, 
        'bac_planeado': bac_planeado, 
        'bac_planeado_display': f"{bac_planeado:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), 
        'bac_real_display': f"{bac_real:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), 
        'duracion_real': duracion_real, 
        'duracion_planeada': duracion_planeada, 
        'porcentaje_ejecutado': executive_data.get('porcentaje_ejecutado', 0), 
        'estado_proyecto': executive_data.get('estado', 'ACTIVO'), 
        'monto_faltante': executive_data.get('monto_faltante', 0), 
        'desviacion_presupuestaria': executive_data.get('desviacion_presupuestaria', 0), 
    } 
    return render(request, 'dashboard/excel_executive.html', context)
