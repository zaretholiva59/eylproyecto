from django import forms
from projects.models.chance import Chance


class ChanceForm(forms.ModelForm):
    # Campo adicional no-modelo para fecha de inicio del proyecto
    project_start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    def clean(self):
        cleaned_data = super().clean()
        currency = cleaned_data.get('currency')
        exchange_rate = cleaned_data.get('exchange_rate')
        if currency != 'PEN':
            if not exchange_rate or exchange_rate <= 0:
                self.add_error('exchange_rate', '⚠️ Ingrese un tipo de cambio válido (> 0).')
        else:
            cleaned_data['exchange_rate'] = 1
        return cleaned_data
    
    class Meta:
        model = Chance
        fields = [
            'cod_projects',
            'info_costumer',
            'staff_presale',
            'cost_center',
            'com_exe',
            'dres_chance',
            'date_aprox_close',
            'currency',
            'exchange_rate',
            'cost_aprox_chance',
            'material_cost',
            'labor_cost',
            'subcontracted_cost',
            'overhead_cost',
        ]
        widgets = {
            'cod_projects': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: PROJ-2024-001'
            }),
            'info_costumer': forms.Select(attrs={
                'class': 'form-control'
            }),
            'staff_presale': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo'
            }),
            'cost_center': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: CC-001'
            }),
            'com_exe': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del ejecutivo'
            }),
            'dres_chance': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción detallada del proyecto'
            }),
            'date_aprox_close': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'currency': forms.Select(attrs={
                'class': 'form-control'
            }),
            'exchange_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001',
                'min': '0',
                'placeholder': 'Ej: 3.7600'
            }),
            'cost_aprox_chance': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'material_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'labor_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'subcontracted_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'overhead_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
        }