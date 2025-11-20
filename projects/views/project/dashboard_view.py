from django.shortcuts import render, get_object_or_404
from django.core.cache import cache
import json
from projects.models import Projects, Hoursrecord
from projects.services.earned_value.calculator import EarnedValueCalculator
from projects.services.excel_reports.executive_reporter import ExecutiveReporter
from projects.services.excel_reports.cost_reporter import CostReporter
from projects.services.excel_reports.efficiency_reporter import EfficiencyReporter
from projects.services.earned_value.activity_calculator import ActivityCalculator

def pmi_dashboard(request, project_id): 
    """Dashboard PMI integrado con métricas financieras y físicas""" 
    project = get_object_or_404(Projects, cod_projects_id=project_id) 
    
    # Obtener datos PMI 
    evm_data = EarnedValueCalculator.calculate_earned_value(project_id) 
    physical_detail = EarnedValueCalculator.get_physical_progress_detail(project_id) 
    
    # Calcular métricas financieras básicas 
    financial_metrics = calculate_financial_metrics(project) 
    
    # Integrar datos para dashboard 
    dashboard_data = { 
        'project': project, 
        'pmi_metrics': { 
            'bac': evm_data['bac_calculated'], 
            'ac': evm_data['curve_data']['ac'][-1], 
            'ev': evm_data['curve_data']['ev'][-1], 
            'pv': evm_data['curve_data']['pv'][-1], 
            'cpi': evm_data['metrics']['cpi'], 
            'spi': evm_data['metrics']['spi'], 
            'eac': evm_data['metrics']['eac'], 
            'physical_progress': evm_data['physical_progress'], 
            'pmi_compliant': evm_data['pmi_compliant'] 
        }, 
        'financial_metrics': financial_metrics, 
        'physical_detail': physical_detail, 
        'performance_analysis': analyze_performance(evm_data, financial_metrics) 
    } 
    
    return render(request, 'projects/pmi_dashboard.html', dashboard_data) 

def calculate_financial_metrics(project): 
    """Calcular métricas financieras integradas""" 
    try: 
        # Datos de presupuesto (desde Chance asociado al proyecto)
        contract_amount = getattr(project.cod_projects, 'cost_aprox_chance', 0) 
        bac = getattr(project.cod_projects, 'total_costs', 0) 
        
        # Datos de facturación (simplificado - luego se extiende) 
        from projects.models import ClientInvoice 
        invoices = ClientInvoice.objects.filter(project=project) 
        total_invoiced = sum(invoice.amount for invoice in invoices) 
        
        # Datos de costos 
        from projects.models import PurchaseOrder 
        ocs = PurchaseOrder.objects.filter(project_code=project) 
        total_spent = sum(oc.total_amount for oc in ocs if oc.total_amount) 
        
        return { 
            'contract_amount': float(contract_amount), 
            'bac': float(bac), 
            'total_invoiced': float(total_invoiced), 
            'total_spent': float(total_spent), 
            'financial_progress': (total_invoiced / contract_amount * 100) if contract_amount > 0 else 0, 
            'estimated_margin': (contract_amount - bac) if contract_amount and bac else 0, 
            'current_margin': (total_invoiced - total_spent) if total_invoiced and total_spent else 0 
        } 
    except: 
        return {} 

def analyze_performance(evm_data, financial_metrics): 
    """Análisis integrado de desempeño PMI + Financiero""" 
    pmi_metrics = evm_data['metrics'] 
    physical_progress = evm_data['physical_progress'] 
    
    analysis = { 
        'cost_efficiency': '✅ Eficiente' if pmi_metrics['cpi'] >= 1.0 else '⚠️ Con sobrecostos', 
        'schedule_efficiency': '✅ En plazo' if pmi_metrics['spi'] >= 1.0 else '⚠️ Atrasado', 
        'physical_vs_financial': '', 
        'overall_health': '' 
    } 
    
    # Análisis físico vs financiero 
    financial_progress = financial_metrics.get('financial_progress', 0) 
    progress_gap = physical_progress - financial_progress 
    
    if abs(progress_gap) <= 10: 
        analysis['physical_vs_financial'] = '✅ Balanceado' 
    elif progress_gap > 10: 
        analysis['physical_vs_financial'] = '🔄 Avance físico > Facturación' 
    else: 
        analysis['physical_vs_financial'] = '💰 Facturación > Avance físico' 
    
    # Salud general del proyecto 
    if pmi_metrics['cpi'] >= 1.0 and pmi_metrics['spi'] >= 0.9: 
        analysis['overall_health'] = '✅ Saludable' 
    elif pmi_metrics['cpi'] >= 0.9 and pmi_metrics['spi'] >= 0.8: 
        analysis['overall_health'] = '⚠️ En observación' 
    else: 
        analysis['overall_health'] = '🚨 Crítico' 
    
    return analysis

