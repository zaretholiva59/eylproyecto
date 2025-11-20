from django.urls import path
from projects.views.logis import (
    purchase_order_index,
    purchase_order_create,
    purchase_order_edit,
    purchase_order_delete,
    autocomplete_supplier,
    autocomplete_product,
    update_supplier_status,
    update_contabilidad_status,
)

urlpatterns = [
    # ✅ SOLO UNA URL para la lista de OCs
    path("", purchase_order_index, name="logis_index"),
    # Vistas de catálogo simples
    path("suppliers/", purchase_order_index, name="supplier_list"),  # reutiliza la misma vista con pestaña
    path("products/", purchase_order_index, name="product_list"),    # reutiliza la misma vista con pestaña
    
    # Crear OC
    path("create/", purchase_order_create, name="purchase_order_create"),
    
    # Editar/Eliminar OC  
    path("<str:pk>/edit/", purchase_order_edit, name="purchase_order_edit"),
    path("<str:pk>/delete/", purchase_order_delete, name="purchase_order_delete"),

    # Autocompletes
    path("autocomplete/supplier/", autocomplete_supplier, name="autocomplete_supplier"),
    path("autocomplete/product/", autocomplete_product, name="autocomplete_product"),
    # AJAX updates from grid
    path("ajax/update-supplier-status/", update_supplier_status, name="update_supplier_status"),
    path("ajax/update-contabilidad-status/", update_contabilidad_status, name="update_contabilidad_status"),
]