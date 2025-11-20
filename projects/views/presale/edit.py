from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.core.cache import cache
from projects.models.chance import Chance
import json
from projects.forms.presale.formpresale import PresaleForm
from projects.models.projects import Projects


def presale_edit(request, pk):
    # Buscar Chance por su clave primaria (cod_projects)
    chance_obj = get_object_or_404(Chance, cod_projects=pk)

    if request.method == "POST":
        form = PresaleForm(request.POST, instance=chance_obj)
        if form.is_valid():
            instance = form.save(commit=False)
            # Conservar fecha de cierre si no se envía en el formulario
            if not form.cleaned_data.get('date_aprox_close'):
                instance.date_aprox_close = getattr(chance_obj, 'date_aprox_close', None)
            # Persistir centros de costo adicionales (solo códigos)
            raw = request.POST.get('extra_cost_centers_json')
            try:
                submitted_any = False
                centers = []
                if raw is not None and raw.strip() not in ('', '[]'):
                    centers = json.loads(raw)
                    submitted_any = True
                if not submitted_any:
                    posted_list = request.POST.getlist('extra_centers[]')
                    if posted_list:
                        centers = posted_list
                        submitted_any = True
                if submitted_any:
                    instance.set_extra_cost_centers(centers, replace=True)
            except Exception:
                pass
            # Calcular duración estimada desde fechas si están presentes
            start_date = form.cleaned_data.get('project_start_date')
            end_date = instance.date_aprox_close
            if start_date and end_date:
                try:
                    days = (end_date - start_date).days
                    instance.estimated_duration = max(days, 1)
                except Exception:
                    pass

            instance.save()  # Chance.save() calcula total_costs y aprox_uti
            # Sincronizar Projects con la fecha de inicio y cierre estimado
            try:
                proj = Projects.objects.get(cod_projects=instance)
                start_date = form.cleaned_data.get('project_start_date')
                if start_date:
                    proj.start_date = start_date
                if instance.date_aprox_close:
                    proj.estimated_end_date = instance.date_aprox_close
                if start_date and instance.date_aprox_close:
                    try:
                        proj.estimated_duration = max((instance.date_aprox_close - start_date).days, 1)
                    except Exception:
                        pass
                proj.save()
            except Projects.DoesNotExist:
                pass
            messages.success(request, f'La oportunidad "{chance_obj.dres_chance}" ha sido actualizada exitosamente.')
            # Invalidar caché de la lista optimizada para reflejar cambios de inmediato
            cache.delete('chance_list_optimized')
            return redirect("presale_list")
        else:
            messages.error(request, "Error al actualizar. Revisa los datos.")
    else:
        form = PresaleForm(instance=chance_obj)
        try:
            proj = Projects.objects.get(cod_projects=chance_obj)
            form.initial['project_start_date'] = proj.start_date
        except Projects.DoesNotExist:
            pass
        if getattr(chance_obj, 'date_aprox_close', None):
            form.initial['date_aprox_close'] = chance_obj.date_aprox_close

    context = {
        "form": form,
        "chance": chance_obj,
        "edit_mode": True
    }
    return render(request, "presale/form.html", context)