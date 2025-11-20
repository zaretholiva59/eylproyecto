from django.db import models
from .projects import Projects
from .project_baseline import ProjectBaseline

class ProjectMonthlyBaseline(models.Model):
    """Datos mensuales planeados para abastecer gráficas (PV/EV/AC/Facturación/Avance)."""
    project = models.ForeignKey(
        Projects,
        on_delete=models.CASCADE,
        related_name='monthly_baseline'
    )
    baseline = models.ForeignKey(
        ProjectBaseline,
        on_delete=models.CASCADE,
        related_name='months'
    )
    month_index = models.PositiveIntegerField(verbose_name='Mes (1..n)')

    # Montos acumulados planeados
    pv_planned = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name='PV planeado (S/)')
    ev_planned = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name='EV planeado (S/)')
    ac_planned = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name='AC planeado (S/)')
    client_billing_planned = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name='Facturación cliente planeada (S/)')

    # Porcentaje de avance plan (0..100)
    progress_planned = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name='% Avance plan')

    label = models.CharField(max_length=30, blank=True, verbose_name='Etiqueta de mes (Enero 2025, etc.)')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'project_monthly_baseline'
        unique_together = [('project', 'month_index')]
        ordering = ['project_id', 'month_index']
        verbose_name = 'Baseline Mensual de Proyecto'
        verbose_name_plural = 'Baselines Mensuales de Proyecto'

    def __str__(self):
        return f"{self.project.cod_projects_id} - Mes {self.month_index}"