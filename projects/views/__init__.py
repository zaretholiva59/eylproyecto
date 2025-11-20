# projects/views/__init__.py 
 
# --- Log°stica --- 
from .logis import ( 
    purchase_order_index, 
    purchase_order_create, 
    purchase_order_edit, 
    purchase_order_delete, 
    autocomplete_supplier, 
    autocomplete_product, 
) 
 
# --- Preventa --- 
from .presale import ( 
    pre_sale, 
    crear_presale, 
    presale_edit, 
    presale_delete, 
) 
 
# --- Proyectos (PMI) --- ? NUEVA SECCI‡N 
from .project import ( 
    # Vistas existentes de project 
    curva_s_view, 
    dashboard_view, 
    costos_view, 
    progress_update, 
 
    # ? Nuevas vistas PMI 
    pmi_dashboard, 
    pmi_activity_management, 
    update_activity_progress_pmi, 
    pmi_physical_progress_api, 
) 
 
__all__ = [ 
    # Log°stica 
    "purchase_order_index", 
    "purchase_order_create", 
    "purchase_order_edit", 
    "purchase_order_delete", 
    "autocomplete_supplier", 
    "autocomplete_product", 
 
    # Preventa 
    "pre_sale", 
    "crear_presale", 
    "presale_edit", 
    "presale_delete", 
 
    # ? Proyectos PMI - NUEVAS EXPORTACIONES 
    "curva_s_view", 
    "dashboard_view", 
    "costos_view", 
    "progress_update", 
    "pmi_dashboard", 
    "pmi_activity_management", 
    "update_activity_progress_pmi", 
    "pmi_physical_progress_api", 
] 
