# projects/services/invoice_management/invoice_manager.py
from django.utils import timezone
from django.db.models import Q, Sum
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class InvoiceManager:
    """
    Servicio para gestión de facturación con verificación dual
    Basado en mejores prácticas de foros financieros
    """
    
    @staticmethod
    def get_invoices_for_assistant(user, project_id=None):
        """Facturas que el asistente puede gestionar"""
        from projects.models import ClientInvoice
        
        queryset = ClientInvoice.objects.filter(
            Q(reported_by=user) | Q(status__in=['BORRADOR', 'EMITIDA'])
        )
        
        if project_id:
            queryset = queryset.filter(project__cod_projects_id=project_id)
            
        return queryset.order_by('-invoice_date')
    
    @staticmethod
    def get_invoices_for_verification(project_id=None):
        """Facturas pendientes de verificación bancaria (para jefe)"""
        from projects.models import ClientInvoice
        
        queryset = ClientInvoice.objects.filter(
            status='PAGO_REPORTADO'
        )
        
        if project_id:
            queryset = queryset.filter(project__cod_projects_id=project_id)
            
        return queryset.order_by('payment_reported_date')
    
    @staticmethod
    def report_payment(invoice_id, user, reported_date=None, client_notes=""):
        """Asistente reporta que cliente dice haber pagado"""
        from projects.models import ClientInvoice
        
        try:
            invoice = ClientInvoice.objects.get(id=invoice_id)
            
            if invoice.status not in ['EMITIDA', 'BORRADOR']:
                return False, "Solo se puede reportar pago en facturas EMITIDAS"
            
            invoice.status = 'PAGO_REPORTADO'
            invoice.payment_reported_date = reported_date or timezone.now().date()
            invoice.reported_by = user
            invoice.client_notes = client_notes
            invoice.save()
            
            logger.info(f"Pago reportado por {user} para factura {invoice.invoice_number}")
            return True, "Pago reportado exitosamente"
            
        except ClientInvoice.DoesNotExist:
            return False, "Factura no encontrada"
    
    @staticmethod
    def verify_payment(invoice_id, user, verified_date=None, bank_reference="", 
                      actual_amount=None, verification_notes="", is_verified=True):
        """Jefe verifica pago real en banco"""
        from projects.models import ClientInvoice
        
        try:
            invoice = ClientInvoice.objects.get(id=invoice_id)
            
            if invoice.status != 'PAGO_REPORTADO':
                return False, "Solo se puede verificar facturas en estado PAGO_REPORTADO"
            
            if is_verified:
                invoice.status = 'PAGO_VERIFICADO'
                invoice.bank_verified_date = verified_date or timezone.now().date()
                invoice.verified_by = user
                invoice.bank_reference = bank_reference
                invoice.verification_notes = verification_notes
                
                if actual_amount is not None:
                    invoice.paid_amount = actual_amount
                else:
                    invoice.paid_amount = invoice.amount
                    
            else:
                invoice.status = 'PAGO_NO_RECIBIDO'
                invoice.verification_notes = f"Pago no recibido: {verification_notes}"
                
            invoice.save()
            
            action = "verificado" if is_verified else "rechazado"
            logger.info(f"Pago {action} por {user} para factura {invoice.invoice_number}")
            return True, f"Pago {action} exitosamente"
            
        except ClientInvoice.DoesNotExist:
            return False, "Factura no encontrada"
    
    @staticmethod
    def confirm_payment(invoice_id, user):
        """Confirmar pago completo (después de verificación)"""
        from projects.models import ClientInvoice
        
        try:
            invoice = ClientInvoice.objects.get(id=invoice_id)
            
            if invoice.status != 'PAGO_VERIFICADO':
                return False, "Solo se puede confirmar facturas en estado PAGO_VERIFICADO"
            
            invoice.status = 'PAGADA'
            invoice.fully_paid_date = timezone.now().date()
            invoice.save()
            
            logger.info(f"Pago confirmado por {user} para factura {invoice.invoice_number}")
            return True, "Pago confirmado exitosamente"
            
        except ClientInvoice.DoesNotExist:
            return False, "Factura no encontrada"
    
    @staticmethod
    def get_financial_metrics(project_id):
        """Métricas financieras reales basadas en estados verificados"""
        from projects.models import ClientInvoice
        
        invoices = ClientInvoice.objects.filter(project__cod_projects_id=project_id)
        
        metrics = {
            'total_invoiced': invoices.aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
            'total_paid_real': invoices.filter(status='PAGADA').aggregate(total=Sum('paid_amount'))['total'] or Decimal('0.00'),
            'pending_verification': invoices.filter(status='PAGO_REPORTADO').aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
            'verified_not_confirmed': invoices.filter(status='PAGO_VERIFICADO').aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
            'problem_invoices': invoices.filter(status__in=['PAGO_NO_RECIBIDO', 'CONTROVERSIA']).aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
            'overdue_invoices': invoices.filter(status='VENCIDA').aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
        }
        
        # Calcular eficiencia de cobranza
        if metrics['total_invoiced'] > 0:
            metrics['collection_efficiency'] = (metrics['total_paid_real'] / metrics['total_invoiced']) * 100
        else:
            metrics['collection_efficiency'] = Decimal('0.00')
        
        return metrics
    
    @staticmethod
    def check_overdue_invoices():
        """Verificar facturas vencidas automáticamente"""
        from projects.models import ClientInvoice
        
        overdue = ClientInvoice.objects.filter(
            due_date__lt=timezone.now().date(),
            status__in=['EMITIDA', 'PAGO_REPORTADO']
        )
        
        updated = overdue.update(status='VENCIDA')
        logger.info(f"Actualizadas {updated} facturas a estado VENCIDA")
        
        return updated
