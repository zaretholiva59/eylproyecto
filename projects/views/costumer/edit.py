from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from projects.models.costumer import Costumer
from projects.forms.costumer.formcostumer import CostumerForm

def customer_edit(request, ruc_costumer):
    customer = get_object_or_404(Costumer, pk=ruc_costumer)
    if request.method == 'POST':
        form = CostumerForm(request.POST, instance=customer)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f'Cliente "{customer.com_name}" actualizado exitosamente.')
            return redirect('customers_list')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        form = CostumerForm(instance=customer)
    
    context = {
        'form': form, 
        'title': 'Editar cliente',
        'customer': customer,
        'is_create': False
    }
    return render(request, 'customers/form.html', context)