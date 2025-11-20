from django import forms
from projects.models.chance import Chance
from projects.models.invoice import Invoice
from projects.models.oc import PurchaseOrder
from projects.models.product import Product
from projects.models.podetail_product import PODetailProduct
from projects.models.supplier import Supplier

class ChanceForm(forms.ModelForm):
    class Meta:
        model = Chance
        fields = ['cod_projects', 'cost_center']
        widgets = {
            'cod_projects': forms.TextInput(attrs={'class': 'form-control'}),
            'cost_center': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['cod_art', 'part_number', 'descrip', 'manufac', 'model']
        widgets = {
            'cod_art': forms.TextInput(attrs={'class': 'form-control'}),
            'part_number': forms.TextInput(attrs={'class': 'form-control'}),
            'descrip': forms.TextInput(attrs={'class': 'form-control'}),
            'manufac': forms.TextInput(attrs={'class': 'form-control'}),
            'model': forms.TextInput(attrs={'class': 'form-control'}),
        }

class PODetailProductForm(forms.ModelForm):
    class Meta:
        model = PODetailProduct
        fields = [
            'product',           # Para Cod. Producto, PN, Detalle, Marca, Modelo
            'quantity',          # Metrado
            'measurement_unit',  # UND  
            'unit_price',        # Costo Unitario
            'total',             # Costo Total
            'local_total',       # S/.
            'comment',           # Comentarios
        ]
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'measurement_unit': forms.Select(attrs={'class': 'form-select'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'readonly': 'readonly'}),
            'local_total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'readonly': 'readonly'}),
            'comment': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ocForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = [
            'po_number',           # Orden de Compra
            'issue_date',          # Fecha de Orden
            'currency',            # Moneda
            'guide_number',        # GR
            'guide_date',          # Fecha Guía
            'project_code',        # Cod. Proyecto, Centro de Costos
            'exchange_rate',       # T.C.
        ]
        widgets = {
            'po_number': forms.TextInput(attrs={'class': 'form-control'}),
            'issue_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'currency': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('PEN', 'Soles'),
                ('USD', 'Dólares'),
            ]),
            'guide_number': forms.TextInput(attrs={'class': 'form-control'}),
            'guide_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'project_code': forms.Select(attrs={'class': 'form-select'}),
            'exchange_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
        }

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name_supplier']  # Proveedor
        widgets = {
            'name_supplier': forms.TextInput(attrs={'class': 'form-control'}),
        }

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            'invoice_number',      # N° Comprobante
            'issue_date',          # F. Factura
        ]
        widgets = {
            'invoice_number': forms.TextInput(attrs={'class': 'form-control'}),
            'issue_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }