#!/usr/bin/env python
import os
import sys
from datetime import date, timedelta
from decimal import Decimal
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from projects.models import (
    Projects,
    Presale,
    PurchaseOrder,
    PODetailProduct,
    Product,
    Supplier,
)
from projects.models.presale import PresaleFlowService
from projects.services.earned_value.calculator import EarnedValueCalculator


def debug_project(project_id):
    """Muestra información básica del proyecto y sus enlaces Presale/Chance."""
    try:
        proyecto = Projects.objects.select_related('cod_projects', 'cod_projects__presale').get(cod_projects_id=project_id)

        print(f"✅ Proyecto encontrado: {proyecto}")
        print(f"   - cod_projects_id: {proyecto.cod_projects_id}")
        print(f"   - state_projects: {proyecto.state_projects}")
        dres_chance = getattr(proyecto.cod_projects, 'dres_chance', 'SIN NOMBRE')
        print(f"   - chance.dres_chance: '{dres_chance}'")
        if hasattr(proyecto.cod_projects, 'presale') and proyecto.cod_projects.presale:
            print(f"   - presale.job_name: '{proyecto.cod_projects.presale.job_name}'")
        else:
            print("   - presale: NO EXISTE")

        print("\n📋 Ejemplos de proyectos:")
        todos = Projects.objects.select_related('cod_projects', 'cod_projects__presale').all()[:10]
        for p in todos:
            dres = getattr(p.cod_projects, 'dres_chance', 'SIN NOMBRE')
            job_name = getattr(getattr(p.cod_projects, 'presale', None), 'job_name', '')
            print(f"   - {p.cod_projects_id}: dres_chance='{dres}' | job_name='{job_name}'")

    except Projects.DoesNotExist:
        print(f"❌ Proyecto {project_id} no encontrado")
        print("\n📋 Proyectos disponibles:")
        todos = Projects.objects.select_related('cod_projects').all()[:10]
        for p in todos:
            print(f"   - {p.cod_projects_id}: {getattr(p.cod_projects, 'dres_chance', 'SIN NOMBRE')}")


def seed_minimal_project_and_po():
    """Crea Presale → Chance → Projects, un Supplier/Product, una OC y detalle, luego imprime métricas EVM."""
    # 1) Crear Presale mínimo
    presale = Presale.objects.create(
        cost_center="CC-DEMO-001",
        job_name="DEMO-PMI",
        contract_amount=Decimal('25000.00'),
        total_cost=Decimal('20000.00'),
        material_cost=Decimal('8000.00'),
        labor_cost=Decimal('7000.00'),
        subcontracted_cost=Decimal('3000.00'),
        overhead_cost=Decimal('2000.00'),
        estimated_duration=6,
    )

    # 2) Flujo Presale → Chance → Projects
    PresaleFlowService.crear_flujo_completo(presale)
    project = Projects.objects.get(cod_projects_id=presale.chance.cod_projects)

    # 3) Crear Supplier y Product mínimos
    supplier, _ = Supplier.objects.get_or_create(
        ruc_supplier="20123456789",
        defaults={"name_supplier": "Proveedor Demo"}
    )

    product, _ = Product.objects.get_or_create(
        code_art="ART-001",
        defaults={
            "part_number": "PN-DEM-001",
            "descrip": "Producto de demostración",
            "ruc_supplier": supplier,
            "manufac": "MarcaDemo",
            "model": "ModeloX",
            "cost": Decimal('900.00'),
        }
    )

    # 4) Crear OC y un detalle
    po = PurchaseOrder.objects.create(
        po_number=f"PO-DEMO-{project.cod_projects_id}",
        project_code=project,
        issue_date=date.today(),
        initial_delivery_date=date.today() + timedelta(days=3),
        final_delivery_date=date.today() + timedelta(days=7),
        total_amount=Decimal('0.00'),
        currency='PEN',
        exchange_rate=Decimal('1.0000'),
        po_status='PENDIENTE',
        observations="OC de prueba para EVM",
        local_import='LOCAL',
        te=5,
        forma_pago='Transferencia',
        pagar_a='Proveedor Demo',
    )

    quantity = 5
    unit_price = Decimal('1000.00')
    subtotal = unit_price * quantity  # 5000.00
    igv = (subtotal * Decimal('0.18')).quantize(Decimal('0.01'))  # 900.00
    total = subtotal + igv  # 5900.00

    PODetailProduct.objects.create(
        purchase_order=po,
        product=product,
        product_name=product.descrip,
        comment="Detalle demo",
        subtotal=subtotal,
        igv=igv,
        quantity=quantity,
        measurement_unit='unidades',
        unit_price=unit_price,
        total=total,
        local_total=total,
    )

    # Actualizar total de la OC con el detalle
    po.total_amount = total
    po.save()

    # 5) Calcular EVM y mostrar
    evm = EarnedValueCalculator.calculate_earned_value(project.cod_projects_id)
    metrics = evm.get('metrics', {})
    curve = evm.get('curve_data', {})

    print(f"\n🎯 Proyecto DEMO listo: {project.cod_projects_id}")
    print(f"   - BAC: {evm.get('bac', 0)}")
    print(f"   - CPI: {metrics.get('cpi')} | SPI: {metrics.get('spi')}")
    print(f"   - PV último: {curve.get('pv', [])[-1] if curve.get('pv') else 0}")
    print(f"   - EV último: {curve.get('ev', [])[-1] if curve.get('ev') else 0}")
    print(f"   - AC último: {curve.get('ac', [])[-1] if curve.get('ac') else 0}")
    print("\n✅ URLs sugeridas para probar en el navegador:")
    print(f"   - Dashboard:        /dashboard/{project.cod_projects_id}/")
    print(f"   - Curva S:          /curva-s/{project.cod_projects_id}/")
    print(f"   - Actividades PMI:  /project/{project.cod_projects_id}/pmi-activities/")

    return project.cod_projects_id


def main():
    args = sys.argv[1:]
    if not args:
        print("Uso: python debug_project.py [seed | debug <PROJECT_ID>]")
        return

    if args[0] == 'seed':
        pid = seed_minimal_project_and_po()
        print(f"\n🔗 ID Proyecto creado: {pid}")
    elif args[0] == 'debug' and len(args) >= 2:
        debug_project(args[1])
    else:
        print("Uso: python debug_project.py [seed | debug <PROJECT_ID>]")


if __name__ == "__main__":
    main()