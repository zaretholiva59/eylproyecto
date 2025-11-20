# client.py - CONTENIDO COMPLETO PARA client_invoice.py
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal

# Importar las opciones desde choice.py
from .choices import INVOICE_STATUS, STATUS_MAPPING

class ClientInvoice(models.Model):
    """
    Modelo para facturas de clientes con flujo automático de estados
    """
    
    # Usar INVOICE_STATUS importado desde choice.py
    INVOICE_STATUS = INVOICE_STATUS
    
    # Relación con proyecto
    project = models.ForeignKey(
        'Projects', 
        on_delete=models.CASCADE, 
        related_name='client_invoices',
        verbose_name="Proyecto"
    )
    
    # Información básica de la factura
    invoice_number = models.CharField(
        "Número de Factura", 
        max_length=50,
        help_text="Número único de factura (Ej: F-001, FAC-2024-001)"
    )
    
    invoice_date = models.DateField(
        "Fecha de Emisión",
        help_text="Fecha cuando se emitió la factura al cliente"
    )
    
    amount = models.DecimalField(
        "Monto Facturado", 
        max_digits=12, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        help_text="Monto total de la factura"
    )
    
    description = models.TextField(
        "Descripción", 
        blank=True,
        help_text="Descripción de los servicios/proyectos facturados"
    )
    
    # Estado legacy para compatibilidad
    payment_status = models.CharField(
        "Estado Pago", 
        max_length=20, 
        default='PENDING'
    )
    
    created_at = models.DateTimeField(
        "Fecha Creación", 
        auto_now_add=True
    )
    
    # NUEVO SISTEMA DE ESTADOS - Usando la constante importada
    status = models.CharField(
        "Estado Factura",
        max_length=20,
        choices=INVOICE_STATUS,  # ← Usando la importación
        default='BORRADOR',
        help_text="Estado actual en el flujo de facturación"
    )
    
    # FECHAS CRÍTICAS DEL FLUJO
    due_date = models.DateField(
        "Fecha Vencimiento", 
        null=True, 
        blank=True,
        help_text="Fecha límite para el pago"
    )
    
    payment_reported_date = models.DateField(
        "Fecha Reporte Pago", 
        null=True, 
        blank=True,
        help_text="Fecha cuando el cliente reportó el pago"
    )
    
    bank_verified_date = models.DateField(
        "Fecha Verificación Banco", 
        null=True, 
        blank=True,
        help_text="Fecha cuando se verificó el pago en el banco"
    )
    
    fully_paid_date = models.DateField(
        "Fecha Pago Completo", 
        null=True, 
        blank=True,
        help_text="Fecha cuando se completó el proceso de pago"
    )
    
    # MONTOS REALES VS REPORTADOS
    paid_amount = models.DecimalField(
        "Monto Pagado", 
        max_digits=12, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0)],
        help_text="Monto real que se recibió en la cuenta"
    )
    
    # SISTEMA DE ARCHIVOS ADJUNTOS
    invoice_file = models.FileField(
        "Archivo Factura",
        upload_to='client_invoices/%Y/%m/',
        null=True,
        blank=True,
        help_text="PDF o imagen de la factura emitida"
    )
    
    # REFERENCIAS BANCARIAS
    bank_reference = models.CharField(
        "Referencia Bancaria", 
        max_length=100, 
        blank=True,
        null=True,  # ← AÑADE ESTA LÍNEA
        default='',  # ← AÑADE ESTA LÍNEA
        help_text="Número de referencia del pago bancario"
    )
    
    bank_confirmation_code = models.CharField(
        "Código Confirmación Banco", 
        max_length=50, 
        blank=True,
        help_text="Código de confirmación del banco"
    )
    
    # SEGUIMIENTO Y AUDITORÍA
    reported_by = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        related_name='reported_invoices',
        verbose_name="Reportado por",
        help_text="Usuario que reportó el pago del cliente"
    )
    
    verified_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL, 
        null=True,
        blank=True, 
        related_name='verified_invoices',
        verbose_name="Verificado por",
        help_text="Usuario que verificó el pago en el banco"
    )
    
    # COMENTARIOS Y SEGUIMIENTO
    client_notes = models.TextField(
        "Comentarios del Cliente", 
        blank=True,
        help_text="Comentarios o información proporcionada por el cliente"
    )
    
    internal_notes = models.TextField(
        "Notas Internas", 
        blank=True,
        help_text="Notas internas del equipo"
    )
    
    verification_notes = models.TextField(
        "Notas Verificación", 
        blank=True,
        help_text="Observaciones durante la verificación bancaria"
    )
    
    # ALERTAS Y CONTROL
    is_urgent = models.BooleanField(
        "Urgente", 
        default=False,
        help_text="Marcar si requiere atención inmediata"
    )
    
    reminder_sent = models.BooleanField(
        "Recordatorio Enviado", 
        default=False,
        help_text="Indica si se envió recordatorio de pago"
    )
    
    class Meta:
        verbose_name = "Factura Cliente"
        verbose_name_plural = "Facturas Clientes"
        ordering = ['-invoice_date', 'invoice_number']
        indexes = [
            models.Index(fields=['status', 'due_date']),
            models.Index(fields=['project', 'status']),
        ]
    
    def __str__(self):
        return f"{self.invoice_number} - S/ {self.amount} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        """
        Guardar con automatización de estados
        """
        # ⚡ AUTOMÁTICO: Si se verifica el pago → inmediatamente a PAGADA
        if self.status == 'PAGO_VERIFICADO':
            self.status = 'PAGADA'
            self.fully_paid_date = timezone.now().date()
            if not self.paid_amount:
                self.paid_amount = self.amount
        
        # Sincronizar payment_status legacy usando STATUS_MAPPING importado
        self.payment_status = STATUS_MAPPING.get(self.status, 'PENDING')
        
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        """Verificar si la factura está vencida"""
        if self.due_date and self.status in ['EMITIDA', 'PAGO_REPORTADO']:
            return self.due_date < timezone.now().date()
        return False
    
    @property
    def days_since_reported(self):
        """Días desde que se reportó el pago"""
        if self.payment_reported_date:
            return (timezone.now().date() - self.payment_reported_date).days
        return None
    
    @property
    def is_fully_paid(self):
        """Verificar si la factura está completamente pagada"""
        return self.status == 'PAGADA' and self.paid_amount >= self.amount
    
    def can_report_payment(self):
        """Verificar si se puede reportar pago"""
        return self.status == 'EMITIDA'
    
    def can_verify_payment(self):
        """Verificar si se puede verificar pago"""
        return self.status == 'PAGO_REPORTADO'



