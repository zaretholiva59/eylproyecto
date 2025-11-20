# CREAR: projects/services/dashboard_context_service.py
from projects.services.earned_value.calculator import EarnedValueCalculator
from projects.services.excel_reports.executive_reporter import ExecutiveReporter
from projects.models import Projects
from django.shortcuts import get_object_or_404
import json

class DashboardContextService:
    """Servicio modular para generar contexto del dashboard"""
    
    @staticmethod
    def get_dashboard_context(project_id):
        """Genera contexto completo para el dashboard"""
        
        # 1. DATOS BÁSICOS
        todos_proyectos = Projects.objects.all()
        proyecto = get_object_or_404(Projects, cod_projects_id=project_id)
        
        # 2. DATOS CURVA S
        calculadora = EarnedValueCalculator()
        datos_curva = calculadora.calculate_earned_value(project_id)
        
        # 3. DATOS EJECUTIVOS
        executive_reporter = ExecutiveReporter()
        executive_data = executive_reporter.generate_executive_data(project_id)
        
        # 4. FORMATEAR DATOS
        bac_real = datos_curva['bac_calculated']
        # BAC planeado proviene del presupuesto de costos (Presale.total_cost)
        bac_planeado = executive_data.get('bac_presupuestado', bac_real)
        
        context = {
            'proyecto': proyecto,
            'todos_proyectos': todos_proyectos,
            
            # Datos para gráficos Curva S
            'meses': json.dumps(datos_curva['curve_data']['months']),
            'pv': json.dumps(datos_curva['curve_data']['pv']),
            'ev': json.dumps(datos_curva['curve_data']['ev']),
            'ac': json.dumps(datos_curva['curve_data']['ac']),
            'bac': f"{bac_real:.1f}",
            'bac_display': DashboardContextService.format_currency(bac_real),
            
            # Métricas Curva S
            'cpi': datos_curva['metrics']['cpi'],
            'spi': datos_curva['metrics']['spi'],
            'cv': datos_curva['metrics']['cv'],
            'sv': datos_curva['metrics']['sv'],
            'eac': datos_curva['metrics']['eac'],
            'etc': datos_curva['metrics']['etc'],
            
            # Datos ejecutivos para Excel Charts
            'bac_planeado': bac_planeado,
            'bac_planeado_display': DashboardContextService.format_currency(bac_planeado) if bac_planeado else "0.00",
            'bac_real': bac_real,
            'duracion_real': executive_data.get('duracion_real', 1),
            'duracion_planeada': executive_data.get('duracion_planeada', 1),
            'porcentaje_ejecutado': executive_data.get('porcentaje_ejecutado', 0),
            'estado_proyecto': executive_data.get('estado', 'ACTIVO'),
            'desviacion_presupuestaria': executive_data.get('desviacion_presupuestaria', 0),
        }
        
        return context
    
    @staticmethod
    def format_currency(value):
        """Formatea valores monetarios"""
        if value:
            return f"{value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return "0.00"