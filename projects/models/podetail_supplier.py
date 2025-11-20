from django.db import models
from django.db.models import Sum
from decimal import Decimal
from .oc import PurchaseOrder
from projects.models.supplier import Supplier

class PODetailSupplier(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, to_field='id', on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    
    # 🔥 CAMPO NUEVO QUE FALTABA
    supplier_name = models.CharField(max_length=255, blank=True)  # Para autocomplete
    
    # 🔥 CAMPOS EXISTENTES - MODIFICADOS
    supplier_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    delivery_date = models.DateField(null=True, blank=True)  # ✅ Ahora permite vacío
    supplier_status = models.CharField(max_length=30)

    # ✅ CAMPO NUEVO DEL EXCEL
    status_factura_contabilidad = models.CharField(
        max_length=50, 
        blank=True, 
        verbose_name="Status Factura Contabilidad"
    )

    def save(self, *args, **kwargs):
        # ✅ CORREGIDO: usa name_supplier en lugar de name
        if not self.supplier_name and self.supplier:
            self.supplier_name = self.supplier.name_supplier
        
        # ✅ NUEVO: CALCULAR supplier_amount AUTOMÁTICAMENTE
        self.calculate_supplier_amount()
        
        super().save(*args, **kwargs)
    
    def calculate_supplier_amount(self):
        """Calcula el monto total facturado por el proveedor sumando los productos"""
        from projects.models.podetail_product import PODetailProduct
        
        if self.purchase_order and self.supplier:
            # Sumar todos los local_total de productos del mismo proveedor en esta OC
            total = PODetailProduct.objects.filter(
                purchase_order=self.purchase_order,
                product__ruc_supplier=self.supplier
            ).aggregate(
                total_amount=Sum('local_total')
            )['total_amount'] or Decimal('0.00')
            
            self.supplier_amount = total

    def __str__(self):
        return f"{self.supplier} ({self.supplier_status})"

    class Meta:
        db_table = "po_detail_supplier"