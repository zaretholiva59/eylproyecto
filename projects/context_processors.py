from projects.models.projects import Projects
from django.core.cache import cache

def projects_nav(request):
    """Context processor optimizado: provee lista de proyectos para navegación.
    Incluye `cod_projects_id`, `cost_center` y `state_projects`.
    """
    # ✅ OPTIMIZACIÓN: Cache para evitar consultas repetidas
    cache_key = 'projects_nav_optimized'
    projects = cache.get(cache_key)
    
    if not projects:
        try:
            # ✅ OPTIMIZACIÓN: Solo campos necesarios con relaciones optimizadas
            projects = Projects.objects.select_related(
                'cod_projects'
            ).only(
                'cod_projects_id',
                'cost_center', 
                'state_projects',
                'cod_projects__dres_chance'
            ).order_by('cod_projects_id')
            
            # Cache por 5 minutos
            cache.set(cache_key, list(projects), 300)
        except Exception:
            projects = []
    
    return {
        'projects_nav': projects
    }