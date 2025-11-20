# projects/urls/contabilidad.py - URLs COMPLETAS Y CORREGIDAS
from django.urls import path
from projects.views.contabilidad.contabilidad_views import (
    contabilidad_asistente,
    contabilidad_seleccion,
    factura_cliente_crear,
    factura_cliente_list,
    factura_cliente_parse_pdf,
    factura_reportar_pago,
    factura_verificar_pago,
    pagos_status,
    reportes_contables,
    verificacion_bancaria,
    verificacion_bancaria_simple,
    contabilidad_jefe,
)

app_name = 'contabilidad'

urlpatterns = [
    # Pagina de seleccion de rol - URL CORREGIDA
    path('', contabilidad_seleccion, name='seleccion_rol'),

    # Dashboards por rol - URLs CORREGIDAS
    path('jefe/', contabilidad_jefe, name='jefe_dashboard'),
    path('asistente/', contabilidad_asistente, name='asistente_dashboard'),

    # Facturas de clientes - URLs CORREGIDAS
    path('facturas-clientes/', factura_cliente_list, name='factura_cliente_list'),
    path('facturas-clientes/crear/', factura_cliente_crear, name='factura_cliente_crear'),
    path('facturas-clientes/parse-pdf/', factura_cliente_parse_pdf, name='factura_cliente_parse_pdf'),

    # Cambios de estado - URLs NUEVAS
    path('factura/<int:factura_id>/reportar-pago/', factura_reportar_pago, name='reportar_pago'),
    path('factura/<int:factura_id>/verificar-pago/', factura_verificar_pago, name='verificar_pago'),

    # Verificacion bancaria - URL CORREGIDA
    path('verificacion-bancaria/', verificacion_bancaria, name='verificacion_bancaria'),
    path('verificacion-bancaria/simple/', verificacion_bancaria_simple, name='verificacion_bancaria_simple'),

    # Estado de pagos
    path('pagos/', pagos_status, name='pagos_status'),

    # Aprobaciones - URL NUEVA (redirige a estado de pagos)
    path('aprobaciones/', pagos_status, name='aprobaciones'),

    # Reportes - URL CORREGIDA
    path('reportes/', reportes_contables, name='reportes_contables'),

    # URL LEGACY para compatibilidad con base.html
    path('dashboard/', contabilidad_seleccion, name='contabilidad_dashboard'),
]