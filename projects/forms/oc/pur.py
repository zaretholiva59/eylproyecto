from django import forms
from projects.models import PurchaseOrder
from projects.models.presale import Presale  # para obtener cost_center

class PurchaseOrderForm(forms.ModelForm):
    # Campo extra: Centro de costo (readonly, se llenará automáticamente al elegir el proyecto)
    cost_center = forms.CharField(
        label="Centro de Costo",
        required=False,
        widget=forms.TextInput(attrs={"readonly": "readonly", "class": "form-control"})
    )

    class Meta:
        model = PurchaseOrder
        fields = [
            "po_number",
            "project_code",
            "issue_date",
            "initial_delivery_date",
            "final_delivery_date",
            "currency",
            "po_status",
            "observations",
        ]
        widgets = {
            "po_number": forms.TextInput(attrs={"class": "form-control"}),
            "issue_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "initial_delivery_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "final_delivery_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "currency": forms.Select(attrs={"class": "form-select"}),
            "po_status": forms.Select(attrs={"class": "form-select"}),
            "observations": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Agregar placeholder al seleccionar proyecto
        self.fields["project_code"].label = "Código Proyecto"
        self.fields["project_code"].widget.attrs.update({"class": "form-select"})
