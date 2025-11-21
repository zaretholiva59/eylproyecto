# 📋 Guía de Formularios - Patrón del Proyecto

## 🎯 Patrón Estándar

Todos los formularios siguen este patrón simple:

### 1. **Formulario** (`projects/forms/[modulo]/form[nombre].py`)
```python
from django import forms
from core.forms_base import BaseModelForm
from core.forms_config import crear_widget, validar_numero_positivo
from projects.models.chance import Chance

class ChanceForm(BaseModelForm):
    class Meta:
        model = Chance
        fields = ['campo1', 'campo2', 'campo3']
        widgets = {
            'campo1': crear_widget('text', placeholder='Ejemplo'),
            'campo2': crear_widget('date'),
            'campo3': crear_widget('number', step='0.01'),
        }
    
    def clean_campo3(self):
        valor = self.cleaned_data.get('campo3')
        return validar_numero_positivo(valor)
```

### 2. **Vista** (`projects/views/[modulo]/create.py`)
```python
from django.shortcuts import render, redirect
from django.contrib import messages
from projects.forms.chance.formchance import ChanceForm

def crear_presale(request):
    if request.method == "POST":
        form = ChanceForm(request.POST)
        if form.is_valid():
            instance = form.save()
            messages.success(request, "Creado exitosamente")
            return redirect("lista")
        else:
            messages.error(request, "Error en el formulario")
    else:
        form = ChanceForm()
    
    return render(request, "presale/form.html", {"form": form})
```

### 3. **Template** (`projects/templates/[modulo]/form.html`)
```html
{% extends "base.html" %}

<form method="POST">
    {% csrf_token %}
    
    <div class="form-group">
        <label>{{ form.campo1.label }}</label>
        {{ form.campo1 }}
        {% if form.campo1.errors %}
            <span class="text-danger">{{ form.campo1.errors }}</span>
        {% endif %}
    </div>
    
    <button type="submit" class="btn btn-primary">Guardar</button>
</form>
```

## 🛠️ Herramientas Disponibles

### `crear_widget(tipo, **attrs)`
Crea widgets con estilos Bootstrap:

- `'text'` - Input de texto
- `'number'` - Input numérico  
- `'date'` - Input de fecha
- `'datetime'` - Input fecha/hora
- `'textarea'` - Área de texto
- `'select'` - Select dropdown
- `'email'` - Input email
- `'file'` - Input archivo

**Ejemplos:**
```python
crear_widget('text', placeholder='Nombre')
crear_widget('number', step='0.01', min='0')
crear_widget('date')
crear_widget('textarea', rows=3)
```

### Validaciones Comunes
```python
from core.forms_config import validar_numero_positivo, validar_rango_fechas, validar_texto

def clean_monto(self):
    valor = self.cleaned_data.get('monto')
    return validar_numero_positivo(valor, mensaje="Debe ser mayor a 0")

def clean_fecha_fin(self):
    inicio = self.cleaned_data.get('fecha_inicio')
    fin = self.cleaned_data.get('fecha_fin')
    return validar_rango_fechas(inicio, fin)
```

## 📁 Estructura de Carpetas

```
projects/
├── forms/
│   ├── chance/
│   │   ├── __init__.py
│   │   └── formchance.py      ← Formulario de Chance
│   ├── oc/
│   │   └── pur.py             ← Formulario de OC
│   └── ...
├── views/
│   └── presale/
│       └── create.py          ← Vista que usa ChanceForm
└── templates/
    └── presale/
        └── form.html          ← Template del formulario
```

## ✅ Ejemplo Completo: ChanceForm

**Ver:** `projects/forms/chance/formchance.py`  
**Vista:** `projects/views/presale/create.py`  
**Template:** `projects/templates/presale/form.html`

Este es el ejemplo que debes seguir para crear nuevos formularios.

