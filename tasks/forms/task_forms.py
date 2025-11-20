# tasks/forms/task_forms.py
from django import forms
from django.utils import timezone
from datetime import datetime
from tasks.models.task import Task
from projects.models.projects import Projects

class TaskForm(forms.ModelForm):
    # Campo opcional para parent (sub-tareas)
    parent = forms.ModelChoiceField(
        required=False,
        queryset=Task.objects.all(),
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-blue-500',
        }),
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
        if planned_start and planned_start < timezone.now():
            raise forms.ValidationError('⚠️ La fecha de inicio no puede ser en el pasado.')
        return planned_start
    
    def clean_planned_end(self):
        """Validar fecha de fin"""
        planned_end = self.cleaned_data.get('planned_end')
        planned_start = self.cleaned_data.get('planned_start')
        
        if planned_start and planned_end and planned_end <= planned_start:
            raise forms.ValidationError('⚠️ La fecha fin debe ser posterior a la fecha inicio.')
        
        return planned_end
    
    def clean_units_planned(self):
        """Validar unidades planificadas"""
        units_planned = self.cleaned_data.get('units_planned')
        if units_planned and units_planned <= 0:
            raise forms.ValidationError('⚠️ Las unidades planificadas deben ser mayores a 0.')
        return units_planned
    
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
            'project': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-blue-500',
            }),
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-blue-500',
                'placeholder': 'Ej: Instalación eléctrica principal'
            }),
            'units_planned': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-blue-500',
                'step': '0.01',
                'min': '0.01',
                'value': '1.00'
            }),
            'planned_start': forms.DateTimeInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-blue-500',
                'type': 'datetime-local'
            }),
            'planned_end': forms.DateTimeInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-blue-500', 
                'type': 'datetime-local'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Descripción detallada de la tarea...'
            }),
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