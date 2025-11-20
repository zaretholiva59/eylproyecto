# projects/services/alert_system/alert_manager.py
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class AlertManager:
    """
    Sistema de alertas automáticas para PMI y Facturación
    Basado en estándares de gestión de proyectos
    """
    
    @staticmethod
    def check_pmi_alerts(project_id):
        """Verificar alertas de métricas PMI"""
        from projects.services.earned_value.calculator import EarnedValueCalculator
        from projects.services.earned_value.metrics import ProjectMetrics
        
        alerts = []
        
        try:
            # Obtener métricas PMI
            evm_data = EarnedValueCalculator.calculate_earned_value(project_id)
            metrics = evm_data['metrics']
            physical_progress = evm_data['physical_progress']
            
            # Alertas de costo
            if metrics['cpi'] < 0.9:
                alerts.append({
                    'type': 'COST_ALERT',
                    'level': 'HIGH',
                    'message': f'🚨 ALERTA COSTOS: CPI = {metrics["cpi"]:.3f} (Sobrecosto detectado)',
                    'metric': 'CPI',
                    'value': metrics['cpi'],
                    'threshold': 0.9
                })
            elif metrics['cpi'] < 1.0:
                alerts.append({
                    'type': 'COST_WARNING', 
                    'level': 'MEDIUM',
                    'message': f'⚠️ Atención Costos: CPI = {metrics["cpi"]:.3f} (Cerca del límite)',
                    'metric': 'CPI',
                    'value': metrics['cpi'],
                    'threshold': 1.0
                })
            
            # Alertas de cronograma
            if metrics['spi'] < 0.8:
                alerts.append({
                    'type': 'SCHEDULE_ALERT',
                    'level': 'HIGH', 
                    'message': f'🚨 ALERTA CRONOGRAMA: SPI = {metrics["spi"]:.3f} (Atraso crítico)',
                    'metric': 'SPI',
                    'value': metrics['spi'],
                    'threshold': 0.8
                })
            elif metrics['spi'] < 0.9:
                alerts.append({
                    'type': 'SCHEDULE_WARNING',
                    'level': 'MEDIUM',
                    'message': f'⚠️ Atención Cronograma: SPI = {metrics["spi"]:.3f} (Atraso moderado)',
                    'metric': 'SPI', 
                    'value': metrics['spi'],
                    'threshold': 0.9
                })
            
            # Alertas de avance físico
            if physical_progress < 30:
                alerts.append({
                    'type': 'PROGRESS_ALERT',
                    'level': 'MEDIUM',
                    'message': f'🔄 Avance físico bajo: {physical_progress:.1f}%',
                    'metric': 'PHYSICAL_PROGRESS',
                    'value': physical_progress,
                    'threshold': 30
                })
                
        except Exception as e:
            logger.error(f"Error verificando alertas PMI: {e}")
            alerts.append({
                'type': 'SYSTEM_ERROR',
                'level': 'HIGH',
                'message': f'🔴 Error en sistema de alertas PMI: {str(e)}'
            })
        
        return alerts
    
    @staticmethod
    def check_financial_alerts(project_id):
        """Verificar alertas financieras"""
        from projects.services.invoice_management.financial_metrics import FinancialMetricsCalculator
        
        alerts = []
        
        try:
            metrics = FinancialMetricsCalculator.calculate_project_financials(project_id)
            
            # Alertas de cobranza
            if metrics['collection_efficiency'] < 50:
                alerts.append({
                    'type': 'COLLECTION_ALERT',
                    'level': 'HIGH',
                    'message': f'💰 ALERTA COBRANZA: Eficiencia = {metrics["collection_efficiency"]:.1f}%',
                    'metric': 'COLLECTION_EFFICIENCY',
                    'value': metrics['collection_efficiency'],
                    'threshold': 50
                })
            
            # Alertas de margen
            if metrics['current_margin'] < 0:
                alerts.append({
                    'type': 'MARGIN_ALERT',
                    'level': 'HIGH',
                    'message': f'📉 ALERTA MARGEN: Negativo (S/ {metrics["current_margin"]:,.2f})',
                    'metric': 'CURRENT_MARGIN',
                    'value': metrics['current_margin'],
                    'threshold': 0
                })
            
            # Alertas de facturas pendientes
            if metrics['pending_invoices_count'] > 0:
                alerts.append({
                    'type': 'PENDING_INVOICES',
                    'level': 'MEDIUM',
                    'message': f'📋 Facturas pendientes: {metrics["pending_invoices_count"]}',
                    'metric': 'PENDING_INVOICES_COUNT',
                    'value': metrics['pending_invoices_count'],
                    'threshold': 0
                })
                
        except Exception as e:
            logger.error(f"Error verificando alertas financieras: {e}")
            alerts.append({
                'type': 'SYSTEM_ERROR', 
                'level': 'HIGH',
                'message': f'🔴 Error en sistema de alertas financieras: {str(e)}'
            })
        
        return alerts
    
    @staticmethod
    def check_invoice_alerts(project_id):
        """Verificar alertas de facturación"""
        from projects.models import ClientInvoice
        from django.utils import timezone
        
        alerts = []
        
        try:
            # Facturas vencidas
            overdue_invoices = ClientInvoice.objects.filter(
                project__cod_projects_id=project_id,
                due_date__lt=timezone.now().date(),
                status__in=['EMITIDA', 'PAGO_REPORTADO']
            )
            
            if overdue_invoices.exists():
                alerts.append({
                    'type': 'OVERDUE_INVOICES',
                    'level': 'HIGH',
                    'message': f'⏰ Facturas vencidas: {overdue_invoices.count()}',
                    'count': overdue_invoices.count(),
                    'invoices': list(overdue_invoices.values('invoice_number', 'due_date', 'amount'))
                })
            
            # Facturas en verificación por mucho tiempo
            verification_pending = ClientInvoice.objects.filter(
                project__cod_projects_id=project_id,
                status='PAGO_REPORTADO',
                payment_reported_date__lt=timezone.now().date() - timedelta(days=3)
            )
            
            if verification_pending.exists():
                alerts.append({
                    'type': 'VERIFICATION_DELAY',
                    'level': 'MEDIUM',
                    'message': f'🕒 Verificación pendiente > 3 días: {verification_pending.count()}',
                    'count': verification_pending.count()
                })
                
        except Exception as e:
            logger.error(f"Error verificando alertas de facturación: {e}")
        
        return alerts
    
    @staticmethod
    def get_all_alerts(project_id):
        """Obtener todas las alertas del proyecto"""
        pmi_alerts = AlertManager.check_pmi_alerts(project_id)
        financial_alerts = AlertManager.check_financial_alerts(project_id)
        invoice_alerts = AlertManager.check_invoice_alerts(project_id)
        
        all_alerts = pmi_alerts + financial_alerts + invoice_alerts
        
        # Ordenar por nivel de severidad
        severity_order = {'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        all_alerts.sort(key=lambda x: severity_order.get(x['level'], 4))
        
        return all_alerts
    
    @staticmethod
    def send_alert_notifications(project_id, recipients):
        """Enviar notificaciones de alertas por email"""
        alerts = AlertManager.get_all_alerts(project_id)
        
        if not alerts:
            return
        
        # Filtrar solo alertas HIGH y MEDIUM para notificación
        critical_alerts = [alert for alert in alerts if alert['level'] in ['HIGH', 'MEDIUM']]
        
        if not critical_alerts:
            return
        
        # Construir mensaje de email
        subject = f"🔔 Alertas del Proyecto {project_id}"
        message_lines = [f"Se han detectado {len(critical_alerts)} alertas críticas:\n"]
        
        for alert in critical_alerts:
            message_lines.append(f"• {alert['message']}")
        
        message = "\n".join(message_lines)
        
        # Enviar email (requiere configuración SMTP)
        try:
            if hasattr(settings, 'EMAIL_HOST') and settings.EMAIL_HOST:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    recipients,
                    fail_silently=True
                )
                logger.info(f"Alertas enviadas para proyecto {project_id}")
        except Exception as e:
            logger.error(f"Error enviando alertas por email: {e}")
