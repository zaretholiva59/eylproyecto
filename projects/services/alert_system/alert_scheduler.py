# projects/services/alert_system/alert_scheduler.py
import logging
from datetime import datetime, timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)

class AlertScheduler:
    """
    Programador simplificado de verificaciones de alertas
    Sin dependencias externas - Usa sistema Django
    """
    
    @staticmethod
    def check_daily_alerts():
        """Verificación diaria manual de alertas"""
        try:
            from .alert_manager import AlertManager
            from projects.models import Projects
            
            active_projects = Projects.objects.filter(state_projects='ACTIVO')
            total_alerts = 0
            
            for project in active_projects:
                try:
                    alerts = AlertManager.get_all_alerts(project.cod_projects_id)
                    
                    if alerts:
                        total_alerts += len(alerts)
                        logger.info(f"Proyecto {project.cod_projects_id}: {len(alerts)} alertas")
                        
                        # Registrar alertas críticas
                        high_alerts = [a for a in alerts if a['level'] == 'HIGH']
                        for alert in high_alerts:
                            logger.warning(f"ALERTA CRÍTICA [{project.cod_projects_id}]: {alert['message']}")
                            
                except Exception as e:
                    logger.error(f"Error verificando {project.cod_projects_id}: {e}")
            
            logger.info(f"Verificación diaria completada: {total_alerts} alertas en {active_projects.count()} proyectos")
            return total_alerts
            
        except Exception as e:
            logger.error(f"Error en verificación diaria: {e}")
            return 0
    
    @staticmethod
    def should_run_daily_check():
        """Determinar si debería ejecutarse la verificación diaria"""
        # Lógica simple: siempre ejecutar por ahora
        # En producción, podrías verificar última ejecución, día de semana, etc.
        return True
    
    @staticmethod  
    def run_scheduled_checks():
        """Ejecutar verificaciones programadas si es necesario"""
        if AlertScheduler.should_run_daily_check():
            return AlertScheduler.check_daily_alerts()
        return 0
