from django.shortcuts import render, get_object_or_404
from django.contrib.humanize.templatetags.humanize import intcomma
from django.db.models import Sum, Q
from django.http import HttpResponse
from decimal import Decimal
from django.core.exceptions import ValidationError
from projects.models import (
    Projects,
    PurchaseOrder, 
    PODetailProduct,
    PODetailSupplier,
    Product,
    Chance  # ✅ AGREGAR
)
from projects.models.invoice import Invoice
from django.core.paginator import Paginator
from projects.security.validators import (
    validate_project_id, 
    validate_search_query, 
    validate_date_range,
    validate_pagination_params,
    sanitize_input
)
import logging

# Logger de seguridad
security_logger = logging.getLogger('django.security')

def format_currency_english(amount):
    if amount is None or amount == '':
        return "0.00"
    try:
        return intcomma(amount)
    except:
        return "0.00"
def grid_costos_variables(request, proyecto_id):
    """VISTA OPTIMIZADA Y SEGURA - UNA SOLA CONSULTA PRINCIPAL"""
    
    # ✅ VALIDACIÓN DE SEGURIDAD
    try:
        proyecto_id = validate_project_id(proyecto_id)
        security_logger.info(f"Access to project costs: {proyecto_id}")
    except ValidationError as e:
        security_logger.warning(f"Invalid project ID access attempt: {proyecto_id}")
        context = {
            'error': str(e),
            'proyecto': None,
            'proyectos': Projects.objects.only('cod_projects_id', 'cost_center').all(),
            'ac': "0.00",
            'bac': "0.00",
            'facturado': "0.00",
            'ordenes': [],
            'facturacion_mes': []
        }
        return render(request, 'project/index.html', context)
    
    print(f"🔍 INICIO - Proyecto: {proyecto_id}")
    
    # 1. SI NO HAY PROYECTO
    if not proyecto_id or proyecto_id == '':
        # ✅ OPTIMIZACIÓN: Consulta ligera para dropdown
        context = {
            'proyecto': None,
            'proyectos': Projects.objects.only('cod_projects_id', 'cost_center').all(),
            'ac': "0.00",
            'bac': "0.00",
            'facturado': "0.00",
            'ordenes': [],
            'facturacion_mes': []
        }
        return render(request, 'project/index.html', context)
    
    # 2. ✅ OPTIMIZACIÓN: UNA SOLA CONSULTA CON TODAS LAS RELACIONES
    try:
        proyecto = Projects.objects.select_related(
            'cod_projects__info_costumer'
        ).prefetch_related(
            'purchaseorder_set__podetailproduct_set__product',
            'purchaseorder_set__podetailsupplier_set__supplier',
            'purchaseorder_set__invoices'
        ).get(cod_projects_id=proyecto_id)
        
        # ✅ OPTIMIZACIÓN: Consulta ligera para dropdown
        todos_proyectos = Projects.objects.only('cod_projects_id', 'cost_center').all()

        print(f"✅ Proyecto: {proyecto.cod_projects_id}")

        # ✅ OPTIMIZACIÓN: Calcular AC desde datos ya cargados
        ac_raw = Decimal('0')
        for oc in proyecto.purchaseorder_set.all():
            for detalle in oc.podetailproduct_set.all():
                if detalle.local_total:
                    ac_raw += Decimal(str(detalle.local_total))
        
        ac = format_currency_english(ac_raw)
        print(f"✅ AC: {ac}")

        # ✅ OPTIMIZACIÓN: BAC desde relación ya cargada
        bac_raw = Decimal('0')
        try:
            # Usar costos calculados de Chance si están disponibles; si no, el monto aproximado
            if hasattr(proyecto.cod_projects, 'total_costs') and proyecto.cod_projects.total_costs:
                bac_raw = Decimal(str(proyecto.cod_projects.total_costs or 0))
            else:
                bac_raw = Decimal(str(proyecto.cod_projects.cost_aprox_chance or 0))
            print(f"✅ BAC: {bac_raw}")
        except Exception as e:
            print(f"❌ Error BAC: {e}")
        
        bac = format_currency_english(bac_raw)

        # ✅ OPTIMIZACIÓN: Usar datos ya cargados para el grid
        ordenes_data = []
        ordenes_compra = proyecto.purchaseorder_set.all()

        print(f"✅ OCs encontradas: {len(ordenes_compra)}")

        def format_date(date):
            return date.strftime("%d/%m/%Y") if date else ""

        for oc in ordenes_compra:
            detalles_productos = oc.podetailproduct_set.all()
            
            for detalle in detalles_productos:
                proveedor_detalle = oc.podetailsupplier_set.first()
                
                # ✅ Factura proveedor 1:1 asociada a la OC
                factura = getattr(oc, 'invoice', None)
                if factura:
                    invoice_number = factura.invoice_number
                    invoice_date = format_date(factura.issue_date)
                    print(f"✅ Factura: {invoice_number} para OC {oc.po_number}")
                else:
                    invoice_number = ""
                    invoice_date = ""
                    print(f"ℹ️  Sin factura para OC {oc.po_number}")
                
                # DATOS DEL PROYECTO
                cost_center = proyecto.cost_center
                cod_projects = proyecto.cod_projects_id
                
                orden_data = {
                    'categoria': 'Equipamiento',
                    'cod_projects': cod_projects,
                    'cost_center': cost_center,
                    'cod_art': detalle.product.code_art if detalle.product else '',
                    'part_number': detalle.product.part_number if detalle.product else '',
                    'descrip': detalle.product.descrip if detalle.product else getattr(detalle, 'product_name', ''),
                    'manufac': detalle.product.manufac if detalle.product else '',
                    'model': detalle.product.model if detalle.product else '',
                    'sn': '',
                    'quantity': detalle.quantity,
                    'measurement_unit': detalle.measurement_unit,
                    'unit_price': format_currency_english(detalle.unit_price),
                    'currency': oc.currency,
                    'total': format_currency_english(detalle.total),
                    'exchange_rate': f"{oc.exchange_rate:.1f}" if oc.exchange_rate else "1.0",
                    'local_total': format_currency_english(detalle.local_total),
                    'name_supplier': proveedor_detalle.supplier.name_supplier if proveedor_detalle and proveedor_detalle.supplier else '',
                    'po_number': oc.po_number,
                    'issue_date': format_date(oc.issue_date),
                    'guide_number': oc.guide_number or '',
                    'guide_date': format_date(oc.guide_date),
                    'invoice_number': invoice_number,
                    'invoice_date': invoice_date,
                    'comment': detalle.comment or '',
                }
                
                ordenes_data.append(orden_data)

        # ✅ OPTIMIZACIÓN: Facturación mensual desde datos ya cargados
        facturacion_mensual = []
        total_facturado_raw = Decimal('0')
        
        # Agrupar por mes usando datos ya cargados
        facturacion_por_mes = {}
        for oc in ordenes_compra:
            if oc.issue_date:
                mes_key = oc.issue_date.strftime('%Y-%m')
                for detalle in oc.podetailproduct_set.all():
                    if detalle.local_total:
                        if mes_key not in facturacion_por_mes:
                            facturacion_por_mes[mes_key] = Decimal('0')
                        facturacion_por_mes[mes_key] += Decimal(str(detalle.local_total))

        print(f"✅ Meses con facturación: {len(facturacion_por_mes)}")

        # Procesar meses ordenados
        for mes_key in sorted(facturacion_por_mes.keys()):
            total_mes = facturacion_por_mes[mes_key]
            if total_mes > 0:
                # Convertir YYYY-MM a formato legible
                año, mes = mes_key.split('-')
                meses_es = {
                    '01': 'Enero', '02': 'Febrero', '03': 'Marzo', '04': 'Abril',
                    '05': 'Mayo', '06': 'Junio', '07': 'Julio', '08': 'Agosto',
                    '09': 'Septiembre', '10': 'Octubre', '11': 'Noviembre', '12': 'Diciembre'
                }
                mes_nombre = meses_es.get(mes, '')
                
                facturacion_mensual.append({
                    'mes': f"{mes_nombre} {año}",
                    'total': format_currency_english(total_mes)
                })
                total_facturado_raw += total_mes
        
        # CALCULAR TOTAL FACTURADO
        facturado = format_currency_english(total_facturado_raw)
        
        print(f"✅ Total facturado: {facturado}")

        # PREPARAR CONTEXTO
        context = {
            'proyecto': proyecto,
            'ac': ac,
            'bac': bac,
            'proyectos': todos_proyectos,
            'facturado': facturado,
            'ordenes': ordenes_data,
            'facturacion_mes': facturacion_mensual,
        }
        
        return render(request, 'project/index.html', context)
        
    except Exception as e:
        print(f"❌ ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        
        context = {
            'proyecto': None,
            'proyectos': Projects.objects.all(),
            'ac': "0.00",
            'bac': "0.00",
            'facturado': "0.00",
            'ordenes': [],
            'facturacion_mes': []
        }
        return render(request, 'project/index.html', context)

# === FUNCIONES DE LOGÍSTICA (AGREGAR AL FINAL DEL ARCHIVO) ===

def purchase_order_index(request):
    """Vista principal de logística OPTIMIZADA Y SEGURA"""
    from django.shortcuts import render
    from django.core.cache import cache
    from projects.models import Projects, PurchaseOrder, PODetailSupplier, PODetailProduct, Supplier, Product
    
    # ✅ VALIDACIÓN Y SANITIZACIÓN DE PARÁMETROS
    try:
        proyecto_id = validate_project_id(request.GET.get('proyecto_id')) if request.GET.get('proyecto_id') else None
        supplier_q = validate_search_query(request.GET.get('supplier'))
        product_q = validate_search_query(request.GET.get('product'))
        po_q = validate_search_query(request.GET.get('po'))
        sort = sanitize_input(request.GET.get('sort', '-issue_date'))
        status_q = sanitize_input(request.GET.get('status'))
        currency_q = sanitize_input(request.GET.get('currency'))
        localimp_q = sanitize_input(request.GET.get('local'))
        manuf_q = validate_search_query(request.GET.get('manuf'))
        date_from, date_to = validate_date_range(
            request.GET.get('from'), 
            request.GET.get('to')
        )
        
        # Validar parámetros de paginación
        page, page_size = validate_pagination_params(
            request.GET.get('page', '1'),
            request.GET.get('page_size', '25')
        )
        
        security_logger.info(f"Purchase order search: proyecto={proyecto_id}, supplier={supplier_q[:20] if supplier_q else None}")
        
    except ValidationError as e:
        security_logger.warning(f"Invalid search parameters: {str(e)}")
        return render(request, "logistica/index.html", {
            'error': str(e),
            'ocs': PurchaseOrder.objects.none(),
            'ocs_page': None,
            'proyectos': Projects.objects.only('cod_projects_id', 'cost_center').all(),
            'proyecto_seleccionado': None,
            'suppliers_list': [],
            'products_list': [],
            'po_list': [],
            'active_tab': 'orders',
            'total_rows': 0,
            'kpi_total_ocs': 0,
            'kpi_total_local': 0,
            'kpi_entregado_pagado': 0,
            'kpi_lead_time_prom': 0,
        })
    
    # ✅ OPTIMIZACIÓN: Cache key basado en parámetros
    cache_key = f'purchase_orders_{proyecto_id}_{supplier_q}_{product_q}_{po_q}_{sort}_{status_q}_{currency_q}_{localimp_q}_{manuf_q}_{date_from}_{date_to}'
    cached_result = cache.get(cache_key)
    
    if cached_result:
        return render(request, "logistica/index.html", cached_result)
    
    proyecto_seleccionado = None

    # ✅ OPTIMIZACIÓN: Construir queryset base optimizado
    base_queryset = PurchaseOrder.objects.select_related(
        "project_code",
        "invoice"
    ).prefetch_related(
        "podetailproduct_set__product",
        "podetailsupplier_set__supplier"
    )

    if proyecto_id:
        try:
            proyecto_seleccionado = Projects.objects.only(
                'cod_projects_id', 'cost_center', 'state_projects'
            ).get(cod_projects_id=proyecto_id)
            ocs = base_queryset.filter(project_code=proyecto_seleccionado)
        except Projects.DoesNotExist:
            ocs = PurchaseOrder.objects.none()
    else:
        ocs = base_queryset

    # ordenar después de aplicar filtros
    valid_sorts = ['issue_date','-issue_date','total_amount','-total_amount','po_status','-po_status']
    ocs = ocs.order_by(sort if sort in valid_sorts else '-issue_date')

    # ✅ OPTIMIZACIÓN: Aplicar filtros de forma eficiente
    from django.db.models import Q
    
    # Construir filtros Q de forma eficiente
    filters = Q()
    
    if supplier_q:
        filters &= (
            Q(podetailsupplier_set__supplier__ruc_supplier__icontains=supplier_q) |
            Q(podetailsupplier_set__supplier__name_supplier__icontains=supplier_q)
        )
    if product_q:
        filters &= (
            Q(podetailproduct_set__product__code_art__icontains=product_q) |
            Q(podetailproduct_set__product__part_number__icontains=product_q)
        )
    if po_q:
        filters &= Q(po_number__icontains=po_q)
    if status_q:
        filters &= Q(po_status=status_q)
    if currency_q:
        filters &= Q(currency=currency_q)
    if localimp_q:
        filters &= Q(local_import=localimp_q)
    if manuf_q:
        filters &= Q(podetailproduct_set__product__manufac__icontains=manuf_q)
    if date_from:
        filters &= Q(issue_date__gte=date_from)
    if date_to:
        filters &= Q(issue_date__lte=date_to)
    
    # Aplicar todos los filtros de una vez
    if filters:
        ocs = ocs.filter(filters)

    # ✅ OPTIMIZACIÓN: Consultas optimizadas para listas
    # Usar solo los campos necesarios para las listas
    suppliers_list = Supplier.objects.filter(
        podetailsupplier__purchase_order__in=ocs
    ).only('ruc_supplier', 'name_supplier').distinct().order_by('name_supplier')

    products_list = Product.objects.filter(
        podetailproduct__purchase_order__in=ocs
    ).only('code_art', 'part_number', 'manufac').distinct().order_by('part_number')

    # ✅ OPTIMIZACIÓN: Lista de OCs optimizada
    po_numbers = ocs.values_list('po_number', flat=True).distinct()
    po_list = PurchaseOrder.objects.filter(
        po_number__in=po_numbers
    ).only('po_number', 'issue_date').order_by('-issue_date')

    # ✅ OPTIMIZACIÓN: Proyectos con campos mínimos
    proyectos = Projects.objects.only('cod_projects_id', 'cost_center', 'state_projects').all()

    # Opciones para subfiltros
    statuses_list = ocs.values_list('po_status', flat=True).distinct().order_by('po_status')
    currencies_list = ocs.values_list('currency', flat=True).distinct().order_by('currency')
    manuf_list = Product.objects.filter(podetailproduct__purchase_order__in=ocs).values_list('manufac', flat=True).distinct().order_by('manufac')

    # Determinar pestaña activa segun ruta
    active_tab = 'orders'
    try:
        url_name = request.resolver_match.url_name
        if url_name == 'supplier_list':
            active_tab = 'suppliers'
        elif url_name == 'product_list':
            active_tab = 'products'
    except Exception:
        active_tab = 'orders'

    # ✅ OPTIMIZACIÓN: KPIs con agregaciones eficientes
    from django.db.models import Sum, Count, Avg
    
    # Usar agregaciones de Django en lugar de Python
    kpi_data = ocs.aggregate(
        total_ocs=Count('po_number', distinct=True),
        total_local=Sum('podetailproduct__local_total'),
        entregado_pagado=Count('po_number', filter=Q(po_status__icontains='PAGADO')),
        lead_time_prom=Avg('te')
    )
    
    kpi_total_ocs = kpi_data['total_ocs'] or 0
    kpi_total_local = kpi_data['total_local'] or 0
    kpi_entregado_pagado = kpi_data['entregado_pagado'] or 0
    kpi_lead_time_prom = kpi_data['lead_time_prom'] or 0

    # Totales por moneda para el grid (sumando en moneda original de la OC)
    totals_by_currency_raw = {}
    try:
        for oc in ocs:
            # iterar detalles ya prefetchados
            for detalle in oc.podetailproduct_set.all():
                cur = oc.currency or 'PEN'
                if cur not in totals_by_currency_raw:
                    totals_by_currency_raw[cur] = Decimal('0')
                try:
                    totals_by_currency_raw[cur] += Decimal(str(detalle.total or 0))
                except Exception:
                    pass
    except Exception:
        totals_by_currency_raw = {}

    currency_totals = {k: format_currency_english(v) for k, v in totals_by_currency_raw.items()}

    # Listas de estados para selects en el grid (valores existentes)
    supplier_status_list = PODetailSupplier.objects.filter(
        purchase_order__in=ocs
    ).values_list('supplier_status', flat=True).distinct().order_by('supplier_status')

    status_contab_list = PODetailSupplier.objects.filter(
        purchase_order__in=ocs
    ).values_list('status_factura_contabilidad', flat=True).distinct().order_by('status_factura_contabilidad')

    # ✅ OPTIMIZACIÓN: Paginación ya validada arriba

    paginator = Paginator(ocs, page_size)
    ocs_page = paginator.get_page(page)

    # Calcular índices para mostrar
    start_index = ocs_page.start_index()
    end_index = ocs_page.end_index()
    total_rows = paginator.count

    # ✅ OPTIMIZACIÓN: Determinar pestaña activa
    active_tab = 'orders'
    try:
        url_name = request.resolver_match.url_name
        if url_name == 'supplier_list':
            active_tab = 'suppliers'
        elif url_name == 'product_list':
            active_tab = 'products'
    except Exception:
        active_tab = 'orders'

    # ✅ OPTIMIZACIÓN: Preparar contexto
    context = {
        "ocs": ocs,
        "ocs_page": ocs_page,
        "proyectos": proyectos,
        "proyecto_seleccionado": proyecto_seleccionado,
        "supplier_q": supplier_q or "",
        "product_q": product_q or "",
        "po_q": po_q or "",
        "suppliers_list": suppliers_list,
        "products_list": products_list,
        "po_list": po_list,
        "active_tab": active_tab,
        "sort": sort,
        "page": page,
        "page_size": page_size,
        "total_rows": total_rows,
        "start_index": start_index,
        "end_index": end_index,
        "status_q": status_q or "",
        "currency_q": currency_q or "",
        "localimp_q": localimp_q or "",
        "manuf_q": manuf_q or "",
        "date_from": date_from or "",
        "date_to": date_to or "",
        "kpi_total_ocs": kpi_total_ocs,
        "kpi_total_local": kpi_total_local,
        "kpi_entregado_pagado": kpi_entregado_pagado,
        "kpi_lead_time_prom": kpi_lead_time_prom,
        "statuses_list": list(statuses_list),
        "supplier_status_list": list(supplier_status_list),
        "status_contab_list": list(status_contab_list),
        "currencies_list": list(currencies_list),
        "manuf_list": list(manuf_list),
        "currency_totals": currency_totals,
    }
    
    # ✅ OPTIMIZACIÓN: Cache del resultado por 5 minutos
    cache.set(cache_key, context, 300)
    
    return render(request, "logistica/index.html", context)

def purchase_order_create(request):
    """Crear orden de compra"""
    from django.shortcuts import render
    return render(request, "logistica/create.html", {})

def purchase_order_edit(request, pk):
    """Editar orden de compra"""
    from django.shortcuts import render
    return render(request, "logistica/edit.html", {})

def purchase_order_delete(request, pk):
    """Eliminar orden de compra""" 
    from django.shortcuts import redirect
    return redirect('logis_index')

# ==============================
# AJAX: Actualización en el GRID
# ==============================
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from projects.security.validators import sanitize_input

@require_POST
def update_supplier_status(request):
    """Actualiza supplier_status de un proveedor en una OC desde el grid"""
    try:
        po_number = sanitize_input(request.POST.get('po_number') or '')
        supplier_ruc = sanitize_input(request.POST.get('supplier_ruc') or '')
        new_status = sanitize_input(request.POST.get('status') or '')

        if not po_number or not supplier_ruc:
            return JsonResponse({"ok": False, "error": "Parámetros incompletos"}, status=400)

        po = PurchaseOrder.objects.get(po_number=po_number)
        from projects.models.supplier import Supplier
        supplier = Supplier.objects.get(ruc_supplier=supplier_ruc)

        sp = PODetailSupplier.objects.filter(purchase_order=po, supplier=supplier).first()
        if not sp:
            return JsonResponse({"ok": False, "error": "Proveedor no asociado a la OC"}, status=404)

        sp.supplier_status = new_status
        sp.save(update_fields=['supplier_status'])
        return JsonResponse({"ok": True})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@require_POST
def update_contabilidad_status(request):
    """Actualiza status_factura_contabilidad de un proveedor en una OC desde el grid"""
    try:
        po_number = sanitize_input(request.POST.get('po_number') or '')
        supplier_ruc = sanitize_input(request.POST.get('supplier_ruc') or '')
        new_status = sanitize_input(request.POST.get('status') or '')

        if not po_number or not supplier_ruc:
            return JsonResponse({"ok": False, "error": "Parámetros incompletos"}, status=400)

        po = PurchaseOrder.objects.get(po_number=po_number)
        from projects.models.supplier import Supplier
        supplier = Supplier.objects.get(ruc_supplier=supplier_ruc)

        sp = PODetailSupplier.objects.filter(purchase_order=po, supplier=supplier).first()
        if not sp:
            return JsonResponse({"ok": False, "error": "Proveedor no asociado a la OC"}, status=404)

        sp.status_factura_contabilidad = new_status
        sp.save(update_fields=['status_factura_contabilidad'])
        return JsonResponse({"ok": True})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)