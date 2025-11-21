"""
Configuración base SIMPLE para formularios Django
Proporciona widgets con estilos Bootstrap consistentes
"""

from django import forms
from django.core.exceptions import ValidationError


# ============================================================================
# FUNCIÓN HELPER SIMPLE
# ============================================================================

def crear_widget(tipo, **attrs):
    """
    Crear un widget con estilos Bootstrap
    
    Tipos: 'text', 'number', 'date', 'datetime', 'textarea', 'select', 'email', 'file'
    
    Ejemplo:
        widget = crear_widget('text', placeholder='Nombre')
        widget = crear_widget('number', step='0.01', min='0')
        widget = crear_widget('date')
    """
    widgets = {
        'text': forms.TextInput,
        'email': forms.EmailInput,
        'number': forms.NumberInput,
        'date': forms.DateInput,
        'datetime': forms.DateTimeInput,
        'textarea': forms.Textarea,
        'select': forms.Select,
        'file': forms.FileInput,
    }
    
    widget_class = widgets.get(tipo)
    if not widget_class:
        # Por defecto usar TextInput
        widget_class = forms.TextInput
    
    # Estilos Bootstrap por defecto
    default_attrs = {'class': 'form-control'}
    
    # Para date y datetime, añadir type
    if tipo == 'date':
        default_attrs['type'] = 'date'
    elif tipo == 'datetime':
        default_attrs['type'] = 'datetime-local'
    
    # Combinar con atributos personalizados
    default_attrs.update(attrs)
    
    return widget_class(attrs=default_attrs)


# ============================================================================
# VALIDACIONES COMUNES
# ============================================================================

def validar_numero_positivo(valor, mensaje="El valor debe ser mayor a 0"):
    """Validar que un número sea positivo"""
    if valor is not None and valor != '':
        try:
            num = float(valor) if isinstance(valor, str) else valor
            if num <= 0:
                raise ValidationError(mensaje)
            return num
        except (ValueError, TypeError):
            raise ValidationError(mensaje)
    return valor


def validar_rango_fechas(fecha_inicio, fecha_fin, mensaje="La fecha fin debe ser posterior a la fecha inicio"):
    """Validar que la fecha fin sea posterior a la fecha inicio"""
    if fecha_inicio and fecha_fin:
        if fecha_fin <= fecha_inicio:
            raise ValidationError(mensaje)
    return fecha_fin


def validar_texto(valor, min_longitud=0, max_longitud=None):
    """Limpiar y validar campo de texto"""
    if valor:
        valor = ' '.join(str(valor).split())
        
        if min_longitud and len(valor) < min_longitud:
            raise ValidationError(f'Debe tener al menos {min_longitud} caracteres')
        
        if max_longitud and len(valor) > max_longitud:
            raise ValidationError(f'Debe tener máximo {max_longitud} caracteres')
    
    return valor
