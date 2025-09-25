from django.db import models
from projects.models.chance import Chance
from projects.models.role import Respon
from .choices import projects_states

class Projects(models.Model):
    cod_projects = models.OneToOneField(
        Chance, on_delete=models.CASCADE, primary_key=True
    )
    respon_projects = models.ForeignKey(Respon, on_delete=models.SET_NULL, null=True)
    state_projects = models.CharField(max_length=30 , choices = projects_states )
    start_date = models.DateField(null=True, blank=True)
    estimated_end_date= models.DateField(null=True, blank=True)

    class Meta:
        db_table = "projects"

    def __str__(self):
        return f"projects {self.cod_projects} ({self.state_projects})"
 