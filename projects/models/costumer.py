from django.db import models

class Costumer(models.Model):
    ruc_costumer = models.CharFiels(max_length=20, primary_hey=True)
    com_name = models.CharFiels(max_length=255, )
    type_costumer = models.CharFiels(max_length=20, )
    contac_costumer = models.CharFiels(max_length=100, black=True)

    class Meta:
        db_table="costumer"

    def __str__(self):
        return f"{self.com_name}({self.ruc_costumer})"
    






