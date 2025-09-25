from django.db import models

class Supplier(models.Model):
    ruc_supplier= models.CharField(max_length=20, primary_key=True)
    name_supplier= models.CharField(max_length=255)

    class Meta:
        db_table = "supplier"

    def __str__(self):
        return f"{self.ruc_supplier} - {self.name_supplier}"
