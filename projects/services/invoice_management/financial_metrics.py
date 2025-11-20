# projects/services/invoice_management/financial_metrics.py
from django.db.models import Sum
from decimal import Decimal

class FinancialMetricsCalculator:
    """
    Servicio para cálculo de métricas financieras reales
    Con manejo seguro de campos faltantes
    """
    
    @staticmethod
    def calculate_project_financials(project_id):
        """Métricas financieras integradas PMI + Finanzas - VERSIÓN SEGURA"""
        try:
            from projects.models import ClientInvoice, Projects
            
            project = Projects.objects.get(cod_projects_id=project_id)
            invoices = ClientInvoice.objects.filter(project=project)
            
            # Métricas de facturación real (con manejo de campos faltantes)
            invoicing_metrics = FinancialMetricsCalculator._calculate_invoicing_metrics_safe(invoices)
            
            # Métricas de costos reales  
            cost_metrics = FinancialMetricsCalculator._calculate_cost_metrics(project)
            
            # Métricas integradas
            integrated_metrics = FinancialMetricsCalculator._calculate_integrated_metrics(
                invoicing_metrics, cost_metrics, project
            )
            
            return {
                **invoicing_metrics,
                **cost_metrics, 
                **integrated_metrics
            }
        except Exception as e:
            print(f"⚠️ Error calculando métricas: {e}")
            return FinancialMetricsCalculator._get_metrics_fallback()
    
    @staticmethod
    def _calculate_invoicing_metrics_safe(invoices):
        """Cálculo SEGURO de métricas de facturación"""
        try:
            # Usar amount como fallback si paid_amount no existe
            total_invoiced = invoices.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            # Para paid_amount, verificar si existe la columna
            try:
                total_paid = invoices.filter(status='PAGADA').aggregate(total=Sum('paid_amount'))['total'] or Decimal('0.00')
            except:
                # Si paid_amount no existe, usar amount para facturas pagadas
                total_paid = invoices.filter(status='PAGADA').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            # Contar facturas por estado
            paid_count = invoices.filter(status='PAGADA').count()
            pending_count = invoices.filter(status='PAGO_REPORTADO').count()
            problem_count = invoices.filter(status__in=['PAGO_NO_RECIBIDO', 'CONTROVERSIA']).count()
            
            # Eficiencia de cobranza
            collection_efficiency = (total_paid / total_invoiced * 100) if total_invoiced > 0 else Decimal('0.00')
            
            return {
                'total_invoiced': total_invoiced,
                'total_paid_real': total_paid,
                'collection_efficiency': collection_efficiency,
                'paid_invoices_count': paid_count,
                'pending_invoices_count': pending_count,
                'problem_invoices_count': problem_count,
                'database_ready': True,
            }
        except Exception as e:
            print(f"⚠️ Error en métricas de facturación: {e}")
            return FinancialMetricsCalculator._get_invoicing_fallback()
    
    @staticmethod
    def _calculate_cost_metrics(project):
        """Cálculo de métricas de costos reales"""
        try:
            from projects.models import PurchaseOrder
            
            ocs = PurchaseOrder.objects.filter(project_code=project)
            total_spent = ocs.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            
            # Obtener BAC (Budget at Completion) desde Chance
            try:
                chance = project.cod_projects
                bac = Decimal(str(getattr(chance, 'total_costs', 0) or getattr(chance, 'cost_aprox_chance', 0) or 0))
            except Exception:
                bac = Decimal('0.00')
            
            return {
                'total_spent': total_spent,
                'bac': bac,
                'cost_variance': total_spent - bac if bac > 0 else Decimal('0.00'),
            }
        except Exception as e:
            print(f"⚠️ Error en métricas de costos: {e}")
            return {'total_spent': Decimal('0.00'), 'bac': Decimal('0.00'), 'cost_variance': Decimal('0.00')}
    
    @staticmethod
    def _calculate_integrated_metrics(invoicing_metrics, cost_metrics, project):
        """Métricas integradas PMI + Finanzas"""
        try:
            # Margen real vs proyectado
            try:
                # Monto contractual desde Chance.cost_aprox_chance
                contract_amount = Decimal(str(getattr(project.cod_projects, 'cost_aprox_chance', 0) or 0))
            except Exception:
                contract_amount = Decimal('0.00')
            
            current_margin = invoicing_metrics['total_paid_real'] - cost_metrics['total_spent']
            projected_margin = contract_amount - cost_metrics['bac'] if contract_amount > 0 else Decimal('0.00')
            
            # Determinar estado del sistema
            system_status = '✅ Operativo'
            if current_margin < 0:
                system_status = '⚠️ Margen negativo'
            elif invoicing_metrics['collection_efficiency'] < 50:
                system_status = '🟡 Cobranza baja'
            
            return {
                'contract_amount': contract_amount,
                'current_margin': current_margin,
                'projected_margin': projected_margin,
                'margin_health': '✅ Saludable' if current_margin >= 0 else '⚠️ En riesgo',
                'system_status': system_status
            }
        except Exception as e:
            print(f"⚠️ Error en métricas integradas: {e}")
            return {
                'contract_amount': Decimal('0.00'),
                'current_margin': Decimal('0.00'),
                'projected_margin': Decimal('0.00'),
                'margin_health': '🔴 Error',
                'system_status': '🔴 Error de configuración'
            }
    
    @staticmethod
    def _get_metrics_fallback():
        """Métricas de fallback cuando hay errores"""
        return {
            'total_invoiced': Decimal('0.00'),
            'total_paid_real': Decimal('0.00'),
            'collection_efficiency': Decimal('0.00'),
            'total_spent': Decimal('0.00'),
            'bac': Decimal('0.00'),
            'contract_amount': Decimal('0.00'),
            'current_margin': Decimal('0.00'),
            'projected_margin': Decimal('0.00'),
            'system_status': '🔴 Requiere migración de base de datos',
            'margin_health': '🔴 Error',
            'paid_invoices_count': 0,
            'pending_invoices_count': 0,
            'problem_invoices_count': 0,
        }
    
    @staticmethod
    def _get_invoicing_fallback():
        """Fallback para métricas de facturación"""
        return {
            'total_invoiced': Decimal('0.00'),
            'total_paid_real': Decimal('0.00'),
            'collection_efficiency': Decimal('0.00'),
            'paid_invoices_count': 0,
            'pending_invoices_count': 0,
            'problem_invoices_count': 0,
            'database_ready': False,
        }
