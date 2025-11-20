from django.contrib import messages
from django.shortcuts import render, redirect
from projects.forms.costumer.formcostumer import CostumerForm


def customer_create(request):
    if request.method == 'POST':
        form = CostumerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f'Cliente "{customer.com_name}" creado exitosamente.')
            return redirect('customers_list')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        form = CostumerForm()

    context = {
        'form': form,
        'title': 'Crear cliente',
        'is_create': True
    }
    return render(request, 'customers/form.html', context)