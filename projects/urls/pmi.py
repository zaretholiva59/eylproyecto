# projects/urls/pmi.py
from django.urls import path
from projects.views.project.dashboard_view import pmi_dashboard
from projects.views.project.activity_views import (
    pmi_activity_management,
    update_activity_progress_pmi,
    pmi_physical_progress_api,
)

urlpatterns = [
    # ✅ URLs PMI
    path('project/<str:project_id>/pmi-dashboard/', pmi_dashboard, name='pmi_dashboard'),
    path('project/<str:project_id>/pmi-activities/', pmi_activity_management, name='pmi_activity_management'),
    # Alias de compatibilidad para plantillas existentes
    path('project/<str:project_id>/activities/', pmi_activity_management, name='project_activities'),
    path('project/activity/<int:activity_id>/update-pmi-progress/', update_activity_progress_pmi, name='update_activity_progress_pmi'),
    path('api/project/<str:project_id>/physical-progress/', pmi_physical_progress_api, name='pmi_physical_progress_api'),
]
