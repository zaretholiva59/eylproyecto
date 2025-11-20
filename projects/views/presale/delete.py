from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.core.cache import cache  # ⬅️ IMPORTAR CACHE
from projects.models.chance import Chance

def presale_delete(request, pk):
    # Buscar Chance por su clave primaria (cod_projects)
    chance_obj = get_object_or_404(Chance, cod_projects=pk)

    if request.method == 'POST':
        project_code = chance_obj.cod_projects
        project_name = chance_obj.dres_chance
        
        chance_obj.delete()
        
        # ⬇️ NUEVO: INVALIDAR CACHE
        cache.delete('chance_list_optimized')
        
        messages.success(
            request,
            f'La oportunidad "{project_name}" (Código: {project_code}) ha sido eliminada exitosamente.'
        )

    return redirect('presale_list')