from projects.models import Projects, PurchaseOrder
from django.db.models import Sum

class CostReporter:
    """Servicio para reportar distribución de costos desde Chance/Projects"""
    
    @staticmethod
    def get_cost_distribution(project_id):
        """Obtiene distribución de costos desde el Chance asociado al Proyecto"""
        project = Projects.objects.get(cod_projects_id=project_id)
        
        # Intentar obtener datos desde Chance (relación OneToOne en Projects)
        try:
            chance = project.cod_projects
            if chance:
                return {
                    'materiales': float(chance.material_cost or 0),
                    'servicios': float(chance.labor_cost or 0),
                    'subcontratado': float(chance.subcontracted_cost or 0),
                    'gastos': float(chance.overhead_cost or 0),
                    'total': float(chance.total_costs or 0)
                }
        except Exception as e:
            print(f"No hay datos de Chance para {project_id}: {e}")
        
        # Fallback: calcular desde OCs (distribucion estimada)
        ocs = PurchaseOrder.objects.filter(project_code=project)
        total_ocs = sum([float(oc.total_amount or 0) for oc in ocs])
        
        # Distribucion estimada si no hay Presale
        return {
            'materiales': total_ocs * 0.40,
            'servicios': total_ocs * 0.30,
            'subcontratado': total_ocs * 0.20,
            'gastos': total_ocs * 0.10,
            'total': total_ocs
        }
