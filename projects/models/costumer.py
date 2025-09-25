from django.db import models
from .choices import customer_types


class Costumer(models.Model):
    ruc_costumer = models.CharField(max_length=20, primary_key=True)
    com_name = models.CharField(max_length=255, )
    type_costumer = models.CharField(max_length=20,choices=customer_types,default="Individual" )
    contac_costumer = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table="costumer"

    def __str__(self):
        return f"{self.com_name}({self.ruc_costumer})"
    






