from django.db import models
from .choices import oc_state

class PurchaseOrder(models.Model):
    po_number = models.CharField(primary_key=True, max_length=30)  # ← PO_NUMBER COMO PK
    project_code = models.ForeignKey('projects.Projects', on_delete=models.CASCADE)
    issue_date = models.DateField(null=True, blank=True)
    initial_delivery_date = models.DateField(null=True, blank=True)
    final_delivery_date = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10)
    exchange_rate = models.DecimalField(
        max_digits=8, 
        decimal_places=4, 
        default=1.0000,
        verbose_name="Tipo de Cambio"
    )
    po_status = models.CharField(
        max_length=50,
        choices=oc_state,
        default='PENDIENTE'
    )
    observations = models.TextField(blank=True)
    guide_number = models.CharField(max_length=50, blank=True)
    guide_date = models.DateField(null=True, blank=True)

    # CAMPOS NUEVOS DEL EXCEL
    local_import = models.CharField(
        max_length=10, 
        choices=[('LOCAL', 'Local'), ('IMPORT', 'Importado')],
        default='LOCAL',
        verbose_name="Local/Import"
    )
    te = models.IntegerField(
        verbose_name="Tiempo de Entrega (días)", 
        null=True, 
        blank=True
    )
    forma_pago = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="Forma de Pago"
    )
    pagar_a = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="Pagar A"
    )

    class Meta:
        db_table = "purchase_order"
        # Ya no necesitas unique_together porque po_number es PK
    
    def __str__(self):
        return f"PO {self.po_number} - Project {self.project_code}"
    
    def update_totals(self):
        details = self.podetailproduct_set.all()
        # Unificar: total_amount representa el total en moneda local
        self.total_amount = sum([d.local_total for d in details])
        self.save()