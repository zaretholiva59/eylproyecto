# services/earned_value/metrics.py
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from projects.models import Projects, ProjectActivity
from .activity_calculator import ActivityCalculator

class ProjectMetrics:
    """
    Servicio para métricas avanzadas de proyectos
    Alineado con estándares PMI y mejores prácticas de la industria
    """
    
    @staticmethod
    def calculate_performance_indexes(project_id):
        """
        Calcula índices de desempeño avanzados según PMI
        """
        from .calculator import EarnedValueCalculator
        
        evm_data = EarnedValueCalculator.calculate_earned_value(project_id)
        metrics = evm_data['metrics']
        
        # Índices de desempeño avanzados
        performance_indexes = {
            # Índices básicos EVM
            'cpi': metrics['cpi'],
            'spi': metrics['spi'],
            
            # Índices avanzados
            'tcp_i': ProjectMetrics._calculate_tcp_i(metrics['cpi'], metrics['spi']),
            'cr': ProjectMetrics._calculate_cost_ratio(metrics['cpi']),
            'sr': ProjectMetrics._calculate_schedule_ratio(metrics['spi']),
            
            # Eficiencias
            'cost_efficiency': ProjectMetrics._get_efficiency_level(metrics['cpi']),
            'schedule_efficiency': ProjectMetrics._get_efficiency_level(metrics['spi']),
            
            # Tendencias
            'cost_trend': ProjectMetrics._analyze_cost_trend(metrics['cpi']),
            'schedule_trend': ProjectMetrics._analyze_schedule_trend(metrics['spi']),
        }
        
        return performance_indexes
    
    @staticmethod
    def _calculate_tcp_i(cpi, spi):
        """To Complete Performance Index - PMI Standard"""
        if cpi == 0:
            return Decimal('0.00')
        return Decimal(str(spi)) / Decimal(str(cpi))
    
    @staticmethod
    def _calculate_cost_ratio(cpi):
        """Cost Ratio - Eficiencia de costos en porcentaje"""
        return Decimal(str(cpi)) * Decimal('100.00')
    
    @staticmethod
    def _calculate_schedule_ratio(spi):
        """Schedule Ratio - Eficiencia de tiempo en porcentaje"""
        return Decimal(str(spi)) * Decimal('100.00')
    
    @staticmethod
    def _get_efficiency_level(value):
        """Nivel de eficiencia basado en valor"""
        value_dec = Decimal(str(value))
        if value_dec >= Decimal('1.10'):
            return '✅ Muy Eficiente'
        elif value_dec >= Decimal('1.00'):
            return '✅ Eficiente'
        elif value_dec >= Decimal('0.90'):
            return '⚠️ Aceptable'
        elif value_dec >= Decimal('0.80'):
            return '⚠️ En Riesgo'
        else:
            return '🚨 Crítico'
    
    @staticmethod
    def _analyze_cost_trend(cpi):
        """Análisis de tendencia de costos"""
        if cpi >= 1.0:
            return '📉 Mejorando'
        elif cpi >= 0.95:
            return '➡️ Estable'
        else:
            return '📉 Empeorando'
    
    @staticmethod
    def _analyze_schedule_trend(spi):
        """Análisis de tendencia de cronograma"""
        if spi >= 1.0:
            return '📈 Adelantado'
        elif spi >= 0.95:
            return '➡️ En Tiempo'
        else:
            return '📉 Atrasado'

    @staticmethod
    def calculate_risk_metrics(project_id):
        """
        Métricas de riesgo del proyecto según PMI
        """
        from .calculator import EarnedValueCalculator
        
        evm_data = EarnedValueCalculator.calculate_earned_value(project_id)
        metrics = evm_data['metrics']
        bac = evm_data['bac_calculated']
        
        risk_metrics = {
            # Variaciones
            'cv_percentage': (metrics['cv'] / bac * 100) if bac > 0 else Decimal('0.00'),
            'sv_percentage': (metrics['sv'] / bac * 100) if bac > 0 else Decimal('0.00'),
            
            # Estimaciones
            'eac': metrics['eac'],
            'etc': metrics['etc'],
            'vac': bac - metrics['eac'],  # Variance at Completion
            
            # Niveles de riesgo
            'cost_risk_level': ProjectMetrics._assess_cost_risk(metrics['cpi']),
            'schedule_risk_level': ProjectMetrics._assess_schedule_risk(metrics['spi']),
            'overall_risk_level': ProjectMetrics._assess_overall_risk(metrics['cpi'], metrics['spi']),
            
            # Alertas
            'cost_alerts': ProjectMetrics._generate_cost_alerts(metrics['cpi'], metrics['cv']),
            'schedule_alerts': ProjectMetrics._generate_schedule_alerts(metrics['spi'], metrics['sv']),
        }
        
        return risk_metrics
    
    @staticmethod
    def _assess_cost_risk(cpi):
        """Evaluar nivel de riesgo de costos"""
        if cpi >= 1.05:
            return '🟢 Riesgo Bajo'
        elif cpi >= 0.95:
            return '🟡 Riesgo Medio'
        elif cpi >= 0.85:
            return '🟠 Riesgo Alto'
        else:
            return '🔴 Riesgo Crítico'
    
    @staticmethod
    def _assess_schedule_risk(spi):
        """Evaluar nivel de riesgo de cronograma"""
        if spi >= 1.05:
            return '🟢 Riesgo Bajo'
        elif spi >= 0.95:
            return '🟡 Riesgo Medio'
        elif spi >= 0.85:
            return '🟠 Riesgo Alto'
        else:
            return '🔴 Riesgo Crítico'
    
    @staticmethod
    def _assess_overall_risk(cpi, spi):
        """Evaluar riesgo general del proyecto"""
        avg_risk = (cpi + spi) / 2
        if avg_risk >= 1.0:
            return '🟢 Bajo Riesgo'
        elif avg_risk >= 0.9:
            return '🟡 Riesgo Moderado'
        elif avg_risk >= 0.8:
            return '🟠 Alto Riesgo'
        else:
            return '🔴 Riesgo Extremo'
    
    @staticmethod
    def _generate_cost_alerts(cpi, cv):
        """Generar alertas de costos"""
        alerts = []
        if cpi < 0.9:
            alerts.append(f"🚨 SOBRECOSTO: CPI = {cpi:.3f} (CV = {cv:.2f})")
        elif cpi < 1.0:
            alerts.append(f"⚠️ Atención Costos: CPI = {cpi:.3f}")
        
        if cv < 0:
            alerts.append(f"📉 Variación Costo Negativa: {cv:.2f}")
        
        return alerts
    
    @staticmethod
    def _generate_schedule_alerts(spi, sv):
        """Generar alertas de cronograma"""
        alerts = []
        if spi < 0.9:
            alerts.append(f"🚨 ATRASO: SPI = {spi:.3f} (SV = {sv:.2f})")
        elif spi < 1.0:
            alerts.append(f"⚠️ Atención Cronograma: SPI = {spi:.3f}")
        
        if sv < 0:
            alerts.append(f"📉 Variación Tiempo Negativa: {sv:.2f}")
        
        return alerts

    @staticmethod
    def calculate_forecast_metrics(project_id):
        """
        Métricas de pronóstico y proyección
        """
        from .calculator import EarnedValueCalculator
        
        evm_data = EarnedValueCalculator.calculate_earned_value(project_id)
        metrics = evm_data['metrics']
        bac = evm_data['bac_calculated']
        physical_progress = evm_data['physical_progress']
        
        # Pronósticos basados en diferentes escenarios
        forecast_metrics = {
            # Escenario actual
            'current_eac': metrics['eac'],
            'current_etc': metrics['etc'],
            
            # Escenario optimista (mejora 10%)
            'optimistic_eac': bac / Decimal(str(max(metrics['cpi'] * 1.1, 0.1))),
            'optimistic_etc': (bac / Decimal(str(max(metrics['cpi'] * 1.1, 0.1)))) - metrics['eac'] + metrics['etc'],
            
            # Escenario pesimista (empeora 10%)
            'pessimistic_eac': bac / Decimal(str(max(metrics['cpi'] * 0.9, 0.1))),
            'pessimistic_etc': (bac / Decimal(str(max(metrics['cpi'] * 0.9, 0.1)))) - metrics['eac'] + metrics['etc'],
            
            # Tiempo estimado de finalización
            'estimated_completion_days': ProjectMetrics._estimate_completion_days(
                physical_progress, metrics['spi']
            ),
            
            # Probabilidad de éxito
            'success_probability': ProjectMetrics._calculate_success_probability(
                metrics['cpi'], metrics['spi']
            ),
        }
        
        return forecast_metrics
    
    @staticmethod
    def _estimate_completion_days(physical_progress, spi):
        """Estimar días hasta la finalización"""
        if physical_progress >= 100:
            return 0
        
        if spi <= 0:
            return 999  # Valor alto para indicar indeterminado
        
        progress_remaining = 100 - physical_progress
        estimated_days = (Decimal(str(progress_remaining)) / Decimal(str(physical_progress))) * (Decimal('30') / Decimal(str(spi)))  # 30 días por mes
        
        return max(1, int(estimated_days))
    
    @staticmethod
    def _calculate_success_probability(cpi, spi):
        """Calcular probabilidad de éxito del proyecto"""
        # Fórmula simplificada basada en CPI y SPI
        base_probability = (cpi * 0.6 + spi * 0.4) * 100
        
        # Ajustar por experiencia (valores > 1 son buenos)
        if cpi > 1.1 and spi > 1.1:
            adjustment = 10
        elif cpi > 1.0 and spi > 1.0:
            adjustment = 5
        elif cpi < 0.9 or spi < 0.9:
            adjustment = -15
        else:
            adjustment = 0
        
        final_probability = max(0, min(100, base_probability + adjustment))
        return Decimal(str(final_probability)).quantize(Decimal('0.1'))

    @staticmethod
    def calculate_quality_metrics(project_id):
        """
        Métricas de calidad del avance físico
        """
        physical_detail = ActivityCalculator.get_physical_progress_detail(project_id)
        activities = physical_detail['activities']
        
        if not activities:
            return {
                'data_quality': 'No Data',
                'measurement_consistency': 0,
                'progress_reliability': 'Low',
                'quality_score': 0
            }
        
        # Calcular consistencia en mediciones
        progress_values = [act['percentage_completed'] for act in activities]
        weight_values = [act['weight'] for act in activities]
        
        quality_metrics = {
            'data_quality': ProjectMetrics._assess_data_quality(activities),
            'measurement_consistency': ProjectMetrics._calculate_consistency(progress_values),
            'progress_reliability': ProjectMetrics._assess_reliability(weight_values),
            'quality_score': ProjectMetrics._calculate_quality_score(activities),
            'activities_with_data': len([act for act in activities if act['completed_units'] > 0]),
            'total_activities': len(activities),
            'weights_valid': physical_detail['weights_valid'],
        }
        
        return quality_metrics
    
    @staticmethod
    def _assess_data_quality(activities):
        """Evaluar calidad de los datos de avance"""
        activities_with_data = len([act for act in activities if act['completed_units'] > 0])
        total_activities = len(activities)
        
        if total_activities == 0:
            return 'No Data'
        
        data_ratio = activities_with_data / total_activities
        
        if data_ratio >= 0.9:
            return '✅ Excelente'
        elif data_ratio >= 0.7:
            return '✅ Buena'
        elif data_ratio >= 0.5:
            return '⚠️ Regular'
        else:
            return '🚨 Mala'
    
    @staticmethod
    def _calculate_consistency(progress_values):
        """Calcular consistencia en las mediciones de progreso"""
        if not progress_values:
            return 0
        
        from statistics import stdev
        try:
            # Menor desviación estándar = mayor consistencia
            deviation = stdev(progress_values)
            consistency = max(0, 100 - (deviation * 10))  # Convertir a porcentaje
            return round(consistency, 1)
        except:
            return 100  # Si solo hay un valor, consistencia perfecta
    
    @staticmethod
    def _assess_reliability(weight_values):
        """Evaluar confiabilidad de los pesos"""
        if not weight_values:
            return 'Low'
        
        # Verificar si los pesos están bien distribuidos
        max_weight = max(weight_values)
        min_weight = min(weight_values)
        
        if max_weight - min_weight > 50:  # Diferencia muy grande
            return '⚠️ Variable'
        elif max_weight - min_weight > 25:
            return '✅ Aceptable'
        else:
            return '✅ Buena'
    
    @staticmethod
    def _calculate_quality_score(activities):
        """Calcular puntaje general de calidad"""
        if not activities:
            return 0
        
        scores = []
        for activity in activities:
            # Puntaje basado en completitud de datos
            score = 0
            if activity['completed_units'] > 0:
                score += 30
            if activity['total_units'] > 0:
                score += 20
            if activity['weight'] > 0:
                score += 20
            if activity['percentage_completed'] <= 100:
                score += 30
            
            scores.append(score)
        
        return round(sum(scores) / len(scores), 1)

    @staticmethod
    def get_comprehensive_metrics(project_id):
        """
        Métricas comprehensivas para dashboard ejecutivo
        """
        performance = ProjectMetrics.calculate_performance_indexes(project_id)
        risk = ProjectMetrics.calculate_risk_metrics(project_id)
        forecast = ProjectMetrics.calculate_forecast_metrics(project_id)
        quality = ProjectMetrics.calculate_quality_metrics(project_id)
        
        return {
            'performance': performance,
            'risk': risk,
            'forecast': forecast,
            'quality': quality,
            'timestamp': timezone.now(),
            'project_id': project_id
        }