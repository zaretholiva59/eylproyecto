# tasks/forms/task_forms.py
from django import forms
from django.utils import timezone
from datetime import datetime
from tasks.models.task import Task
from projects.models.projects import Projects
from core.forms_base import BaseModelForm
from core.forms_config import crear_widget, validar_numero_positivo, validar_rango_fechas

class TaskForm(BaseModelForm):
    # 🎯 NUEVO: Campo PROJECT definido explícitamente
    project = forms.ModelChoiceField(
        queryset=Projects.objects.all(),
        widget=crear_widget('select'),
        label="🏢 Proyecto",
        help_text="Selecciona el proyecto para esta tarea"
    )
    
    # 🎯 NUEVO: Campo opcional para parent (sub-tareas)
    parent = forms.ModelChoiceField(
        required=False,
        queryset=Task.objects.all(),
        widget=crear_widget('select'),
        label="📂 Tarea Padre",
        help_text="Opcional: selecciona si es una sub-tarea"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 🎯 NUEVO: Personalizar cómo se muestran los proyectos
        self.fields['project'].label_from_instance = self.get_project_display_name
        
        # Personalizar el queryset de parent tasks (excluir la tarea actual si está editando)
        if self.instance and self.instance.pk:
            self.fields['parent'].queryset = Task.objects.exclude(pk=self.instance.pk)
    
    def get_project_display_name(self, obj):
        """
        🎯 PERSONALIZAR: Cómo se muestra cada proyecto en el dropdown
        Convierte: "projects Edificios - AYA EDIFICACIONES ($80,000.00) (Planeado)"
        En: "1 - AYA EDIFICACIONES"
        """
        # obj es cada proyecto de la base de datos
        cod_str = str(obj.cod_projects)
        
        print(f"DEBUG: Proyecto original: {cod_str}")  # Para ver qué está llegando
        
        # Extraer solo la parte antes del primer '('
        nombre_limpio = cod_str.split('(')[0].strip()
        
        # Limpiar "projects " si existe al inicio
        if nombre_limpio.startswith('projects '):
            nombre_limpio = nombre_limpio.replace('projects ', '', 1)
        
        # Si tiene ' - ' separar y tomar la parte después del último ' - '
        if ' - ' in nombre_limpio:
            # Tomar solo la parte después del último ' - '
            partes = nombre_limpio.split(' - ')
            nombre_limpio = partes[-1]  # Última parte
        
        # Si el nombre está vacío, usar el código como respaldo
        if not nombre_limpio or nombre_limpio.isspace():
            nombre_limpio = f"Proyecto {obj.cod_projects_id}"
            
        return f"{obj.cod_projects_id} - {nombre_limpio.strip()}"
    
    def clean_planned_start(self):
        """Validar fecha de inicio"""
        planned_start = self.cleaned_data.get('planned_start')
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
        if units_planned is None or units_planned == '':
            return 1.0
        return validar_numero_positivo(
            units_planned, 
            mensaje='⚠️ Las unidades planificadas deben ser mayores a 0.'
        )
    
    def clean(self):
        """Validación general"""
        cleaned_data = super().clean()
        return cleaned_data
    
    class Meta:
        model = Task
        fields = [
            'project',      # 🎯 AHORA ESTÁ DEFINIDO EN EL FORM
            'title', 
            'units_planned',
            'planned_start',
            'planned_end',
            'descripcion'
        ]
        widgets = {
            'project': crear_widget('select'),
            'title': crear_widget('text', placeholder='Ej: Instalación eléctrica principal'),
            'units_planned': crear_widget('number', step='0.01', min='0.01', value='1.00'),
            'planned_start': crear_widget('datetime'),
            'planned_end': crear_widget('datetime'),
            'descripcion': crear_widget('textarea', rows=3, placeholder='Descripción detallada de la tarea...'),
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
            'parent': 'Selecciona una tarea existente si esta es una sub-tarea',
        }