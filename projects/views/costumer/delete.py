from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Count, Q
from projects.models.costumer import Costumer
from projects.models.chance import Chance
from projects.models.projects import Projects


def customer_delete(request, ruc):
    customer = get_object_or_404(Costumer, pk=ruc)
    
    # Verificar si el cliente tiene relaciones activas
    has_chances = Chance.objects.filter(info_costumer=customer).exists()
    has_projects = Projects.objects.filter(cod_projects__info_costumer=customer).exists()
    
    # Si es POST, confirmar eliminación
    if request.method == 'POST':
        if has_chances or has_projects:
            messages.error(request, f"No se puede eliminar el cliente '{customer.com_name}' porque tiene oportunidades o proyectos asociados.")
            return redirect('customer_detail', ruc=customer.pk)
        
        com_name = customer.com_name
        customer.delete()
        messages.success(request, f"Cliente '{com_name}' eliminado correctamente.")
        return redirect('customers_list')
    
    # GET: Mostrar confirmación con información de relaciones
    context = {
        'customer': customer,
        'has_chances': has_chances,
        'has_projects': has_projects,
        'total_relations': (1 if has_chances else 0) + (1 if has_projects else 0),
    }
    
    return render(request, 'customers/delete_confirm.html', context)