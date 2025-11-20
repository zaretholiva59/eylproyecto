def contabilidad_jefe(request): 
    # === MêTRICAS PMI CORREGIDAS CON DECIMAL === 
    from projects.models.chance import Chance 
    proyectos_chance = Chance.objects.all() 
    metricas_pmi = [] 
 
    for chance in proyectos_chance: 
        # Facturas relacionadas a este proyecto 
        facturas = ClientInvoice.objects.filter(project__cod_projects=chance) 
        total_facturado = facturas.aggregate(total=Sum('amount'))['total'] or Decimal('0.00') 
        total_pagado = facturas.filter(status='PAGADA').aggregate(total=Sum('amount'))['total'] or Decimal('0.00') 
 
        # MêTRICAS PMI CON DECIMAL 
        monto_contractual = chance.cost_aprox_chance 
        avance_contractual = (total_pagado / monto_contractual * Decimal('100.0')) if monto_contractual else Decimal('0.00') 
        eficiencia_cobranza = (total_pagado / total_facturado * Decimal('100.0')) if total_facturado else Decimal('0.00') 
        facturacion_vs_contrato = (total_facturado / monto_contractual * Decimal('100.0')) if monto_contractual else Decimal('0.00') 
        pendiente_facturar = monto_contractual - total_facturado 
        pendiente_cobrar = total_facturado - total_pagado 
 
        metricas_pmi.append({ 
            'proyecto': chance.dres_chance, 
            'monto_contractual': monto_contractual, 
            'total_facturado': total_facturado, 
            'total_pagado': total_pagado, 
            'avance_contractual': avance_contractual, 
            'eficiencia_cobranza': eficiencia_cobranza, 
            'facturacion_vs_contrato': facturacion_vs_contrato, 
            'pendiente_facturar': pendiente_facturar, 
            'pendiente_cobrar': pendiente_cobrar, 
        }) 
 
    # MêTRICAS GLOBALES 
    total_contractual_global = sum(m['monto_contractual'] for m in metricas_pmi) 
    total_facturado_global = sum(m['total_facturado'] for m in metricas_pmi) 
    total_pagado_global = sum(m['total_pagado'] for m in metricas_pmi) 
 
    avance_contractual_global = (total_pagado_global / total_contractual_global * Decimal('100.0')) if total_contractual_global else Decimal('0.00') 
    eficiencia_cobranza_global = (total_pagado_global / total_facturado_global * Decimal('100.0')) if total_facturado_global else Decimal('0.00') 
    facturacion_vs_contrato_global = (total_facturado_global / total_contractual_global * Decimal('100.0')) if total_contractual_global else Decimal('0.00') 
 
    # MêTRICAS OPERATIVAS (existentes) 
    pendientes_qs = ClientInvoice.objects.filter(status='PAGO_REPORTADO').order_by('payment_reported_date') 
    alertas_detalle = [] 
    for f in pendientes_qs: 
        if f.payment_reported_date: 
            f.dias_pendiente = (timezone.now().date() - f.payment_reported_date).days 
        else: 
            f.dias_pendiente = 0 
        if f.dias_pendiente 
            alertas_detalle.append({ 
                'invoice_number': f.invoice_number, 
                'amount': f.amount, 
                'dias': f.dias_pendiente, 
                'project_id': getattr(f.project, 'cod_projects_id', None), 
            }) 
 
    pendientes_count = pendientes_qs.count() 
    monto_pendiente = pendientes_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00') 
    problemas_qs = ClientInvoice.objects.filter(status__in=['PAGO_NO_RECIBIDO', 'CONTROVERSIA']) 
    problemas_count = problemas_qs.count() 
 
    context = { 
        # MêTRICAS PMI GLOBALES 
        'avance_contractual_global': avance_contractual_global, 
        'eficiencia_cobranza_global': eficiencia_cobranza_global, 
        'facturacion_vs_contrato_global': facturacion_vs_contrato_global, 
        'total_contractual_global': total_contractual_global, 
        'total_facturado_global': total_facturado_global, 
        'total_pagado_global': total_pagado_global, 
        'metricas_pmi': metricas_pmi, 
 
        # MêTRICAS OPERATIVAS 
        'pendientes_verificacion': pendientes_count, 
        'monto_pendiente': monto_pendiente, 
        'facturas_problema': problemas_count, 
        'pendientes': pendientes_qs, 
        'alertas_detalle': alertas_detalle, 
    } 
    return render(request, 'contabilidad/jefe/dashboard.html', context) 
