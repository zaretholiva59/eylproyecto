from django import forms
from projects.models.chance import Chance
from core.forms_base import BaseModelForm
from core.forms_config import crear_widget, validar_numero_positivo


class ChanceForm(BaseModelForm):
    # Campo adicional no-modelo para fecha de inicio del proyecto
    project_start_date = forms.DateField(
        required=False,
        widget=crear_widget('date')
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
            'cod_projects': crear_widget('text', placeholder='Ej: PROJ-2024-001'),
            'info_costumer': crear_widget('select'),
            'staff_presale': crear_widget('text', placeholder='Nombre completo'),
            'cost_center': crear_widget('text', placeholder='Ej: CC-001'),
            'com_exe': crear_widget('text', placeholder='Nombre del ejecutivo'),
            'dres_chance': crear_widget('textarea', rows=3, placeholder='Descripción detallada del proyecto'),
            'date_aprox_close': crear_widget('date'),
            'currency': crear_widget('select'),
            'exchange_rate': crear_widget('number', step='0.0001', min='0', placeholder='Ej: 3.7600'),
            'cost_aprox_chance': crear_widget('number', step='0.01', min='0', placeholder='0.00'),
            'material_cost': crear_widget('number', step='0.01', min='0', placeholder='0.00'),
            'labor_cost': crear_widget('number', step='0.01', min='0', placeholder='0.00'),
            'subcontracted_cost': crear_widget('number', step='0.01', min='0', placeholder='0.00'),
            'overhead_cost': crear_widget('number', step='0.01', min='0', placeholder='0.00'),
        }