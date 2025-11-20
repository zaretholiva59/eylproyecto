projects_states = [
    ("Planeado", "Planeado" ),
    ("En Progreso", "En Progreso"),
    ("Completado", "Completado"),
    ("Cancelado", "Cancelado"),
]

activity_states = [
    ("Pendiente", "Pendiente"),
    ("En Progreso", "En Progreso"),
    ("Completada", "Completada"),
]

oc_state = [
    ("PENDIENTE", "Pendiente"),
    ("APROBADO", "Aprobado"),
    ("EN_PROCESO", "En Proceso"),
    ("ENTREGADO - PAGO PENDIENTE", "Entregado - Pago Pendiente"),
    ("ENTREGADO Y PAGADO", "Entregado y Pagado"),
    ("SERVICIO", "Servicio"),
    ("CANCELADO", "Cancelado"),
]

currency = [
    ("PEN", "Soles (S/)"),
    ("USD", "Dólares ($)"),
    ("EUR", "Euros (€)"),
]

customer_types = [
    ("Corporativo", "Cliente Corporativo"),
    ("PYME", "Pequeña y Mediana Empresa"),
    ("Individual", "Cliente Individual"),
    ("Gobierno", "Entidad Gubernamental"),
]

states_chance = [
    ("Prospecto", "Prospecto"),
    ("Calificada", "Oportunidad Calificada"),
    ("Propuesta", "Propuesta Enviada"),
    ("Negociacion", "En Negociación"),
    ("Ganada", "Oportunidad Ganada"),
    ("Perdida", "Oportunidad Perdida"),
    ("Cancelada", "Cancelada"),
]

general_states = [
    ("Activo", "Activo"),
    ("Inactivo", "Inactivo"),
    ("Suspendido", "Suspendido"),
    ("Bloqueado", "Bloqueado"),
]

approval_stats = [
    ("Pendiente", "Pendiente de Aprobación"),
    ("Aprobado", "Aprobado"),
    ("Rechazado", "Rechazado"),
    ("Revision", "En Revisión"),
]


ES_GR = [
            ('pending', 'Pending Reception'),
            ('partial', 'Partial Reception'), 
            ('complete', 'Complete Reception'),
        ],

STATUS_MAPPING = {
            'BORRADOR': 'PENDING',
            'EMITIDA': 'PENDING', 
            'PAGO_REPORTADO': 'PENDING',
            'PAGO_VERIFICADO': 'PAID',
            'PAGADA': 'PAID',
            'VENCIDA': 'OVERDUE',
            'PAGO_NO_RECIBIDO': 'PROBLEM',
            'CONTROVERSIA': 'PROBLEM'
        }
status_mapping = STATUS_MAPPING
INVOICE_STATUS = [
        ('BORRADOR', '📝 Borrador'),
        ('EMITIDA', '✅ Factura Emitida'),
        ('PAGO_REPORTADO', '🟡 Pago Reportado por Cliente'),
        ('PAGO_VERIFICADO', '🔵 Pago Verificado en Banco'), 
        ('PAGADA', '💰 Pagada Confirmada'),
        ('VENCIDA', '❌ Vencida'),
        ('PAGO_NO_RECIBIDO', '🚨 Pago No Recibido'),
        ('CONTROVERSIA', '⚖️ En Controversia'),
    ]
    