#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def analizar_modelo(model_class, name):
    """Analiza el uso de un modelo específico"""
    try:
        count = model_class.objects.count()
        print(f"\n📊 {name}")
        print(f"   Total registros: {count}")
        
        if count > 0:
            # Mostrar últimos 3 registros
            latest = model_class.objects.all().order_by('-id')[:3]
            print("   Últimos registros:")
            for i, obj in enumerate(latest, 1):
                print(f"   {i}. {obj}")
                # Si tiene created_at o similar
                if hasattr(obj, 'created_at'):
                    print(f"      Creado: {obj.created_at}")
        else:
            print("   ❌ SIN REGISTROS")
            
        return count
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return 0

# Importar modelos
from projects.models import *

print("🔍 ANÁLISIS DE USO DE MODELOS")
print("="*50)

# Análisis por módulos
print("\n🏗️ MÓDULO PMI/PROYECTOS:")
total_proyectos = analizar_modelo(Projects, "Projects")
analizar_modelo(ProjectActivity, "ProjectActivity")
analizar_modelo(ProjectProgress, "ProjectProgress")

print("\n💼 MÓDULO COMERCIAL:")
analizar_modelo(Chance, "Chance")
analizar_modelo(Costumer, "Costumer")

print("\n📋 MÓDULO LOGÍSTICA:")
analizar_modelo(PurchaseOrder, "PurchaseOrder")
analizar_modelo(PODetailProduct, "PODetailProduct")
analizar_modelo(Product, "Product")
analizar_modelo(Supplier, "Supplier")

print("\n💰 MÓDULO CONTABILIDAD:")
analizar_modelo(Invoice, "Invoice")
analizar_modelo(ClientInvoice, "ClientInvoice")

# Billing - cuidado con duplicados
try:
    from projects.models.billing import Billing as Billing1
    print("\n💳 BILLING (billing.py - costos):")
    analizar_modelo(Billing1, "Billing (costos)")
except: 
    print("❌ Billing (costos) no disponible")

try:
    from projects.models.billin import Billing as Billing2
    print("\n💳 BILLING (billin.py - pagos):")
    analizar_modelo(Billing2, "Billing (pagos)")
except:
    print("❌ Billing (pagos) no disponible")

print(f"\n📈 RESUMEN:")
print(f"   Total proyectos: {total_proyectos}")
if total_proyectos == 0:
    print("   🚨 ¡NO HAY PROYECTOS! El sistema está VACÍO")
else:
    print("   ✅ Hay proyectos activos")