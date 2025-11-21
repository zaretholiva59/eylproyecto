from django.db import models
from decimal import Decimal
from .oc import PurchaseOrder
from projects.models.product import Product
from projects.models.podetail_supplier import PODetailSupplier

class PODetailProduct(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, to_field='po_number', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    
    product_name = models.CharField(max_length=255, blank=True)
    comment = models.CharField(max_length=255, blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    igv = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    quantity = models.PositiveIntegerField()
    measurement_unit = models.CharField(
        max_length=20,
        choices=[
            ('unidades', 'Unidades'),
            ('m²', 'Metros Cuadrados'),
            ('m', 'Metros Lineales'), 
            ('kg', 'Kilogramos'),
            ('lt', 'Litros'),
            ('gl', 'Galones'),
            ('caja', 'Cajas'),
            ('juego', 'Juegos'),
        ],
        default='unidades'
    )
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    local_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        # Cálculo canónico: subtotal, igv, total y local_total
        self.subtotal = Decimal(self.quantity) * self.unit_price

        # IGV aplica solo si la OC es LOCAL
        igv_rate = Decimal("0.18")
        is_local = False
        if getattr(self, 'purchase_order', None) and getattr(self.purchase_order, 'local_import', None):
            is_local = (self.purchase_order.local_import == 'LOCAL')

        self.igv = (self.subtotal * igv_rate) if is_local else Decimal("0.00")
        self.total = (self.subtotal + self.igv).quantize(Decimal('0.01'))

        # Conversión a moneda local usando tipo de cambio de la OC
        if getattr(self, 'purchase_order', None) and getattr(self.purchase_order, 'exchange_rate', None):
            try:
                rate = Decimal(self.purchase_order.exchange_rate)
            except Exception:
                rate = Decimal('1')
        else:
            rate = Decimal('1')

        # Si la OC es en USD, exchange_rate debe convertir a S/.
        self.local_total = (self.total * rate).quantize(Decimal('0.01'))

        # Completar nombre de producto si falta
        if not self.product_name and self.product:
            self.product_name = self.product.descrip

        super().save(*args, **kwargs)

        # Actualizar automáticamente el total de la orden padre en moneda local
        if self.purchase_order:
            self.purchase_order.update_totals()

        # Sin signals: recalcular supplier_amount del proveedor afectado
        try:
            supplier = getattr(self.product, 'ruc_supplier', None)
            if self.purchase_order and supplier:
                for sp in PODetailSupplier.objects.filter(
                    purchase_order=self.purchase_order,
                    supplier=supplier
                ):
                    # Recalcular y persistir el monto del proveedor
                    sp.calculate_supplier_amount()
                    sp.save(update_fields=['supplier_amount'])
        except Exception:
            # Evitar que errores en el recálculo rompan el guardado del detalle
            pass

    def __str__(self):
        return f"{self.product} x {self.quantity}"

    class Meta:
        db_table = "po_detail_product"