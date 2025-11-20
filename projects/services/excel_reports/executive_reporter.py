from projects.models import Projects, PurchaseOrder, Invoice, PODetailProduct, ClientInvoice
from django.db.models import Sum
from datetime import timedelta
from projects.services.baseline_service import BaselineService

class ExecutiveReporter:
    """Servicio para datos ejecutivos de Excel - CORREGIDO"""

    @staticmethod
    def generate_executive_data(project_id):
        """Genera datos ejecutivos - CORREGIDO según PMI"""
        project = Projects.objects.get(cod_projects_id=project_id)
        
        # ✅ Presupuesto y monto contractual desde Chance asociado
        try:
            bac_presupuestado = getattr(project.cod_projects, 'total_costs', 0)
            contract_amount = getattr(project.cod_projects, 'cost_aprox_chance', 0)
        except Exception:
            bac_presupuestado = 0
            contract_amount = 0
        # Normalizar tipos para evitar mezcla Decimal/float
        bac_presupuestado = float(bac_presupuestado or 0)
        contract_amount = float(contract_amount or 0)
        
        # ✅ AC/Costo Total desde detalles de OC en moneda local (misma fuente que Grid)
        try:
            ac_result = PODetailProduct.objects.filter(
                purchase_order__project_code=project
            ).aggregate(total=Sum('local_total'))
            total_gastado = float(ac_result['total'] or 0)
        except Exception:
            # Fallback: suma de total_amount de OC
            ocs = PurchaseOrder.objects.filter(project_code=project)
            total_gastado = float(sum([oc.total_amount for oc in ocs if oc.total_amount]))
        
        # ✅ Fallback a baseline si no hay costos reales
        if total_gastado == 0.0:
            try:
                bl = BaselineService.get_monthly_arrays(project_id)
                if bl and bl.get('ac'):
                    total_gastado = float(bl['ac'][-1])
            except Exception:
                pass
        
        # Porcentaje ejecutado sobre el PRESUPUESTO (no sobre la venta)
        porcentaje_ejecutado = (total_gastado / bac_presupuestado * 100.0) if bac_presupuestado > 0 else 0.0

        # ✅ Facturado por el cliente REAL (misma fuente que Grid): facturas PAGADAS
        try:
            total_facturado_cliente = ClientInvoice.objects.filter(
                project=project,
                status='PAGADA'
            ).aggregate(total=Sum('paid_amount'))['total'] or 0
            total_facturado_cliente = float(total_facturado_cliente)
        except Exception:
            total_facturado_cliente = 0.0

        # ✅ Facturación mensual (clientes verificada)
        facturacion_mensual = []
        try:
            from django.db.models.functions import TruncMonth
            facturacion_por_mes = ClientInvoice.objects.filter(
                project=project,
                status='PAGADA'
            ).annotate(
                mes=TruncMonth('fully_paid_date')
            ).values('mes').annotate(
                total=Sum('paid_amount')
            ).order_by('mes')

            meses_es = {
                1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
                5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
                9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
            }

            for item in facturacion_por_mes:
                if item['mes'] and item['total']:
                    mes_numero = item['mes'].month
                    año = item['mes'].year
                    mes_nombre = meses_es.get(mes_numero, '')
                    facturacion_mensual.append({
                        'mes': f"{mes_nombre} {año}",
                        'total': float(item['total'])
                    })
        except Exception:
            facturacion_mensual = []
        
        # ✅ Fallback a baseline si no hay facturación mensual o total
        try:
            bl = BaselineService.get_monthly_arrays(project_id)
            if bl and bl.get('labels'):
                if not facturacion_mensual:
                    # Convertir serie acumulada de billing a mensual (delta)
                    billing_acc = bl.get('billing', [])
                    facturacion_mensual = []
                    for i, label in enumerate(bl.get('labels', [])):
                        prev = float(billing_acc[i-1]) if i > 0 else 0.0
                        delta = float(billing_acc[i]) - prev
                        facturacion_mensual.append({'mes': label, 'total': delta})
                if total_facturado_cliente == 0.0:
                    total_facturado_cliente = float(bl['billing'][-1]) if bl.get('billing') else 0.0
        except Exception:
            pass
        
        # Duración real
        duracion_real = ExecutiveReporter.calculate_duracion_real(project)
        
        return {
            'proyecto': project.cod_projects_id,
            'centro_costo': project.cost_center,
            'contract_amount': float(contract_amount),  # ✅ Venta al cliente
            'bac_presupuestado': float(bac_presupuestado),  # ✅ Presupuesto de costos
            'total_gastado': float(total_gastado),  # ✅ Costo total (AC) real o baseline
            'porcentaje_ejecutado': porcentaje_ejecutado,
            'duracion_planeada': project.estimated_duration,
            'duracion_real': duracion_real,
            'estado': project.state_projects,
            'desviacion': float(bac_presupuestado - total_gastado),
            'monto_faltante': float(bac_presupuestado - total_gastado),
            'facturado_cliente_total': float(total_facturado_cliente),
            'facturacion_mensual': facturacion_mensual,
        }
    @staticmethod
    def calculate_duracion_real(project):
        """Calcula duración REAL basada en fechas de OCs y facturas"""
        ocs = PurchaseOrder.objects.filter(project_code=project)
        invoices = Invoice.objects.filter(purchase_order__project_code=project)
        
        # Recolectar TODAS las fechas relevantes
        todas_fechas = []
        
        # Fechas de OCs
        for oc in ocs:
            if oc.issue_date:
                todas_fechas.append(oc.issue_date)
            if oc.initial_delivery_date:
                todas_fechas.append(oc.initial_delivery_date)
            if oc.final_delivery_date:
                todas_fechas.append(oc.final_delivery_date)
        
        # Fechas de facturas
        for inv in invoices:
            if inv.issue_date:
                todas_fechas.append(inv.issue_date)
        
        if not todas_fechas:
            return project.estimated_duration  # Fallback
        
        # Calcular rango completo
        fecha_min = min(todas_fechas)
        fecha_max = max(todas_fechas)
        delta_days = (fecha_max - fecha_min).days
        
        # Convertir a meses (mínimo 1 mes)
        return max(1, round(delta_days / 30))