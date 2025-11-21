from django.shortcuts import redirect, render
from projects.forms.presale.formpresale import PresaleForm
from projects.models.projects import Projects

def crear_presale(request):
    if request.method == "POST":
        form = PresaleForm(request.POST)   # ⬅️ 1. Vincula datos enviados al formulario
        if form.is_valid():                # ⬅️ 2. Valida que los campos sean correctos
            form.save()                    # ⬅️ 3. Guarda en BD (aquí se activa el save() del modelo)
            return redirect("crear_presale")     # ⬅️ 4. Redirige a la lista de preventas
    else:
        form = PresaleForm()               # ⬅️ 5. Si es GET, renderiza formulario vacío
    
    return render(request, "presale/form.html", {"form": form})

def create_pro(pre_venta):
    if pre_venta:
        Projects.objects.create(
            
        )


