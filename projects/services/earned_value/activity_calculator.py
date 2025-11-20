# services/earned_value/activity_calculator.py
from decimal import Decimal
from projects.models import Projects, ProjectActivity

class ActivityCalculator:
    """
    Servicio especializado para cálculos de avance físico
    Alineado con estándares PMI
    """
    
    @staticmethod
    def calculate_activity_weights(project):
        """
        Calcula pesos automáticos basado en complejidad, esfuerzo e impacto
        Fórmula: Peso = (Comp + Esf + Imp) / Total_puntos * 100
        """
        activities = ProjectActivity.objects.filter(project=project, is_active=True)
        
        if not activities.exists():
            return False
            
        # Calcular total de puntos
        total_points = sum(
            act.complexity + act.effort + act.impact 
            for act in activities
        )
        
        if total_points == 0:
            return False
            
        # Actualizar pesos
        for activity in activities:
            activity_points = activity.complexity + activity.effort + activity.impact
            new_weight = (activity_points / total_points) * 100
            activity.calculated_weight = Decimal(str(new_weight)).quantize(Decimal('0.01'))
            activity.save()
            
        return True
    
    @staticmethod
    def calculate_physical_progress(project):
        """
        Calcula avance físico total del proyecto según PMI
        Fórmula: Σ(Peso_actividad × %_completado_actividad) / 100
        """
        activities = ProjectActivity.objects.filter(project=project, is_active=True)
        
        if not activities.exists():
            # Fallback: usar registros de ProjectProgress o campo del proyecto
            from django.db.models import Max
            from projects.models import ProjectProgress
            try:
                max_pct = ProjectProgress.objects.filter(project=project).aggregate(max_pct=Max('actual_percentage'))['max_pct']
            except Exception:
                max_pct = None
            if max_pct is not None:
                return Decimal(str(max_pct)).quantize(Decimal('0.01'))
            return Decimal(str(project.physical_percent_complete or 0)).quantize(Decimal('0.01'))
            
        total_progress = sum(
            (activity.calculated_weight * activity.percentage_completed) / Decimal('100.00')
            for activity in activities
        )
        
        return total_progress.quantize(Decimal('0.01'))
    
    @staticmethod
    def validate_weights_sum(project):
        """
        Valida que la suma de pesos sea 100% (PMI compliance)
        """
        activities = ProjectActivity.objects.filter(project=project, is_active=True)
        total_weight = sum(act.calculated_weight for act in activities)
        
        # Permitir pequeña tolerancia por redondeo
        return abs(total_weight - Decimal('100.00')) <= Decimal('0.05')
    
    @staticmethod
    def get_physical_progress_detail(project_id):
        """
        ✅ MOVIDO DESDE CALCULATOR.PY - Detalle completo del avance físico
        """
        project = Projects.objects.get(cod_projects_id=project_id)
        activities = ProjectActivity.objects.filter(project=project, is_active=True)
        
        activity_details = []
        for activity in activities:
            contribution = (activity.calculated_weight * activity.percentage_completed) / Decimal('100.00')
            
            activity_details.append({
                'id': activity.id,
                'name': activity.name,
                'description': activity.description,
                'unit_of_measure': activity.unit_of_measure,
                'complexity': activity.complexity,
                'effort': activity.effort,
                'impact': activity.impact,
                'weight': float(activity.calculated_weight),
                'completed_units': activity.completed_units,
                'total_units': activity.total_units,
                'percentage_completed': float(activity.percentage_completed),
                'contribution': float(contribution)
            })
        
        total_progress = ActivityCalculator.calculate_physical_progress(project)
        weights_valid = ActivityCalculator.validate_weights_sum(project)
        # Calcular peso total para visualización
        total_weight = sum(act.calculated_weight for act in activities) if activities else Decimal('0.00')
        total_weight = total_weight.quantize(Decimal('0.01'))
        
        data_source = 'activities' if activities.exists() else 'project_progress'
        
        return {
            'activities': activity_details,
            'total_physical_progress': float(total_progress),
            'total_weight': float(total_weight),
            'weights_valid': weights_valid,
            'activities_count': len(activity_details),
            'project_id': project_id,
            'source': data_source
        }