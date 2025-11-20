from django.db import models
from projects.models.role import Respon
from .choices import projects_states

class Projects(models.Model):
    cod_projects = models.OneToOneField(
        'projects.Chance', on_delete=models.CASCADE, primary_key=True
    )
    respon_projects = models.ForeignKey(Respon, on_delete=models.SET_NULL, null=True)
    state_projects = models.CharField(max_length=30 , choices = projects_states )
    cost_center = models.CharField(max_length=20, default="SIN-CENTRO")
    start_date = models.DateField(null=True, blank=True)
    estimated_end_date= models.DateField(null=True, blank=True) 
    estimated_duration = models.PositiveIntegerField(default=8)
    
    # ✅ NUEVO CAMPO PMI: % Avance Físico Real
    physical_percent_complete = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        default=0.00,
        verbose_name="% Avance Físico (PMI)",
        help_text="Porcentaje real de avance físico según PMI"
    )
    
    # ✅ NUEVO: Fecha última actualización avance
    last_progress_update = models.DateField(
        null=True, blank=True,
        verbose_name="Última actualización avance"
    )


    class Meta:
        db_table = "projects"

    def __str__(self):
        return f"projects {self.cod_projects} ({self.state_projects})"
 