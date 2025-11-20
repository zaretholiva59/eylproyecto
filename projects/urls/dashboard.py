from django.urls import path
from projects.views.dashboard_views import pmi_dashboard

urlpatterns = [
    path('pmi/<str:project_id>/', pmi_dashboard, name='pmi_dashboard'),
    path('project/<str:project_id>/pmi-dashboard/', pmi_dashboard, name='project_pmi_dashboard'),
]