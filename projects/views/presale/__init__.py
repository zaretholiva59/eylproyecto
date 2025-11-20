# projects/views/presale/__init__.py

from .list import pre_sale
from .create import crear_presale
from .edit import presale_edit
from .delete import presale_delete

__all__ = [
    "pre_sale",
    "crear_presale",
    "presale_edit",
    "presale_delete",
    
]

