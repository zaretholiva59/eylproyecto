from django.db import models

class Hoursrecord(models.Model):
    pro=models.ForeignKey('projects.Projects', on_delete=models.CASCADE, related_name="horas")
    respon=models.CharField(max_length=100)
    date= models.DateField()
    hours = models.DecimalField(max_digits=6, decimal_places=2)
    acti=models.CharField(max_length=200 , blank=True, null=True)
