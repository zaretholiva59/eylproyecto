from django.db import models
from django.utils import timezone
from .projects import Projects

class ProjectBaseline(models.Model):
    """Resumen de baseline del proyecto (versión, fechas y BAC planeado)."""
    project = models.OneToOneField(
        Projects,
        on_delete=models.CASCADE,
        related_name='baseline'
    )
    version_name = models.CharField(max_length=60, default='Inicial', verbose_name='Versión Baseline')
    start_date = models.DateField(null=True, blank=True, verbose_name='Fecha inicio baseline')
    duration_months = models.PositiveIntegerField(default=1, verbose_name='Duración (meses)')
    bac_planned = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name='BAC planeado')
    contract_planned = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name='Venta planeada')
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'project_baseline'
        verbose_name = 'Baseline de Proyecto'
        verbose_name_plural = 'Baselines de Proyectos'

    def __str__(self):
        return f"{self.project.cod_projects_id} - {self.version_name}"

    def ensure_defaults(self):
        """Rellena campos con valores del proyecto si faltan."""
        if not self.start_date:
            self.start_date = self.project.start_date or timezone.now().date()
        # Si duración no está definida o es menor a 2, usar estimada o 12 por defecto
        if not self.duration_months or self.duration_months < 2:
            self.duration_months = max(1, int(self.project.estimated_duration or 12))
        if not self.bac_planned:
            try:
                # Usar costos totales calculados de Chance; fallback a monto aproximado
                chance = self.project.cod_projects
                self.bac_planned = getattr(chance, 'total_costs', 0) or getattr(chance, 'cost_aprox_chance', 0) or 0
            except Exception:
                self.bac_planned = 0
        if not self.contract_planned:
            try:
                # Venta planeada desde Chance.cost_aprox_chance
                self.contract_planned = getattr(self.project.cod_projects, 'cost_aprox_chance', 0) or 0
            except Exception:
                self.contract_planned = 0
        return self