from django.shortcuts import render, get_object_or_404 
import json 
from projects.models import Projects 
from projects.services.earned_value.calculator import EarnedValueCalculator 
 
def curva_s_view(request, project_id): 
    """Vista SOLO para Curva S EVM""" 
    proyecto = get_object_or_404(Projects, cod_projects_id=project_id) 
 
    # SOLO CURVA S 
    calculadora = EarnedValueCalculator() 
    datos_curva = calculadora.calculate_earned_value(project_id) 
    bac_real = datos_curva['bac_calculated'] 
 
    context = { 
        'proyecto': proyecto, 
        'meses': json.dumps(datos_curva['curve_data']['months']), 
        'pv': json.dumps(datos_curva['curve_data']['pv']), 
        'ev': json.dumps(datos_curva['curve_data']['ev']), 
        'ac': json.dumps(datos_curva['curve_data']['ac']), 
        'bac': f"{bac_real:.1f}", 
        'bac_display': f"{bac_real:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), 
        'cpi': datos_curva['metrics']['cpi'], 
        'spi': datos_curva['metrics']['spi'], 
        'cv': datos_curva['metrics']['cv'], 
        'sv': datos_curva['metrics']['sv'], 
        'eac': datos_curva['metrics']['eac'], 
        'etc': datos_curva['metrics']['etc'], 
    } 
    return render(request, 'project/curva_s.html', context) 