def dashboard_view(request, project_id):
    """Vista principal del Dashboard Ejecutivo - OPTIMIZADA"""
    # ✅ OPTIMIZACIÓN: Cache para datos costosos
    cache_key = f'dashboard_data_{project_id}'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return render(request, 'dashboard/index.html', cached_data)
    
    # 1. ✅ OPTIMIZACIÓN: Una sola consulta con todas las relaciones
    proyecto = Projects.objects.select_related(
        'cod_projects',
        'cod_projects__info_costumer',
        'respon_projects'
    ).prefetch_related(
        'purchaseorder_set__podetailproduct_set__product',
        'purchaseorder_set__podetailsupplier_set__supplier',
        'client_invoices',  # ✅ CORREGIDO: Usar el related_name correcto
        'progress_records',  # ✅ CORREGIDO: Usar el related_name correcto
        'horas'
    ).get(cod_projects_id=project_id)
    
    # 2. ✅ OPTIMIZACIÓN: Consulta optimizada para dropdown
    todos_proyectos = Projects.objects.only(
        'cod_projects_id', 'cost_center', 'state_projects'
    ).all()
    
    # 3. DATOS CURVA S DESDE SERVICIO (mantener servicios especializados)
    calculadora = EarnedValueCalculator()
    datos_curva = calculadora.calculate_earned_value(project_id)
    
    # 4. DATOS EJECUTIVOS DESDE NUEVO SERVICIO
    executive_reporter = ExecutiveReporter()
    executive_data = executive_reporter.generate_executive_data(project_id)
    
    # 5. DATOS DE COSTOS
    cost_reporter = CostReporter()
    cost_data = cost_reporter.get_cost_distribution(project_id)
    
    # 6. DATOS DE EFICIENCIA
    efficiency_reporter = EfficiencyReporter()
    efficiency_data = efficiency_reporter.get_monthly_efficiency(project_id)
    
    bac_real = datos_curva['bac_calculated']
    
    # FORMATOS PARA TEMPLATE
    bac_js = f"{bac_real:.1f}"
    bac_display = f"{bac_real:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    # BAC planeado desde presupuesto de costos (Chance.total_costs)
    bac_planeado = executive_data.get('bac_presupuestado', bac_real)
    bac_planeado_display = f"{bac_planeado:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if bac_planeado else "0.00"

    # ✅ OPTIMIZACIÓN: Horas del proyecto usando datos ya cargados
    horas_records = [
        {
            'date': str(h.date),
            'hours': float(h.hours or 0),
            'respon': h.respon,
            'acti': h.acti,
        } for h in proyecto.horas.all()
    ]

    # ✅ OPTIMIZACIÓN: Preparar contexto
    context = {
        'proyecto': proyecto,
        'todos_proyectos': todos_proyectos,
        
        # Datos para graficos Curva S
        'meses': json.dumps(datos_curva['curve_data']['months']),
        'pv': json.dumps(datos_curva['curve_data']['pv']),
        'ev': json.dumps(datos_curva['curve_data']['ev']),
        'ac': json.dumps(datos_curva['curve_data']['ac']),
        'ac_paid': json.dumps(datos_curva['curve_data'].get('ac_paid', [])),
        'bac': bac_js,
        'bac_display': bac_display,
        
        # Granularidad (semanas y días)
        'semanas_labels': json.dumps(datos_curva.get('curve_data_weekly', {}).get('labels', [])),
        'semanas_pv': json.dumps(datos_curva.get('curve_data_weekly', {}).get('pv', [])),
        'semanas_ev': json.dumps(datos_curva.get('curve_data_weekly', {}).get('ev', [])),
        'semanas_ac': json.dumps(datos_curva.get('curve_data_weekly', {}).get('ac', [])),
        'dias_labels': json.dumps(datos_curva.get('curve_data_daily', {}).get('labels', [])),
        'dias_pv': json.dumps(datos_curva.get('curve_data_daily', {}).get('pv', [])),
        'dias_ev': json.dumps(datos_curva.get('curve_data_daily', {}).get('ev', [])),
        'dias_ac': json.dumps(datos_curva.get('curve_data_daily', {}).get('ac', [])),
        
        # Metricas EVM
        'cpi': datos_curva['metrics']['cpi'],
        'spi': datos_curva['metrics']['spi'],
        'cv': datos_curva['metrics']['cv'],
        'sv': datos_curva['metrics']['sv'],
        'eac': datos_curva['metrics']['eac'],
        'etc': datos_curva['metrics']['etc'],
        
        # Datos ejecutivos
        'duracion_real': executive_data.get('duracion_real', 1),
        'duracion_planeada': executive_data.get('duracion_planeada', 1),
        'porcentaje_ejecutado': executive_data.get('porcentaje_ejecutado', 0),
        'estado_proyecto': executive_data.get('estado', 'ACTIVO'),
        'monto_faltante': executive_data.get('monto_faltante', 0),
        'bac_planeado': bac_planeado,
        'bac_planeado_display': bac_planeado_display,
        'contract_amount': executive_data.get('contract_amount', 0),
        'facturado_cliente_total': executive_data.get('facturado_cliente_total', 0),
        'facturacion_mensual': json.dumps(executive_data.get('facturacion_mensual', [])),
        
        # Datos para graficos Excel Ejecutivo
        'cost_data': json.dumps(cost_data),
        'efficiency_meses': json.dumps(efficiency_data.get('meses', [])),
        'efficiency_data': json.dumps(efficiency_data.get('eficiencias', [])),
        
        # Hoja de horas
        'horas_data': json.dumps(horas_records),
    }
    
    # ✅ OPTIMIZACIÓN: Cache del resultado por 10 minutos
    cache.set(cache_key, context, 600)
    
    return render(request, 'dashboard/index.html', context)
