from django.shortcuts import redirect, render
from django.contrib import messages
from django.core.cache import cache
from projects.forms.chance.formchance import ChanceForm  # ⬅️ Usar ChanceForm
import json
from projects.models.chance import Chance
from projects.models.projects import Projects

def crear_presale(request):
    if request.method == "POST":
        form = ChanceForm(request.POST)   # Usa ChanceForm
        if form.is_valid():
            instance = form.save(commit=False)        # Guarda en Chance (calcula total_costs y aprox_uti)
            # Persistir centros de costo adicionales (solo códigos)
            raw = request.POST.get('extra_cost_centers_json')
            try:
                centers = json.loads(raw) if raw else []
                if not centers:
                    centers = request.POST.getlist('extra_centers[]')
                instance.set_extra_cost_centers(centers, replace=True)
            except Exception:
                instance.set_extra_cost_centers([], replace=True)

            # Calcular duración estimada desde fechas si están presentes
            start_date = form.cleaned_data.get('project_start_date')
            end_date = instance.date_aprox_close
            if start_date and end_date:
                try:
                    days = (end_date - start_date).days
                    instance.estimated_duration = max(days, 1)
                except Exception:
                    pass

            instance.save()
            # Sincronizar fecha de inicio y cierre estimado en Projects
            try:
                proj = Projects.objects.get(cod_projects=instance)
                start_date = form.cleaned_data.get('project_start_date')
                if start_date:
                    proj.start_date = start_date
                # También reflejar la fecha estimada de cierre si existe
                if instance.date_aprox_close:
                    proj.estimated_end_date = instance.date_aprox_close
                # Recalcular también duración en Projects
                if start_date and instance.date_aprox_close:
                    try:
                        proj.estimated_duration = max((instance.date_aprox_close - start_date).days, 1)
                    except Exception:
                        proj.estimated_duration = instance.estimated_duration
                else:
                    proj.estimated_duration = instance.estimated_duration
                proj.save()
            except Projects.DoesNotExist:
                pass
            # Invalidar caché de la lista optimizada si existe
            cache.delete('chance_list_optimized')
            messages.success(request, f"Oportunidad '{instance.cod_projects}' creada exitosamente.")
            return redirect("presale_list")
        else:
            messages.error(request, "Error en el formulario. Revisa los campos.")
    else:
        form = ChanceForm()               # Formulario vacío
    
    return render(request, "presale/form.html", {"form": form})

# Nota: Se eliminó create_pro(pre_venta) por estar incompleta y no utilizada