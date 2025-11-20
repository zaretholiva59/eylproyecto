from django.urls import path, include
from django.shortcuts import redirect
from projects.models import Projects
from projects.views.project.curva_s_view import curva_s_view
from projects.views.project.curva_s_home import curva_s_home
from projects.views.project.dashboard_view import dashboard_view
from projects.views.project.activity_views import (
    project_activities,
    add_project_activity,
    update_activity_units,
    delete_activity,
    recalculate_weights,
    get_activity_progress_api as get_physical_progress_api,
    edit_activity,
)

def redirect_to_dashboard(request):
    """Redirige al dashboard del primer proyecto"""
    proyectos = Projects.objects.all()
    if proyectos.exists():
        primer_proyecto = proyectos.first()
        return redirect('project_dashboard', project_id=primer_proyecto.cod_projects_id)
    else:
        return curva_s_home(request)

def redirect_to_activities(request):
    """Redirige a la gestión de actividades del primer proyecto disponible"""
    proyectos = Projects.objects.all()
    if proyectos.exists():
        primer_proyecto = proyectos.first()
        return redirect('pmi_activity_management', project_id=primer_proyecto.cod_projects_id)
    # Si no hay proyectos, lleva a la pantalla informativa sin loop
    return curva_s_home(request)

urlpatterns = [
    path("presale/", include("projects.urls.presale")),
    path("logis/", include("projects.urls.logis")),
    path("grid/", include("projects.urls.grid")),
    path("customers/", include("projects.urls.costumer")),
    path('curva-s/', curva_s_home, name='curva_s_home'),
    path('curva-s/<str:project_id>/', curva_s_view, name='curva_s'),

    # ✅ AGREGAR: Ruta para /dashboard/ sin project_id
    path('dashboard/', redirect_to_dashboard, name='dashboard_home'),
    path('dashboard/<str:project_id>/', dashboard_view, name='project_dashboard'),

    # Acceso directo a actividades sin especificar proyecto
    path('activities/', redirect_to_activities, name='activities_home'),

    # ✅ NUEVO: Rutas para gestión de actividades PMI
    path('project/<str:project_id>/add-activity/', add_project_activity, name='add_project_activity'),
    path('activity/<int:activity_id>/update-units/', update_activity_units, name='update_activity_units'),
    path('activity/<int:activity_id>/edit/', edit_activity, name='edit_activity'),
    path('project/<str:project_id>/recalculate-weights/', recalculate_weights, name='recalculate_weights'),
    path('activity/<int:activity_id>/delete/', delete_activity, name='delete_activity'),
    path('api/project/<str:project_id>/physical-progress/', get_physical_progress_api, name='physical_progress_api'),

    # Incluir URLs PMI centralizadas
    path('', include('projects.urls.pmi')),
]