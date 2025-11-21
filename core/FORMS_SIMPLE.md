# 📋 Guía Simple de Formularios

## 🎯 Patrón Estándar (Sigue el ejemplo de ChanceForm)

### 1. **Estructura de Archivos**
```
projects/
├── forms/
│   └── chance/
│       └── formchance.py    ← FORMULARIO
├── views/
│   └── presale/
│       └── create.py        ← VISTA (usa el formulario)
└── templates/
    └── presale/
        └── form.html        ← TEMPLATE (muestra el formulario)
```

### 2. **Cómo Crear un Formulario**

#### Paso 1: Crear el Formulario
**Archivo:** `projects/forms/[modulo]/form[nombre].py`

```python
from django import forms
from core.forms_base import BaseModelForm          # ← Importar esto
from core.forms_config import crear_widget         # ← Y esto
from projects.models.chance import Chance          # ← Tu modelo

class ChanceForm(BaseModelForm):                   # ← Heredar de BaseModelForm
    class Meta:
        model = Chance                              # ← Tu modelo
        fields = ['campo1', 'campo2', 'campo3']    # ← Campos que quieres
        widgets = {                                 # ← Cómo se ven los campos
            'campo1': crear_widget('text', placeholder='Ejemplo'),
            'campo2': crear_widget('date'),
            'campo3': crear_widget('number', step='0.01'),
        }
```

#### Paso 2: Crear la Vista
**Archivo:** `projects/views/[modulo]/create.py`

```python
from django.shortcuts import render, redirect
from django.contrib import messages
from projects.forms.chance.formchance import ChanceForm  # ← Tu formulario

def crear_presale(request):
    if request.method == "POST":                    # ← Si el usuario envía datos
        form = ChanceForm(request.POST)             # ← Cargar datos
        if form.is_valid():                         # ← Validar
            instance = form.save()                  # ← Guardar
            messages.success(request, "Creado exitosamente")
            return redirect("lista")                # ← Redirigir
        else:
            messages.error(request, "Error en el formulario")
    else:
        form = ChanceForm()                         # ← Formulario vacío
    
    return render(request, "presale/form.html", {"form": form})  # ← Mostrar template
```

#### Paso 3: Crear el Template
**Archivo:** `projects/templates/[modulo]/form.html`

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

## 🛠️ Widgets Disponibles

Usa `crear_widget()` con estos tipos:

```python
crear_widget('text', placeholder='Texto')           # Input de texto
crear_widget('number', step='0.01', min='0')        # Input numérico
crear_widget('date')                                 # Input de fecha
crear_widget('datetime')                             # Input fecha/hora
crear_widget('textarea', rows=3)                     # Área de texto
crear_widget('select')                               # Select dropdown
crear_widget('email')                                # Input email
crear_widget('file')                                 # Input archivo
```

## ✅ Ejemplo Real: ChanceForm

**Ver estos archivos como referencia:**
- Formulario: `projects/forms/chance/formchance.py`
- Vista: `projects/views/presale/create.py`
- Template: `projects/templates/presale/form.html`

Este es el patrón que debes seguir para todos los formularios.

## 📝 Validaciones (Opcional)

Si necesitas validar campos:

```python
from core.forms_config import validar_numero_positivo, validar_rango_fechas

def clean_monto(self):
    valor = self.cleaned_data.get('monto')
    return validar_numero_positivo(valor, mensaje="Debe ser mayor a 0")
```

## 🎯 Resumen

1. **Formulario** hereda de `BaseModelForm`
2. **Vista** usa el formulario y valida con `form.is_valid()`
3. **Template** muestra `{{ form.campo }}` 
4. **Widgets** se crean con `crear_widget()`
5. **Todo modular** - cada cosa en su carpeta

