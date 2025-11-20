from projects.services.invoice_management.client_invoice_pdf_parser import ClientInvoicePDFParser
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, F
from decimal import Decimal
from datetime import timedelta
from django.http import JsonResponse
import os
from projects.models.client_invoice import ClientInvoice
from projects.models.projects import Projects
from projects.models.invoice import Invoice
from django.contrib.auth import get_user_model

User = get_user_model()

def contabilidad_seleccion(request):
    return render(request, 'contabilidad/seleccion_rol.html')


def contabilidad_asistente(request):
    facturas_emitidas = ClientInvoice.objects.filter(status='EMITIDA').count()
    pagos_reportados = ClientInvoice.objects.filter(status='PAGO_REPORTADO').count()
    facturas_pagadas = ClientInvoice.objects.filter(status='PAGADA').count()

    total_facturado = ClientInvoice.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    ultimas_facturas = ClientInvoice.objects.order_by('-invoice_date')[:10]

    context = {
        'facturas_emitidas': facturas_emitidas,
        'pagos_reportados': pagos_reportados,
        'facturas_pagadas': facturas_pagadas,
        'total_facturado': total_facturado,
        'ultimas_facturas': ultimas_facturas,
    }
    return render(request, 'contabilidad/asistente/dashboard.html', context)


def contabilidad_jefe(request):
    # Facturas con pago reportado y cÃ¡lculo de dÃ­as pendientes
    pendientes_qs = ClientInvoice.objects.filter(status='PAGO_REPORTADO').order_by('payment_reported_date')
    alertas_detalle = []
    for f in pendientes_qs:
        if f.payment_reported_date:
            f.dias_pendiente = (timezone.now().date() - f.payment_reported_date).days
        else:
            f.dias_pendiente = 0
        # Retraso si > 3 dÃ­as
        if f.dias_pendiente > 3:
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

    total_facturado = ClientInvoice.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_pagado = ClientInvoice.objects.filter(status='PAGADA').aggregate(total=Sum('paid_amount'))['total'] or Decimal('0.00')
    eficiencia_cobranza = (float(total_pagado) / float(total_facturado) * 100.0) if total_facturado else 0.0

    # MÃ©tricas por proyecto
    metricas_proyectos = []
    for resumen in ClientInvoice.objects.values('project__cod_projects_id').annotate(
        total_facturado=Sum('amount'),
        pagado=Sum('paid_amount')
    ).order_by('project__cod_projects_id'):
        total = resumen['total_facturado'] or Decimal('0.00')
        pagado = resumen['pagado'] or Decimal('0.00')
        pendiente = total - pagado
        eficiencia = float(pagado) / float(total) * 100.0 if total else 0.0
        metricas_proyectos.append({
            'proyecto': resumen['project__cod_projects_id'],
            'total_facturado': total,
            'pagado': pagado,
            'pendiente': pendiente,
            'eficiencia': eficiencia,
        })

    context = {
        # Contadores y montos para tarjetas y header
        'pendientes_verificacion': pendientes_count,
        'monto_pendiente': monto_pendiente,
        'facturas_problema': problemas_count,
        'total_facturado': total_facturado,
        'eficiencia_cobranza': eficiencia_cobranza,
        # Datos de tabla
        'pendientes': pendientes_qs,
        'metricas_proyectos': metricas_proyectos,
        # Alertas para popover (solo si hay retrasos)
        'alertas_detalle': alertas_detalle,
    }
    return render(request, 'contabilidad/jefe/dashboard.html', context)


def factura_cliente_list(request):
    estado_filtro = request.GET.get('estado', 'todas')
    buscar = request.GET.get('buscar', '').strip()

    queryset = ClientInvoice.objects.all().order_by('-invoice_date')
    if estado_filtro and estado_filtro != 'todas':
        queryset = queryset.filter(status=estado_filtro)

    if buscar:
        from django.db.models import Q
        queryset = queryset.filter(
            Q(invoice_number__icontains=buscar) |
            Q(project__cod_projects_id__icontains=buscar)
        )

    context = {
        'facturas': queryset,
        'estados': ClientInvoice.INVOICE_STATUS,
        'estado_filtro': estado_filtro,
        'buscar': buscar,
        'es_jefe': getattr(request.user, 'is_staff', False) or getattr(request.user, 'is_superuser', False),
    }
    return render(request, 'contabilidad/shared/factura_cliente_list.html', context)


