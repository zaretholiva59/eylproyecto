from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re
from projects.models.costumer import Costumer


class CostumerForm(forms.ModelForm):
    def clean_ruc_costumer(self):
        """Validar formato de RUC peruano"""
        ruc = self.cleaned_data['ruc_costumer']
        
        # Eliminar espacios y convertir a mayúsculas
        ruc = ruc.strip().upper()
        
        # Validar longitud (debe ser 11 dígitos)
        if len(ruc) != 11:
            raise ValidationError(_('El RUC debe tener 11 dígitos'))
        
        # Validar que sean solo números
        if not ruc.isdigit():
            raise ValidationError(_('El RUC debe contener solo números'))
        
        # Validar dígito verificador (algoritmo para RUC peruano)
        def calcular_digito_verificador(ruc):
            """Calcular dígito verificador para RUC peruano (SUNAT)"""
            if len(ruc) != 11:
                return False

            coeficientes = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
            digitos = [int(d) for d in ruc[:10]]

            suma = sum(d * c for d, c in zip(digitos, coeficientes))
            residuo = suma % 11

            # Fórmula estándar: dv = 11 - residuo; ajustar casos 10 y 11
            dv = 11 - residuo
            if dv == 10:
                dv = 0
            elif dv == 11:
                dv = 1

            return dv == int(ruc[10])
        
        if not calcular_digito_verificador(ruc):
            raise ValidationError(_('El RUC no es válido'))
        
        # Verificar si ya existe (solo en creación)
        if not self.instance.pk and Costumer.objects.filter(pk=ruc).exists():
            raise ValidationError(_('Ya existe un cliente con este RUC'))
        
        return ruc
    
    def clean_com_name(self):
        """Validar nombre comercial"""
        nombre = self.cleaned_data['com_name']
        
        # Eliminar espacios extras
        nombre = ' '.join(nombre.split())
        
        # Validar longitud mínima
        if len(nombre) < 3:
            raise ValidationError(_('El nombre debe tener al menos 3 caracteres'))
        
        return nombre
    
    def clean_contac_costumer(self):
        """Validar nombre de contacto"""
        contacto = self.cleaned_data['contac_costumer']
        
        if contacto:
            # Eliminar espacios extras
            contacto = ' '.join(contacto.split())
            
            # Validar formato (solo letras y espacios)
            if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', contacto):
                raise ValidationError(_('El nombre del contacto solo puede contener letras'))
        
        return contacto
    
    class Meta:
        model = Costumer
        fields = [
            'ruc_costumer',
            'com_name',
            'type_costumer',
            'contac_costumer',
        ]
        widgets = {
            'ruc_costumer': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese RUC (11 dígitos)',
                'maxlength': '11',
                'pattern': '[0-9]{11}',
                'title': 'El RUC debe tener 11 dígitos numéricos',
            }),
            'com_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre comercial / Razón social',
                'maxlength': '255',
            }),
            'type_costumer': forms.Select(attrs={
                'class': 'form-control',
            }),
            'contac_costumer': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Persona de contacto (opcional)',
                'maxlength': '100',
            }),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Hacer el campo RUC solo lectura en edición
        if self.instance and self.instance.pk:
            self.fields['ruc_costumer'].widget.attrs['readonly'] = True
            self.fields['ruc_costumer'].help_text = 'El RUC no se puede modificar'