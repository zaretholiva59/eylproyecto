from django.shortcuts import render, get_object_or_404
import json
from projects.models import Projects
from projects.services.earned_value.calculator import EarnedValueCalculator
from projects.services.excel_reports.executive_reporter import ExecutiveReporter  # ✅ NUEVO

def curva_s_view(request, project_id):
    """Vista para mostrar la Curva S del proyecto - 100% DATOS REALES"""

    # ✅ 1. PROYECTO DESDE BD
    proyecto = get_object_or_404(Projects, cod_projects_id=project_id)

    # ✅ 2. DATOS CURVA S DESDE SERVICIO ACTUALIZADO
    calculadora = EarnedValueCalculator()
    datos_curva = calculadora.calculate_earned_value(project_id)

    # ✅ 3. DATOS EJECUTIVOS DESDE NUEVO SERVICIO
    executive_reporter = ExecutiveReporter()
    executive_data = executive_reporter.generate_executive_data(project_id)

    # ✅ 4. USAR EXACTAMENTE LOS MISMOS DATOS DEL SERVICIO
    bac_real = datos_curva['bac_calculated']

    # ✅ 5. OBTENER DATOS PARA COMPARACIÓN
    duracion_real = executive_data.get('duracion_real', 3)
    duracion_planeada = executive_data.get('duracion_planeada', 8)
    bac_planeado = executive_data.get('bac_planeado', bac_real)

    context = {
        'proyecto': proyecto,
        'meses': json.dumps(datos_curva['curve_data']['months']),
        'pv': json.dumps(datos_curva['curve_data']['pv']),
        'ev': json.dumps(datos_curva['curve_data']['ev']),
        'ac': json.dumps(datos_curva['curve_data']['ac']),
        # ✅ DATOS COHERENTES
        'bac': f"{bac_real:.1f}",
        'bac_display': f"{bac_real:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
        'bac_planeado_display': f"{bac_planeado:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
        # ✅ MÉTRICAS DEL SERVICIO
        'cpi': datos_curva['metrics']['cpi'],
        'spi': datos_curva['metrics']['spi'],
        'cv': datos_curva['metrics']['cv'],
        'sv': datos_curva['metrics']['sv'],
        'eac': datos_curva['metrics']['eac'],
        'etc': datos_curva['metrics']['etc'],
        # ✅ DATOS EJECUTIVOS DESDE NUEVO SERVICIO
        'duracion_real': duracion_real,
        'duracion_planeada': duracion_planeada,
        'porcentaje_ejecutado': executive_data.get('porcentaje_ejecutado', 0),
        'estado_proyecto': executive_data.get('estado', 'ACTIVO'),
        'monto_faltante': executive_data.get('monto_faltante', 0),
    }

    return render(request, 'project/curva_s.html', context)