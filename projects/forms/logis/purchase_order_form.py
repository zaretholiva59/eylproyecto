# projects/forms/logis/purchase_order.py
from django import forms
from django.forms import inlineformset_factory
from projects.models import (
    PurchaseOrder,
    PODetailProduct,
    PODetailSupplier,
    Projects,
)

# === 1. FORM PRINCIPAL ORDEN DE COMPRA ===
class PurchaseOrderForm(forms.ModelForm):
    project_code = forms.ModelChoiceField(
        queryset=Projects.objects.all(),
        label="Proyecto",
        empty_label="Seleccione un proyecto",
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    cost_center = forms.CharField(
        label="Centro de Costo",
        required=False,
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control'})
    )

    class Meta:
        model = PurchaseOrder
        fields = [
            'po_number',
            'issue_date',
            'initial_delivery_date',
            'final_delivery_date',
            'currency',
            'project_code',
            'po_status',
            'observations',
            'local_import', 'te', 'forma_pago', 'pagar_a' 
        ]
        widgets = {
            'po_number': forms.TextInput(attrs={'class': 'form-control'}),
            'issue_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'initial_delivery_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'final_delivery_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'po_status': forms.Select(attrs={'class': 'form-select'}),
            'observations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, project_id=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Si recibimos un proyecto, rellenamos automáticamente el centro de costo
        if project_id:
            try:
                project = Projects.objects.get(cod_projects_id=project_id)
                self.fields['cost_center'].initial = project.cost_center
                self.fields['project_code'].initial = project
            except Projects.DoesNotExist:
                pass


# === 2. DETALLE PRODUCTO ===
class PODetailProductForm(forms.ModelForm):
    product_name = forms.CharField(   
        required=False,
        label="Producto",
        widget=forms.TextInput(attrs={'class': 'form-control product-autocomplete'})
    )

    class Meta:
        model = PODetailProduct
        fields = ['product', 'product_name', 'quantity', 'unit_price', 'comment']  # ✅ AGREGAR 'comment'
        widgets = {
            'product': forms.HiddenInput(),
            'quantity': forms.NumberInput(attrs={'class': 'form-control quantity'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control unit_price', 'step': '0.01'}),
            'comment': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comentario'}),  # ✅ NUEVO
        }

# === 3. DETALLE PROVEEDOR ===
class PODetailSupplierForm(forms.ModelForm):
    supplier_name = forms.CharField(   
        required=False,
        label="Proveedor",
        widget=forms.TextInput(attrs={'class': 'form-control supplier-autocomplete'})
    )

    class Meta:
        model = PODetailSupplier
        fields = ['supplier', 'supplier_name', 'supplier_amount', 'delivery_date', 'supplier_status','status_factura_contabilidad' ]
        widgets = {
            'supplier': forms.HiddenInput(),
            'delivery_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'supplier_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'supplier_status': forms.TextInput(attrs={'class': 'form-control'}),
        }
# === 4. FORMSETS ===
PODetailProductFormset = inlineformset_factory(
    PurchaseOrder,
    PODetailProduct,
    form=PODetailProductForm,
    extra=1,
    can_delete=True,
    fields=['product', 'product_name', 'quantity', 'unit_price', 'comment']  # ✅ AGREGAR 'comment'
)

PODetailSupplierFormset = inlineformset_factory(
    PurchaseOrder,
    PODetailSupplier,
    form=PODetailSupplierForm,
    extra=1,
    can_delete=True,
    fields=['supplier', 'supplier_name', 'supplier_amount', 'delivery_date', 'supplier_status', 'status_factura_contabilidad']  # ✅ AGREGAR CAMPO
)