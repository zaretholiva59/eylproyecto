from django.shortcuts import get_object_or_404, render
from django.db.models import Count, Sum, Q, Prefetch
from projects.models.costumer import Costumer
from projects.models.projects import Projects
from projects.models.chance import Chance
from projects.models.client_invoice import ClientInvoice
from projects.models.oc import PurchaseOrder

def customer_detail(request, ruc):
    # Obtener el cliente o devolver 404 si no existe
    customer = get_object_or_404(Costumer, pk=ruc)
    
    # Query optimizada con anotaciones y prefetch
    # Relación correcta: Projects → cod_projects (Chance) → info_costumer
    related_projects = Projects.objects.filter(
        cod_projects__info_costumer=customer
    ).annotate(
        # Cuenta cuántas órdenes de compra tiene cada proyecto
        purchase_orders_count=Count('purchaseorder', distinct=True),
        # Cuenta cuántas facturas de venta tiene cada proyecto
        client_invoices_count=Count('client_invoices', distinct=True)
    ).prefetch_related(
        # Carga las órdenes de compra relacionadas
        'purchaseorder_set',
        # Carga las facturas de venta relacionadas
        'client_invoices'
    ).select_related(
        # Carga la información de la oportunidad sin hacer otra query
        'cod_projects'
    )
    
    # Obtener conteos adicionales del cliente
    customer_stats = {
        # Cuenta total de oportunidades del cliente (se elimina Presale)
        'total_chances': Chance.objects.filter(info_costumer=customer).count(),
        # Cuenta total de proyectos del cliente
        'total_projects': related_projects.count(),
        # Suma el total facturado al cliente (usando IDs de proyectos relacionados)
        'total_invoiced': ClientInvoice.objects.filter(
            project__in=related_projects.values('cod_projects')
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0
    }
    
    # Obtener listados limitados para mostrar en la página
    # Últimas "preventas" ahora se sirven desde Chance para mantener la sección
    latest_presales = Chance.objects.filter(
        info_costumer=customer
    ).order_by('-regis_date')[:5]

    latest_chances = Chance.objects.filter(
        info_costumer=customer
    ).order_by('-regis_date')[:5]
    
    # Renderizar la plantilla con todos los datos
    return render(request, 'customers/detail.html', {
        'customer': customer,
        'projects': related_projects,
        'customer_stats': customer_stats,
        'latest_presales': latest_presales,
        'latest_chances': latest_chances,
    })