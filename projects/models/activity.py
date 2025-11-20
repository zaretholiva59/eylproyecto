from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class ProjectActivity(models.Model):
    """
    Modelo para actividades específicas del proyecto
    Alineado con PMI para cálculo preciso de Earned Value
    """
    
    # Relación con proyecto
    project = models.ForeignKey(
        'Projects', 
        on_delete=models.CASCADE, 
        related_name='activities',
        verbose_name="Proyecto"
    )
    
    # Datos básicos de la actividad
    name = models.CharField(
        "Nombre de la actividad",
        max_length=200,
        help_text="Ej: Instalación puntos de red, Configuración equipos, etc."
    )
    
    description = models.TextField(
        "Descripción",
        blank=True,
        help_text="Detalles específicos de la actividad"
    )
    
    # Criterios para cálculo automático de pesos (1-5 puntos)
    complexity = models.IntegerField(
        "Complejidad técnica",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1=Básico, 5=Avanzado",
        choices=[(1, '1 - Básico'), (2, '2'), (3, '3 - Medio'), (4, '4'), (5, '5 - Avanzado')]
    )
    
    effort = models.IntegerField(
        "Esfuerzo estimado", 
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1=Poco esfuerzo, 5=Mucho esfuerzo",
        choices=[(1, '1 - Bajo'), (2, '2'), (3, '3 - Medio'), (4, '4'), (5, '5 - Alto')]
    )
    
    impact = models.IntegerField(
        "Impacto en el proyecto",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1=Bajo impacto, 5=Crítico",
        choices=[(1, '1 - Bajo'), (2, '2'), (3, '3 - Medio'), (4, '4'), (5, '5 - Crítico')]
    )
    
    # Peso calculado automáticamente
    calculated_weight = models.DecimalField(
        "Peso calculado (%)",
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Calculado automáticamente basado en complejidad, esfuerzo e impacto"
    )
    
    # Sistema de unidades flexible
    unit_of_measure = models.CharField(
        "Unidad de medida",
        max_length=50,
        help_text="Ej: puntos, equipos, metros, pruebas, etc."
    )
    
    total_units = models.IntegerField(
        "Total de unidades",
        validators=[MinValueValidator(1)],
        help_text="Cantidad total a completar"
    )
    
    completed_units = models.IntegerField(
        "Unidades completadas",
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Cantidad actualmente completada"
    )
    
    percentage_completed = models.DecimalField(
        "Porcentaje completado",
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Calculado automáticamente: (completadas / total) * 100"
    )
    
    # Control y auditoría
    is_active = models.BooleanField("Activa", default=True)
    created_at = models.DateTimeField("Fecha creación", auto_now_add=True)
    updated_at = models.DateTimeField("Fecha actualización", auto_now=True)
    created_by = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='created_activities'
    )
    
    class Meta:
        verbose_name = "Actividad del proyecto"
        verbose_name_plural = "Actividades del proyecto"
        ordering = ['-calculated_weight', 'name']
        indexes = [
            models.Index(fields=['project', 'is_active']),
            models.Index(fields=['calculated_weight']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.calculated_weight}%) - {self.percentage_completed}%"
    
    def save(self, *args, **kwargs):
        # Calcular porcentaje completado
        if self.total_units > 0:
            self.percentage_completed = (self.completed_units / self.total_units) * 100
        else:
            self.percentage_completed = 0.00
            
        # Validar que completed_units no exceda total_units
        if self.completed_units > self.total_units:
            self.completed_units = self.total_units
            
        super().save(*args, **kwargs)







