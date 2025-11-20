from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q
from projects.models.costumer import Costumer


def customers_list(request):
    # Get search query and filters
    search_query = request.GET.get('search', '')
    customer_type = request.GET.get('type', '')
    
    # Base queryset
    customers = Costumer.objects.all()
    
    # Apply search filter
    if search_query:
        customers = customers.filter(
            Q(ruc_costumer__icontains=search_query) |
            Q(com_name__icontains=search_query) |
            Q(contac_costumer__icontains=search_query)
        )
    
    # Apply type filter
    if customer_type:
        customers = customers.filter(type_costumer=customer_type)
    
    # Order results
    customers = customers.order_by('com_name')
    
    # Pagination
    paginator = Paginator(customers, 10)  # 10 customers per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get customer type choices for filter dropdown
    customer_types = Costumer._meta.get_field('type_costumer').choices
    
    return render(request, 'customers/list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'customer_type': customer_type,
        'customer_types': customer_types,
        'total_customers': customers.count(),
    })