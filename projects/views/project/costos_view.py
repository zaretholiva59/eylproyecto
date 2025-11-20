from django.shortcuts import render, get_object_or_404
from django.contrib.humanize.templatetags.humanize import intcomma
from django.db.models import Sum, Q
from django.http import HttpResponse
from decimal import Decimal
from projects.models import (
    Projects,
    PurchaseOrder, 
    PODetailProduct,
    PODetailSupplier,
    Product,
    ClientInvoice
)
from django.db.models.functions import TruncMonth

def grid_costos_variables(request, proyecto_id):
    """Vista para mostrar el grid de costos variables"""
    
    # ✅ 1. SI NO HAY PROYECTO SELECCIONADO - MOSTRAR TEMPLATE VACÍO
    if not proyecto_id or proyecto_id == '':
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
    
    # ✅ 2. SI HAY PROYECTO SELECCIONADO
    try:
        # 1. OBTENER EL PROYECTO
        proyecto = get_object_or_404(Projects, cod_projects_id=proyecto_id)
        todos_proyectos = Projects.objects.all()

        # ✅ FUNCIONES DE FORMATEO
        def format_date(date):
            return date.strftime("%d/%m/%Y") if date else ""
        

        # 2. CALCULAR AC (ACTUAL COST)
        ac_result = PODetailProduct.objects.filter(
            purchase_order__project_code=proyecto
        ).aggregate(total=Sum('local_total'))
        ac_raw = ac_result['total'] or 0
        ac = ac_raw

        # 3. OBTENER BAC (BUDGET AT COMPLETION) desde Chance asociado
        try:
            chance = proyecto.cod_projects
            if chance and getattr(chance, 'total_costs', None):
                bac_raw = chance.total_costs
                print(f"✅ BAC desde Chance.total_costs: {bac_raw}")
            else:
                bac_raw = getattr(chance, 'cost_aprox_chance', 0) or 0
                print(f"⚠️ BAC desde Chance.cost_aprox_chance: {bac_raw}")
        except Exception as e:
            print(f"❌ Error obteniendo BAC: {e}")
            bac_raw = 0
        
        bac = bac_raw

        # 4. OBTENER DATOS PARA EL GRID
        ordenes_data = []
        ordenes_compra = PurchaseOrder.objects.filter(
            project_code=proyecto
        ).select_related('project_code').prefetch_related(
            'podetailproduct_set__product',
            'podetailsupplier_set__supplier'
            # ❌ 'invoice' QUITADO - CAUSABA ERROR
        )
        
        for oc in ordenes_compra:
            detalles_productos = oc.podetailproduct_set.all()
            for detalle in detalles_productos:
                # Factura asociada 1:1 a la OC (si existe)
                factura = getattr(oc, 'invoice', None)

                # Proveedor: priorizar el proveedor del producto si está definido; en caso contrario, usar el primer proveedor de la OC
                if detalle.product and getattr(detalle.product, 'ruc_supplier', None):
                    try:
                        name_supplier = getattr(detalle.product.ruc_supplier, 'name_supplier', '')
                    except Exception:
                        name_supplier = ''
                else:
                    proveedor_detalle = oc.podetailsupplier_set.first()
                    name_supplier = proveedor_detalle.supplier.name_supplier if proveedor_detalle and proveedor_detalle.supplier else ''

                cost_center = proyecto.cod_projects.cost_center
                cod_projects = proyecto.cod_projects.cod_projects
                
                # Los montos vienen calculados desde el modelo; no recalcular aquí
                
                # ✅ CORREGIDO: Mostrar OC como factura si no hay factura real
                invoice_number = factura.invoice_number if factura else f""
                invoice_date = format_date(factura.issue_date) if factura else ""
                
                # Construir datos para el grid
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
                    'unit_price': detalle.unit_price,
                    'currency': oc.currency,
                    'total': detalle.total,
                    'exchange_rate': oc.exchange_rate,
                    'local_total': detalle.local_total,
                    'name_supplier': name_supplier,
                    'po_number': oc.po_number,
                    'issue_date': format_date(oc.issue_date),
                    'guide_number': oc.guide_number or '',
                    'guide_date': format_date(oc.guide_date),
                    'invoice_number': invoice_number,
                    'invoice_date': invoice_date,
                    'comment': detalle.comment or '',
                }
                
                ordenes_data.append(orden_data)

        # 4.1 Totales por moneda (sumando en la moneda original de la OC)
        totals_by_currency_raw = {}
        try:
            for oc in ordenes_compra:
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

        # Nota: los montos se envían como numéricos y se formatean en plantilla
        # 5.1 FACTURACIÓN POR OC Y MES (proveedor): sumar local_total por OC según fecha de factura
        facturacion_oc_mes = []
        try:
            meses_es = {
                1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
                5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
                9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
            }
            
            # Diccionario para guardar totales por mes
            totales_por_mes = {}
            
            ordenes_con_factura = PurchaseOrder.objects.filter(project_code=proyecto).select_related('invoice')
            
            for oc in ordenes_con_factura:
                factura = getattr(oc, 'invoice', None)
                fecha_ref = factura.issue_date if (factura and factura.issue_date) else oc.issue_date
                if not fecha_ref:
                    continue
                
                mes_nombre = meses_es.get(fecha_ref.month, '')
                año = fecha_ref.year
                mes_clave = f"{mes_nombre} {año}"
                
                # Sumar todos los productos de esta OC
                total_oc = 0
                for producto in oc.podetailproduct_set.all():
                    try:
                        total_oc += float(producto.local_total or 0)
                    except Exception:
                        pass
                
                # Acumular en el mes correspondiente
                if mes_clave not in totales_por_mes:
                    totales_por_mes[mes_clave] = 0
                totales_por_mes[mes_clave] += total_oc
            
            # Crear una fila por cada mes
            for mes, total in totales_por_mes.items():
                facturacion_oc_mes.append({
                    'mes': mes,
                    'total': total
                })
            
            # Ordenar por mes
            try:
                facturacion_oc_mes.sort(key=lambda x: x['mes'])
            except Exception:
                pass

        except Exception as e:
            print(f"⚠️ Error calculando facturación por OC y mes: {e}")
            facturacion_oc_mes = []

        # 5. CALCULAR FACTURACIÓN MENSUAL (CLIENTES, VERIFICADA POR JEFE)
        facturacion_mensual = []
        total_facturado_raw = 0

        facturacion_por_mes = ClientInvoice.objects.filter(
            project=proyecto,
            status='PAGADA'
        ).annotate(
            mes=TruncMonth('fully_paid_date')
        ).values('mes').annotate(
            total=Sum('paid_amount')
        ).order_by('mes')

        print(f"✅ Meses con facturación (clientes verificada): {len(list(facturacion_por_mes))}")

        for item in facturacion_por_mes:
            if item['mes'] and item['total']:
                meses_es = {
                    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
                    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
                    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
                }
                mes_numero = item['mes'].month
                año = item['mes'].year
                mes_nombre = meses_es.get(mes_numero, '')

                facturacion_mensual.append({
                    'mes': f"{mes_nombre} {año}",
                    'total': item['total']
                })
                total_facturado_raw += item['total']
                print(f"✅ Mes {mes_nombre} {año}: {item['total']}")

        # 6. CALCULAR TOTAL FACTURADO REAL DESDE CONTABILIDAD (CLIENTES, VERIFICADO)
        try:
            total_facturado_real = ClientInvoice.objects.filter(
                project=proyecto,
                status='PAGADA'
            ).aggregate(total=Sum('paid_amount'))['total'] or 0
            print(f"✅ Total facturado (clientes verificado): {total_facturado_real}")
        except Exception as e:
            print(f"❌ Error calculando facturado de clientes: {e}")
            total_facturado_real = 0

        total_facturado = total_facturado_raw if total_facturado_raw else total_facturado_real

        # 7.1 Preparar totales por moneda para la plantilla
        currency_totals = totals_by_currency_raw

        # 7. PREPARAR CONTEXTO
        context = {
            'proyecto': proyecto,
            'ac': ac,
            'bac': bac,
            'proyectos': todos_proyectos,
            'facturado': total_facturado,
            'ordenes': ordenes_data,
            'facturacion_mes': facturacion_mensual,
            'facturacion_oc_mes': facturacion_oc_mes,
            'currency_totals': currency_totals,
        }
        
        return render(request, 'project/index.html', context)
        
    except Exception as e:
        print(f"Error en grid_costos_variables: {e}")
        # ✅ EN CASO DE ERROR, MOSTRAR TEMPLATE VACÍO
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

def exportar_excel_grid(request):
    """Vista para exportar el grid a Excel"""
    try:
        proyecto_id = request.GET.get('proyecto_id')
        if not proyecto_id:
            return HttpResponse("Proyecto ID requerido", status=400)
            
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="costos_variables.xlsx"'
        response.write(b"Excel export functionality to be implemented")
        return response
        
    except Exception as e:
        return HttpResponse(f"Error al exportar Excel: {e}", status=500)