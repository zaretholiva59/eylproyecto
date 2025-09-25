from django.db import models
from django.core.validators import MinValueValidator 

from projects.models.costumer import Costumer

class Chance(models.Model):
    cod_projects= models.CharField(max_length=20 , primary_key=True)
    info_costumer=models.ForeignKey(Costumer,on_delete=models.CASCADE)
    staff_presale=models.CharField(max_length=100)
    cost_center=models.CharField(max_length=20)
    com_exe=models.CharField(max_length=100)
    regis_date=models.DateField(auto_now_add=True)
    dres_chance=models.CharField(max_length=255)
    date_aprox_close=models.DateField(null=True , blank=True)
    cost_aprox_chance=models.DecimalField(max_digits=12 , decimal_places=2 , default=0.00, validators=[MinValueValidator(0.00)])
    aprox_uti = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    class Meta:
        db_table ="chance"
    
    def __str__(self):
        return f"Chance {self.cod_projects} - {self.info_costumer.com_name}"
   
   
    # Calcula utilidad
    def save(self ,*args , **kwargs):
        self.aprox_uti=self.cost_aprox_chance - 1000
        super().save(*args, **kwargs)
       


