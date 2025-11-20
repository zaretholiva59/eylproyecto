from django.db import models
from django.core.validators import MinValueValidator

class EarnedValue(models.Model):
    """Modelo para análisis de Valor Ganado (Curva S)"""
    
    project = models.OneToOneField(
        'projects.Projects',
        on_delete=models.CASCADE,
        related_name="earned_value"
    )
    
    # Datos de la curva S
    curve_data = models.JSONField(
        default=dict,
        help_text="Datos para el gráfico: {months: [], pv: [], ev: [], ac: []}"
    )
    
    # Métricas de desempeño
    bac = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )  # Budget at Completion
    
    cpi = models.DecimalField(
        max_digits=6, 
        decimal_places=3,
        default=1.0
    )  # Cost Performance Index
    
    spi = models.DecimalField(
        max_digits=6, 
        decimal_places=3, 
        default=1.0
    )  # Schedule Performance Index
    
    cv = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0
    )  # Cost Variance
    
    sv = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0
    )  # Schedule Variance
    
    eac = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0
    )  # Estimate at Completion
    
    etc = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0
    )  # Estimate to Complete
    
    analysis_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "earned_value"
        verbose_name = "Análisis de Valor Ganado"
        verbose_name_plural = "Análisis de Valor Ganado"
    
    def __str__(self):
        return f"Curva S - {self.project.cod_projects_id}"
