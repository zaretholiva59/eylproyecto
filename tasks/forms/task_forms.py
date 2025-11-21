# tasks/forms/task_forms.py
from django import forms
from django.utils import timezone
from datetime import datetime
from tasks.models.task import Task
from projects.models.projects import Projects
from core.forms_base import BaseModelForm
from core.forms_config import crear_widget, validar_numero_positivo, validar_rango_fechas

class TaskForm(BaseModelForm):
    # Campo opcional para parent (sub-tareas)
    parent = forms.ModelChoiceField(
        required=False,
        queryset=Task.objects.all(),
        widget=crear_widget('select'),
        label="📂 Tarea Padre",
        help_text="Opcional: selecciona si es una sub-tarea"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar el queryset de proyectos
        self.fields['project'].queryset = Projects.objects.all()
        
        # Personalizar el queryset de parent tasks (excluir la tarea actual si está editando)
        if self.instance and self.instance.pk:
            self.fields['parent'].queryset = Task.objects.exclude(pk=self.instance.pk)
    
    def clean_planned_start(self):
        """Validar fecha de inicio"""
        planned_start = self.cleaned_data.get('planned_start')
        # Permitir fechas en el pasado para flexibilidad (se puede cambiar después)
        # if planned_start and planned_start < timezone.now():
        #     raise forms.ValidationError('⚠️ La fecha de inicio no puede ser en el pasado.')
        return planned_start
    
    def clean_planned_end(self):
        """Validar fecha de fin"""
        planned_end = self.cleaned_data.get('planned_end')
        planned_start = self.cleaned_data.get('planned_start')
        
        return validar_rango_fechas(
            planned_start,
            planned_end,
            mensaje='⚠️ La fecha fin debe ser posterior a la fecha inicio.'
        )
    
    def clean_units_planned(self):
        """Validar unidades planificadas"""
        units_planned = self.cleaned_data.get('units_planned')
        # Si no se proporciona, usar valor por defecto
        if units_planned is None or units_planned == '':
            return 1.0
        return validar_numero_positivo(
            units_planned, 
            mensaje='⚠️ Las unidades planificadas deben ser mayores a 0.'
        )
    
    def clean(self):
        """Validación general"""
        cleaned_data = super().clean()
        # Aquí puedes agregar validaciones que involucren múltiples campos
        return cleaned_data
    
    class Meta:
        model = Task
        fields = [
            'project',
            'title', 
            'units_planned',
            'planned_start',
            'planned_end',
            'parent',  # Nuevo campo para sub-tareas
            'descripcion'  # Agregamos descripción también
        ]
        widgets = {
            'project': crear_widget('select'),
            'title': crear_widget('text', placeholder='Ej: Instalación eléctrica principal'),
            'units_planned': crear_widget('number', step='0.01', min='0.01', value='1.00'),
            'planned_start': crear_widget('datetime'),
            'planned_end': crear_widget('datetime'),
            'descripcion': crear_widget('textarea', rows=3, placeholder='Descripción detallada de la tarea...'),
            'parent': crear_widget('select'),
        }
        labels = {
            'project': '🏢 Proyecto',
            'title': '📝 Título de la tarea',
            'units_planned': '📊 Unidades planificadas',
            'planned_start': '📅 Fecha inicio', 
            'planned_end': '📅 Fecha fin',
            'descripcion': '📋 Descripción',
        }
        help_texts = {
            'units_planned': 'Cantidad total de unidades a completar (ej: 10.50 metros)',
            'planned_start': 'Fecha y hora estimada de inicio',
            'planned_end': 'Fecha y hora estimada de finalización',
        }