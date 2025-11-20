from django.shortcuts import redirect, render
from projects.models import Projects

def curva_s_home(request):
    """Redirige a la Curva S del primer proyecto disponible.
    Se elimina el template de selección y conceptos.
    """
    proyectos = Projects.objects.all()
    if proyectos.exists():
        primer = proyectos.first()
        return redirect('curva_s', project_id=primer.cod_projects_id)
    # Si no hay proyectos, mostrar una página informativa sin redirigir para evitar loops
    return render(request, 'project/curva_s_home.html', {})