def factura_cliente_parse_pdf(request):
    """
    Vista AJAX para procesar PDF cuando el usuario selecciona un archivo.
    Retorna JSON con los datos extraÃ­dos del PDF.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'MÃ©todo no permitido'}, status=405)
    
    try:
        invoice_file = request.FILES.get('invoice_file')
        if not invoice_file:
            return JsonResponse({'error': 'No se proporcionÃ³ ningÃºn archivo'}, status=400)
        
        # Aceptar PDFs e imÃ¡genes
        file_ext = os.path.splitext(invoice_file.name.lower())[1]
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
        if file_ext not in allowed_extensions:
            return JsonResponse({
                'error': f'Formato de archivo no soportado. Formatos permitidos: PDF, JPG, PNG, GIF, BMP, TIFF, WEBP'
            }, status=400)
        
        file_type = "imagen" if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'] else "PDF"
        print(f"ðŸ”„ Procesando {file_type} vÃ­a AJAX...")
        parser = ClientInvoicePDFParser()
        pdf_data = parser.parse_uploaded_pdf(invoice_file)
        
        if pdf_data:
            # Convertir Decimal a string para JSON
            if 'amount' in pdf_data and isinstance(pdf_data['amount'], Decimal):
                pdf_data['amount'] = str(pdf_data['amount'])
            
            print(f"âœ… Datos extraÃ­dos: {pdf_data}")
            return JsonResponse({
                'success': True,
                'data': pdf_data,
                'message': f'Se detectaron {len(pdf_data)} campos del PDF automÃ¡ticamente'
            })
        else:
            # Verificar si el archivo es realmente un PDF con texto
            error_message = 'No se pudieron detectar datos en el PDF. '
            error_message += 'El PDF podrÃ­a ser una imagen escaneada. '
            error_message += 'Por favor, verifica que el PDF contenga texto seleccionable (no solo imÃ¡genes).'
            
            return JsonResponse({
                'success': False,
                'data': {},
                'message': error_message,
                'is_image_pdf': True  # Indicar que podrÃ­a ser una imagen
            })
            
    except Exception as e:
        print(f"âŒ Error procesando PDF: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'error': f'Error al procesar PDF: {str(e)}'
        }, status=500)


def factura_cliente_crear(request):
    proyectos = Projects.objects.all().order_by('cod_projects_id')

    # NUEVO: Variable para datos extraÃ­dos del PDF
    pdf_data = {}
    
    if request.method == 'POST':
        try:
            # âœ… NUEVA FUNCIONALIDAD: Leer PDF automÃ¡ticamente
            invoice_file = request.FILES.get('invoice_file')
            if invoice_file and invoice_file.name.lower().endswith('.pdf'):
                print("ðŸ”„ Iniciando lectura automÃ¡tica de PDF...")
                parser = ClientInvoicePDFParser()
                pdf_data = parser.parse_uploaded_pdf(invoice_file)
                
                # Mostrar mensaje al usuario
                if pdf_data:
                    messages.info(request, f'âœ… Se detectaron {len(pdf_data)} campos del PDF automÃ¡ticamente')
                else:
                    messages.warning(request, 'âš ï¸ No se pudieron detectar datos en el PDF')

            # Usar datos del PDF si estÃ¡n disponibles Y el usuario no los llenÃ³ manualmente
            project_id = request.POST.get('project') or None
            invoice_number = request.POST.get('invoice_number') or pdf_data.get('invoice_number')
            amount = request.POST.get('amount') or pdf_data.get('amount')
            invoice_date = request.POST.get('invoice_date') or pdf_data.get('invoice_date')
            due_date = request.POST.get('due_date') or pdf_data.get('due_date')
            description = request.POST.get('description', '')
            bank_reference = request.POST.get('bank_reference') or pdf_data.get('bank_reference')

            # Validar campos obligatorios
            if not invoice_number:
                messages.error(request, 'El nÃºmero de factura es obligatorio')
                return render(request, 'contabilidad/asistente/factura_cliente_crear.html', {
                    'proyectos': proyectos,
                    'pdf_data': pdf_data  # â† Pasar datos extraÃ­dos
                })

            # Crear la factura (tu cÃ³digo original)
            factura = ClientInvoice(
                project_id=project_id,
                invoice_number=invoice_number,
                amount=Decimal(amount or '0.00'),
                invoice_date=invoice_date,
                due_date=due_date,
                description=description,
                status='EMITIDA',
                bank_reference=bank_reference,
            )
            
            if invoice_file:
                factura.invoice_file = invoice_file
                
            factura.save()

            messages.success(request, 'Factura creada correctamente')
            return redirect('contabilidad:factura_cliente_list')

        except Exception as e:
            messages.error(request, f'Error al crear factura: {e}')
            print(f"âŒ Error en vista: {e}")

    # GET request - mostrar formulario
    return render(request, 'contabilidad/asistente/factura_cliente_crear.html', {
        'proyectos': proyectos,
        'pdf_data': pdf_data  # â† Pasar datos extraÃ­dos a la plantilla
    })

def factura_reportar_pago(request, factura_id):
    factura = get_object_or_404(ClientInvoice, id=factura_id)
    
    if request.method == 'POST':
        factura.bank_reference = request.POST.get('bank_reference', '')
        factura.client_notes = request.POST.get('client_notes', '')
        factura.payment_reported_date = timezone.now().date()
        factura.status = 'PAGO_REPORTADO'
        
        # âœ… SOLUCIÃ“N: Manejar usuario no autenticado
        if request.user.is_authenticated:
            factura.reported_by = request.user
        else:
            # Usar un usuario por defecto o dejar como None
            try:
                default_user = User.objects.filter(is_superuser=True).first()
                if default_user:
                    factura.reported_by = default_user
                # Si no hay usuarios, dejar como None (si el campo lo permite)
            except:
                pass  # Si hay error, dejar como None
        
        factura.save()
        messages.success(request, 'Pago reportado correctamente')
        return redirect('contabilidad:factura_cliente_list')
    
    return render(request, 'contabilidad/asistente/factura_reportar_pago.html', {'factura': factura})

def factura_verificar_pago(request, factura_id):
    factura = get_object_or_404(ClientInvoice, id=factura_id)
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        notas = request.POST.get('verification_notes', '')
        
        if accion == 'verificar':
            try:
                factura.paid_amount = Decimal(request.POST.get('paid_amount') or '0.00')
                factura.bank_confirmation_code = request.POST.get('bank_confirmation_code', '')
                factura.verification_notes = notas
                factura.bank_verified_date = timezone.now().date()
                
                # âœ… SOLUCIÃ“N: Manejar usuario no autenticado
                if request.user.is_authenticated:
                    factura.verified_by = request.user
                else:
                    try:
                        default_user = User.objects.filter(is_superuser=True).first()
                        if default_user:
                            factura.verified_by = default_user
                    except:
                        pass  # Si hay error, dejar como None
                
                factura.status = 'PAGO_VERIFICADO'
                factura.save()
                messages.success(request, 'Pago verificado y factura marcada como PAGADA')
            except Exception as e:
                messages.error(request, f'Error al verificar pago: {e}')
        elif accion == 'rechazar':
            factura.verification_notes = notas
            factura.status = 'PAGO_NO_RECIBIDO'
            factura.save()
            messages.warning(request, 'Factura marcada como PAGO NO RECIBIDO')
        
        return redirect('contabilidad:factura_cliente_list')
    
    return render(request, 'contabilidad/jefe/factura_verificar_pago.html', {'factura': factura})

def verificacion_bancaria(request):
    # Alias legacy: redirige al motor simple para homogeneidad
    return redirect('contabilidad:verificacion_bancaria_simple')

def verificacion_bancaria_simple(request):
    if request.method == 'POST':
        try:
            factura_id = request.POST.get('invoice_id') or request.POST.get('factura_id')
            accion = request.POST.get('accion')
            factura = get_object_or_404(ClientInvoice, id=factura_id)
            
            if accion == 'problema':
                factura.verification_notes = request.POST.get('verification_notes', '')
                factura.status = 'PAGO_NO_RECIBIDO'
            else:
                factura.paid_amount = Decimal(request.POST.get('paid_amount') or factura.amount)
                factura.bank_confirmation_code = request.POST.get('bank_confirmation_code', '')
                factura.verification_notes = request.POST.get('verification_notes', '')
                factura.bank_verified_date = timezone.now().date()
                
                # âœ… SOLUCIÃ“N: Manejar usuario no autenticado
                if request.user.is_authenticated:
                    factura.verified_by = request.user
                else:
                    try:
                        default_user = User.objects.filter(is_superuser=True).first()
                        if default_user:
                            factura.verified_by = default_user
                    except:
                        pass  # Si hay error, dejar como None
                
                factura.status = 'PAGO_VERIFICADO'
            
            factura.save()
            messages.success(request, f'Factura {factura.invoice_number} actualizada correctamente')
        except Exception as e:
            messages.error(request, f'Error al actualizar factura: {e}')
        return redirect('contabilidad:verificacion_bancaria_simple')

    # GET: mostrar pendientes
    facturas_pendientes = ClientInvoice.objects.filter(status='PAGO_REPORTADO').order_by('payment_reported_date')
    for f in facturas_pendientes:
        if f.payment_reported_date:
            f.dias_espera = (timezone.now().date() - f.payment_reported_date).days
        else:
            f.dias_espera = 0

    context = {
        'facturas_pendientes': facturas_pendientes,
        'total_pendientes': facturas_pendientes.count(),
        'monto_total_pendiente': facturas_pendientes.aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
    }
    return render(request, 'contabilidad/jefe/verificacion_bancaria.html', context)

def pagos_status(request):
    # Proveedores (modelo Invoice)
    facturas_pendientes_prov = Invoice.objects.all()
    total_pendiente_proveedores = facturas_pendientes_prov.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

    # Clientes
    facturas_clientes_pendientes = ClientInvoice.objects.filter(status__in=['EMITIDA', 'PAGO_REPORTADO'])
    total_pendiente_clientes = facturas_clientes_pendientes.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    context = {
        'facturas_pendientes': facturas_pendientes_prov,
        'total_pendiente_proveedores': total_pendiente_proveedores,
        'facturas_clientes_pendientes': facturas_clientes_pendientes,
        'total_pendiente_clientes': total_pendiente_clientes,
    }
    return render(request, 'contabilidad/jefe/pagos.html', context)

def reportes_contables(request):
    # Reporte bÃ¡sico para activar la ruta (plantilla estÃ¡ vacÃ­a)
    total_facturado = ClientInvoice.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_pagado = ClientInvoice.objects.filter(status='PAGADA').aggregate(total=Sum('paid_amount'))['total'] or Decimal('0.00')
    context = {
        'total_facturado': total_facturado,
        'total_pagado': total_pagado,
    }
    return render(request, 'contabilidad/jefe/reportes.html', context)
