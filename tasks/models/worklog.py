from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from .choices import WORKLOG_STATUS

class WorkLog(models.Model):
    """Registro diario de trabajo de campo - formulario de Juan"""
    
    # === RELACIONES ===
    worker = models.ForeignKey(User,on_delete=models.CASCADE,related_name='work_logs')
    date = models.DateField("Fecha de trabajo",default=timezone.now)
    task = models.ForeignKey('Task',on_delete=models.CASCADE, related_name='work_logs',null=True,blank=True )
    free_activity_name = models.CharField("Actividad libre", max_length=200,blank=True,help_text="Si no es tarea asignada, describir qué se hizo")
    # === UNIDADES TRABAJADAS ===
    units_completed = models.DecimalField("Unidades completadas", max_digits=10,decimal_places=2)
    # === HORAS TRABAJADAS ===
    hours_start = models.TimeField("Hora inicio",help_text="Hora en que empezó a trabajar")
    hours_end = models.TimeField("Hora fin",help_text="Hora en que terminó de trabajar")
    # === COMENTARIOS Y EVIDENCIA ===
    comments = models.TextField("Comentarios", blank=True,help_text="Observaciones del trabajo realizado")
    photos = models.ImageField("Fotos de evidencia",upload_to='work_logs/%Y/%m/',blank=True,null=True,help_text="Fotos del trabajo realizado")
    # === ESTADO DE APROBACIÓN ===
    status = models.CharField("Estado",max_length=20,choices=WORKLOG_STATUS,default='PENDING')
    
    # === AUDITORÍA ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,related_name='created_work_logs')

def __str__(self):
        return f"{self.worker.username} - {self.date} - {self.units_completed}"
    
class Meta:
        db_table = 'work_logs'
        ordering = ['-date', '-created_at']

def save(self, *args, **kwargs):
        # === LÓGICA DE AUTO-APROBACIÓN ===
        if self.task:
            # Si tiene tarea asignada → AUTO-APROBAR
            self.status = 'APPROVED'
        
        # === ACTUALIZAR TASK SI ESTÁ APROBADO ===
        if self.status == 'APPROVED' and self.task:
            # Sumar las unidades completadas a la Task
            self.task.units_completed += self.units_completed
            self.task.save()
        
        # Llamar al save original de Django
        super().save(*args, **kwargs)      