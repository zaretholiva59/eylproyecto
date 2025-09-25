from django.utils import timezone
from django.db import models
from django.core.validators import MinValueValidator
from .projects import Projects
class Billing(models.Model):
    projects = models.ForeignKey(
        Projects,
        on_delete=models.CASCADE,
        related_name="billing"
    )

    cost_center=models.CharField(max_length=100, editable=False , null=True , blank=True)
    job_name=models.CharField(max_length=255, editable=False , null=True , blank=True)

    
    cost_material=models.FloatField(default=0, validators=[MinValueValidator(0)])
    cost_h=models.FloatField(default=0, validators=[MinValueValidator(0)])
    outsourced=models.FloatField(default=0, validators=[MinValueValidator(0)])
    overhead_costs=models.FloatField(default=0, validators=[MinValueValidator(0)])

    regis_date=models.DateField(default=timezone.now)
    month=models.CharField(max_length=20, editable=False)
    amount=models.FloatField(default=0,validators=[MinValueValidator(0)],editable=False)

    def save(self,*args,**kwargs):
 # 🔹 Copia automática de datos del proyecto
        if self.projects and self.projects.cod_projects:
            self.cost_center= self.projects.cod_projects.cost_center
            self.job_name=self.projects.cod_projects.des_opport
    
     # 🔹 Convierte la fecha de registro en un formato de mes y año

        if self.regis_date:
            self.month= self.regis_date.strftime("%b %Y")

        self.amount=(
            (self.costo_material or 0) +
            (self.costo_2h or 0) +
            (self.costo_subcontratado or 0) +
            (self.costo_gastos_generales or 0)
        )

        super().save(*args , **kwargs)

    def __str__(self):

        if self.projects and self.projects.cod_projects:
            projects_name = self.projects.cod_proyecto.dres_chance
        else:
            projects_name="Sin proyecto"

        return f"{projects_name} - {self.month}({self.cost})"
            

    










