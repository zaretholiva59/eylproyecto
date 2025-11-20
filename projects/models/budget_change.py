from django.db import models
from .projects import Projects
from .choices import approval_stats


class BudgetChange(models.Model):
    """Cambios aprobados al presupuesto (re-baseline / órdenes de cambio).

    Suma de montos aprobados se aplica sobre el BAC Planeado (baseline) para
    obtener el BAC Real vigente.
    """

    project = models.ForeignKey(Projects, on_delete=models.CASCADE, related_name="budget_changes")
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Monto del cambio (+ incremento, - reducción)")
    status = models.CharField(max_length=20, choices=approval_stats, default="Aprobado")
    reason = models.CharField(max_length=255, blank=True)
    change_date = models.DateField(null=True, blank=True)
    reference = models.CharField(max_length=64, blank=True, help_text="Referencia de orden de cambio/contrato")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "budget_change"
        verbose_name = "Cambio de Presupuesto"
        verbose_name_plural = "Cambios de Presupuesto"

    def __str__(self):
        sign = "+" if self.amount and self.amount >= 0 else "-"
        return f"{self.project.cod_projects_id} • {sign}{abs(self.amount)} ({self.status})"