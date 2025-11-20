from projects.models import Projects, PurchaseOrder, Invoice
from datetime import datetime
from collections import defaultdict
from projects.services.baseline_service import BaselineService

class EfficiencyReporter:
    """Servicio para calcular eficiencia mensual del proyecto"""
    
    @staticmethod
    def get_monthly_efficiency(project_id):
        """Calcula eficiencia mensual basada en facturacion vs costos"""
        project = Projects.objects.get(cod_projects_id=project_id)
        invoices = Invoice.objects.filter(purchase_order__project_code=project).order_by('issue_date')
        
        # Agrupar por mes
        monthly_data = defaultdict(lambda: {'facturas': 0, 'costos': 0})
        
        for invoice in invoices:
            if invoice.issue_date:
                mes_key = invoice.issue_date.strftime('%Y-%m')
                monthly_data[mes_key]['facturas'] += float(invoice.total_amount or 0)
                if invoice.purchase_order:
                    monthly_data[mes_key]['costos'] += float(invoice.purchase_order.total_amount or 0)
        
        # Calcular eficiencia por mes
        meses = []
        eficiencias = []
        
        for mes in sorted(monthly_data.keys()):
            data = monthly_data[mes]
            if data['costos'] > 0:
                eficiencia = (data['facturas'] / data['costos']) * 100
            else:
                eficiencia = 100
            
            meses.append(mes)
            eficiencias.append(round(eficiencia, 1))
        
        # Fallback: usar baseline si no hay datos
        if not meses:
            try:
                bl = BaselineService.get_monthly_arrays(project_id)
                if bl and bl.get('labels'):
                    # Convertir acumulados a mensuales (delta)
                    ac_acc = bl.get('ac', [])
                    bill_acc = bl.get('billing', [])
                    for i, label in enumerate(bl['labels']):
                        prev_ac = float(ac_acc[i-1]) if i > 0 else 0.0
                        prev_bill = float(bill_acc[i-1]) if i > 0 else 0.0
                        ac_delta = float(ac_acc[i]) - prev_ac
                        bill_delta = float(bill_acc[i]) - prev_bill
                        eff = (bill_delta / ac_delta) * 100 if ac_delta > 0 else 100
                        meses.append(label)
                        eficiencias.append(round(eff, 1))
            except Exception:
                pass
        
        return {
            'meses': meses,
            'eficiencias': eficiencias
        }
