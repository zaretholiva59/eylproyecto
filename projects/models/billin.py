from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone

class Billing(models.Model):
    """Modelo para registro de pagos y estados de factura"""
    
    PAYMENT_STATUS = [
        ('pending', 'Pendiente'),
        ('partial', 'Pago Parcial'),
        ('paid', 'Pagado'),
        ('overdue', 'Vencido'),
        ('cancelled', 'Cancelado'),
    ]

    # 🔗 RELACIÓN CON FACTURA
    invoice = models.OneToOneField(
        'invoice.Invoice',
        on_delete=models.CASCADE,
        related_name='billing_info'
    )
    
    # 💰 INFORMACIÓN DE PAGO
    payment_status = models.CharField(
        max_length=20, 
        choices=PAYMENT_STATUS, 
        default='pending',
        verbose_name="Estado de Pago"
    )
    paid_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00,
        verbose_name="Monto Pagado"
    )
    payment_date = models.DateField(null=True, blank=True, verbose_name="Fecha de Pago")
    due_date = models.DateField(verbose_name="Fecha Vencimiento")
    
    # 🏦 DATOS BANCARIOS (opcional)
    payment_method = models.CharField(max_length=50, blank=True, verbose_name="Método de Pago")
    bank_name = models.CharField(max_length=100, blank=True, verbose_name="Banco")
    transaction_number = models.CharField(max_length=100, blank=True, verbose_name="Número Transacción")
    
    # 📝 SEGUIMIENTO
    observations = models.TextField(blank=True, verbose_name="Observaciones de Pago")
    
    # ⏰ METADATA
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "billing"
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ['-due_date']

    def __str__(self):
        return f"Pago - {self.invoice.invoice_number} - {self.get_payment_status_display()}"

    @property
    def pending_amount(self):
        return self.invoice.total_amount - self.paid_amount

    @property
    def is_overdue(self):
        return self.due_date < timezone.now().date() and self.payment_status != 'paid'