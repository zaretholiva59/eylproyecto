from django.db import models
from django.core.validators import MinValueValidator

from projects.models.supplier import Supplier 
 
class Product(models.Model):
    code_art = models.CharField(max_length=50, primary_key=True)
    part_number = models.CharField(max_length=100)
    descrip = models.CharField(max_length=255, blank=True)
    ruc_supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    manufac = models.CharField(max_length=100)
    model = models.CharField(max_length=100, blank=True, verbose_name="Modelo")
    cost = models.DecimalField(
        max_digits=12, decimal_places=2,
        default=0.00, validators=[MinValueValidator(0.00)]
    )

    class Meta:
        db_table = "product"

    def __str__(self):
        return f"{self.part_number} - {self.manufac}"
