# projects/views/logis/autocomplete.py
from django.http import JsonResponse
from projects.models import Supplier, Product

# 🔹 Buscar proveedores
def autocomplete_supplier(request):
    term = request.GET.get("term", "")
    suppliers = Supplier.objects.filter(name_supplier__icontains=term)[:10]
    results = [
        {"id": s.ruc_supplier, "label": s.name_supplier, "ruc": s.ruc_supplier}
        for s in suppliers
    ]
    return JsonResponse(results, safe=False)


# 🔹 Buscar productos
def autocomplete_product(request):
    term = request.GET.get("term", "")
    products = Product.objects.filter(description__icontains=term)[:10]
    results = [
        {
            "id": p.id,
            "label": p.description,
            "part_number": p.part_number,
            "manufacturer": p.manufacturer,
        }
        for p in products
    ]
    return JsonResponse(results, safe=False)
