# projects/views/project/__init__.py
# Exportación completa de todas las vistas de project

# ✅ Importar TODAS las vistas existentes
from .dashboard_view import pmi_dashboard
from .activity_views import (
    pmi_activity_management,
    update_activity_progress_pmi,
    pmi_physical_progress_api
)

from .curva_s_view import curva_s_view
# # from .curva_s_home import curva_s_home
from .dashboard_view import dashboard_view
from .costos_view import grid_costos_variables
from .progress_update import update_physical_progress as progress_update
from .excel_executive_view import excel_executive_view

__all__ = [
    # Vistas existentes de Curva S
    'curva_s_view',
    'curva_s_home',
    
    # Vistas existentes de Dashboard y Costos
    'dashboard_view',
    'grid_costos_variables',
    'progress_update',
    'excel_executive_view',
    
    # ✅ Nuevas vistas PMI
    'pmi_dashboard',
    'pmi_activity_management',
    'update_activity_progress_pmi',
    'pmi_physical_progress_api',
]