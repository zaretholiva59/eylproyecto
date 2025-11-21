"""
Clase base SIMPLE para formularios Django
Aplica estilos Bootstrap automáticamente
"""

from django import forms
from core.forms_config import crear_widget


class BaseModelForm(forms.ModelForm):
    """
    Clase base para formularios de modelos con estilos Bootstrap
    
    Uso:
        class MiFormulario(BaseModelForm):
            class Meta:
                model = MiModelo
                fields = ['campo1', 'campo2']
                widgets = {
                    'campo1': crear_widget('text', placeholder='Ingrese...'),
                    'campo2': crear_widget('date'),
                }
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aplicar estilos Bootstrap a todos los campos que no tengan widget personalizado
        for field_name, field in self.fields.items():
            if not field.widget.attrs.get('class'):
                field.widget.attrs['class'] = 'form-control'


class BaseForm(forms.Form):
    """
    Clase base para formularios simples con estilos Bootstrap
    
    Uso:
        class MiFormulario(BaseForm):
            nombre = forms.CharField(
                widget=crear_widget('text', placeholder='Nombre')
            )
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aplicar estilos Bootstrap a todos los campos
        for field_name, field in self.fields.items():
            if not field.widget.attrs.get('class'):
                field.widget.attrs['class'] = 'form-control'
