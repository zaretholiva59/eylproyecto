from django.db import models
from .projects import Projects

class ProjectProgress(models.Model):
    """Modelo para seguimiento mensual de avance del proyecto"""
    project = models.ForeignKey(
        Projects, 
        on_delete=models.CASCADE,
        related_name="progress_records"
    )
    month_number = models.IntegerField(
        verbose_name="Número de mes",
        help_text="Mes 1, 2, 3..."
    )
    planned_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        verbose_name="% Avance Programado",
        help_text="Porcentaje programado para este mes"
    )
    actual_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2, 
        verbose_name="% Avance Real",
        help_text="Porcentaje real completado"
    )
    record_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "project_progress"
        unique_together = ['project', 'month_number']
        verbose_name = "Avance de Proyecto"
        verbose_name_plural = "Avances de Proyectos"
    
    def __str__(self):
        return f"{self.project.cod_projects_id} - Mes {self.month_number}"