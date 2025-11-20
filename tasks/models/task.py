from django.db import models 
from django.contrib.auth.models import User
from django.utils import timezone
from .choices import TASK_STATUS

class Task(models.Model):
    """Tarea del Kanban - creada por PM"""
    
  # === RELACIONES ===
    project = models.ForeignKey(
        'projects.Projects',
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks'
    )
    
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subtasks',
        help_text="Tarea padre (para crear sub-tareas)"
    )
    # === METADATA ===
    title = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    
    # === UNIDADES DE TRABAJO ===
    units_planned = models.DecimalField(max_digits=10, decimal_places=2)
    units_completed = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # === FECHAS PLANIFICADAS (GANTT) ===
    planned_start = models.DateTimeField(null=True, blank=True)
    planned_end = models.DateTimeField(null=True, blank=True)
    
    # === FECHAS REALES (EJECUCIÓN) ===
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    
    # === ESTADO KANBAN ===
    status = models.CharField(max_length=20, choices=TASK_STATUS, default='BACKLOG')
    
    # === MÉTRICAS PMI ===
    weight = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        help_text="Peso porcentual en el proyecto (0-100)"
    )
    
    # === AUDITORÍA ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,
        null=True, 
        related_name='created_tasks'
    )
    
    def __str__(self):
        return f"{self.title} - {self.project.cod_projects}"  # ← CAMBIO CRÍTICO
    
    def save(self, *args, **kwargs):
        # Registrar inicio real
        if self.status == 'IN_PROGRESS' and not self.actual_start:
            self.actual_start = timezone.now()
        
        # Registrar fin real
        if self.status == 'DONE' and not self.actual_end:
            self.actual_end = timezone.now()
        
        super().save(*args, **kwargs)
    
    class Meta:
        db_table = 'tasks'
        ordering = ['-created_at']
        verbose_name = "Tarea"
        verbose_name_plural = "Tareas"