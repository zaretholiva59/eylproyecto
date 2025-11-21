from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal


class Invoice(models.Model):
    """Modelo para GUARDAR facturas recibidas (solo registro)"""
    
    INVOICE_TYPES = [
        ('invoice', 'Factura'),
        ('receipt', 'Boleta'),
        ('ticket', 'Ticket'),
    ]
    
    CURRENCY_CHOICES = [
        ('PEN', 'Soles'),
        ('USD', 'Dólares'),
        ('EUR', 'Euros'),
    ]

    # 🔥 DATOS BÁSICOS DE LA FACTURA
    invoice_number = models.CharField(max_length=50, unique=True, verbose_name="Número de Factura")
    issue_date = models.DateField(default=timezone.now, verbose_name="Fecha de Emisión")
    invoice_type = models.CharField(max_length=20, choices=INVOICE_TYPES, default='invoice', verbose_name="Tipo de Comprobante")
    
    # ✅ RELACIÓN UNO-A-UNO CON ORDEN DE COMPRA (Factura Proveedor por OC)
    purchase_order = models.OneToOneField(
        'projects.PurchaseOrder',
        to_field='po_number',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='invoice',
        verbose_name="Orden de Compra relacionada"
    )
        
    # 🔗 DATOS DEL PROVEEDOR
    supplier_ruc = models.CharField(max_length=20, verbose_name="RUC Proveedor")
    supplier_name = models.CharField(max_length=255, verbose_name="Nombre Proveedor")
    supplier_address = models.CharField(max_length=500, blank=True, verbose_name="Dirección Proveedor")
    
    # 💰 TOTALES (según viene en la factura)
    subtotal = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0.00)],
        verbose_name="Subtotal"
    )
    tax_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00,
        verbose_name="IGV/Impuestos"
    )
    total_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00,
        verbose_name="Total Factura"
    )
    
    # 🌍 MONEDA
    currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES, default='PEN', verbose_name="Moneda")
    exchange_rate = models.DecimalField(
        max_digits=8, 
        decimal_places=4, 
        default=1.0000,
        verbose_name="Tipo de Cambio"
    )
    
    # 📝 INFORMACIÓN ADICIONAL
    observations = models.TextField(blank=True, verbose_name="Observaciones")
    
    # 📎 ARCHIVOS (para guardar PDF/XML de la factura)
    pdf_file = models.FileField(upload_to='invoices/pdf/', null=True, blank=True, verbose_name="PDF Factura")
    xml_file = models.FileField(upload_to='invoices/xml/', null=True, blank=True, verbose_name="XML Factura")
    
    # ⏰ METADATA
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "invoice"
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"
        ordering = ['-issue_date', 'invoice_number']

    def __str__(self):
        return f"{self.invoice_number} - {self.supplier_name} - S/ {self.total_amount}"

    def save(self, *args, **kwargs):
        """Solo guarda los datos, NO genera cálculos automáticos"""
        super().save(*args, **kwargs)


class InvoiceDetail(models.Model):
    """Modelo para GUARDAR los productos/detalles de cada factura"""
    
    # 🔗 RELACIÓN CON FACTURA
    invoice = models.ForeignKey(
        Invoice, 
        on_delete=models.CASCADE,
        related_name='invoice_details'
    )
    
    # 🔗 RELACIÓN CON PRODUCTO (TU TABLA PRODUCT)
    product = models.ForeignKey(
        'Product',  # ✅ Relación a tu modelo Product
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Producto del Catálogo"
    )
    
    # 📦 DESCRIPCIÓN DEL PRODUCTO (según viene en la factura)
    product_description = models.CharField(max_length=255, verbose_name="Descripción en Factura")
    product_code = models.CharField(max_length=100, blank=True, verbose_name="Código en Factura")
    product_brand = models.CharField(max_length=100, blank=True, verbose_name="Marca en Factura")
    product_model = models.CharField(max_length=100, blank=True, verbose_name="Modelo en Factura")
    
    # 🔢 CANTIDADES Y PRECIOS (según factura)
    quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0.01)],
        verbose_name="Cantidad"
    )
    unit_price = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        validators=[MinValueValidator(0.00)],
        verbose_name="Precio Unitario en Factura"
    )
    
    # 💰 SUBTOTAL (según factura)
    subtotal = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00,
        verbose_name="Subtotal en Factura"
    )

    class Meta:
        db_table = "invoice_detail"
        verbose_name = "Detalle de Factura"
        verbose_name_plural = "Detalles de Factura"

    def save(self, *args, **kwargs):
        """Auto-completar desde el catálogo si hay producto relacionado"""
        if self.product and not self.product_description:
            # ✅ AUTO-COMPLETAR DESDE TU CATÁLOGO PRODUCT
            self.product_description = self.product.descrip
            self.product_code = self.product.code_art
            self.product_brand = self.product.manufac
            self.product_model = self.product.model
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product_description} - {self.quantity} x S/ {self.unit_price}"

    @property
    def cost_vs_price(self):
        """Calcular diferencia entre costo en catálogo y precio en factura"""
        if self.product:
            return self.unit_price - self.product.cost
        return None