from projects.models import Projects
from projects.services.earned_value.calculator import EarnedValueCalculator

class BACReporter: 
    @staticmethod 
    def get_bac_comparison_data(project_id): 
        project = Projects.objects.get(cod_projects_id=project_id)

        # BAC Planeado (baseline) desde Chance.total_costs (fallback a cost_aprox_chance)
        try:
            chance = project.cod_projects
            bac_planeado = float(getattr(chance, 'total_costs', 0) or getattr(chance, 'cost_aprox_chance', 0) or 0)
        except Exception:
            bac_planeado = 0.0

        # BAC Real (vigente) desde calculadora EVM
        bac_real = float(EarnedValueCalculator.get_bac_real(project))

        return {
            'bac_planeado': bac_planeado,
            'bac_real': bac_real,
        }
