# projects/views/logis/__init__.py

# --- RESTAURAR TODO ---
from .purchase_order import (
    purchase_order_index,
    purchase_order_create,
    purchase_order_edit,
    purchase_order_delete,
    update_supplier_status,
    update_contabilidad_status,
)

from .autocomplete import (
    autocomplete_supplier,
    autocomplete_product,
)

__all__ = [
    "purchase_order_index",
    "purchase_order_create",
    "purchase_order_edit",
    "purchase_order_delete",
    "autocomplete_supplier",
    "autocomplete_product",
    "update_supplier_status",
    "update_contabilidad_status",
]