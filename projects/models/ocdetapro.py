from django.db import models
from decimal import Decimal
from projects.models.oc import PurchaseOrder 
from projects.models.product import Product

class PODetailProduct(models.Model):
    po_number = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE)
    product_code = models.ForeignKey(Product, on_delete=models.CASCADE)
    units = models.PositiveIntegerField()
    unit_amount = models.DecimalField(max_digits=12, decimal_places=2)
    comment = models.CharField(max_length=255, blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.subtotal = self.units * self.unit_amount
        self.tax = self.subtotal * Decimal("0.18")
        self.total = self.subtotal + self.tax
        super().save(*args, **kwargs)

    class Meta:
        db_table = "po_detail_product"
        unique_together = ("po_number", "product_code")
    
    def __str__(self):
        return f"{self.po_number} - {self.product_code}"


