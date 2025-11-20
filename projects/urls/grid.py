from django.urls import path
from django.shortcuts import render
from projects.models import Projects
from projects.views.project.curva_s_view import curva_s_view
from projects.views.project.dashboard_view import dashboard_view
from projects.views.project.costos_view import grid_costos_variables, exportar_excel_grid

def grid_principal(request):
    """Página principal del Grid - Redirige al primer proyecto"""
    proyectos = Projects.objects.all()
    if proyectos.exists():
        primer_proyecto = proyectos.first()
        return grid_costos_variables(request, primer_proyecto.cod_projects_id)
    else:
        return render(request, 'project/index.html', {'proyectos': proyectos})

urlpatterns = [
    path('', grid_principal, name='grid'),
    path('grid-costos/<str:proyecto_id>/', grid_costos_variables, name='grid_costos'),
    path('excel-grid/', exportar_excel_grid, name='excel_grid'),
    
    # ✅ RUTA DASHBOARD (corregida)
    path('dashboard/<str:project_id>/', dashboard_view, name='project_dashboard'),
    
    # ✅ MANTENER CURVA S
    path('curva-s/<str:project_id>/', curva_s_view, name='curva_s'),
]