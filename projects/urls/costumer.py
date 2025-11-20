from django.urls import path
from projects.views.costumer import (
    customers_list,
    customer_detail,
    customer_create,
    customer_edit,
    customer_delete,
)

urlpatterns = [
    path('', customers_list, name='customers_list'),
    path('crear/', customer_create, name='customer_create'),
    path('<str:ruc>/', customer_detail, name='customer_detail'),
    path('<str:ruc>/editar/', customer_edit, name='customer_edit'),
    path('<str:ruc>/eliminar/', customer_delete, name='customer_delete'),
]