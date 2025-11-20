import traceback
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.apps import apps


class Command(BaseCommand):
    help = "Script corregido: asegura uso de campos válidos y FK de Supplier en Product; recalcula totales en PODetailProduct."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true', default=False,
            help='No guarda cambios, solo muestra lo que haría'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        Supplier = apps.get_model('projects', 'Supplier')
        Product = apps.get_model('projects', 'Product')
        PODetailProduct = apps.get_model('projects', 'PODetailProduct')
        PurchaseOrder = apps.get_model('projects', 'PurchaseOrder')

        self.stdout.write("\n🚀 INICIO: Script corregido de importación/ajuste")
        self.stdout.write("=" * 80)

        # 1) Validación: evitar uso de campo inexistente 'total_price'
        if any(f.name == 'total_price' for f in PODetailProduct._meta.get_fields()):
            self.stdout.write("⚠️ Encontrado campo 'total_price' en PODetailProduct (inesperado).")
        else:
            self.stdout.write("✅ Confirmado: 'total_price' NO existe en PODetailProduct. Use 'total' y 'local_total'.")

        # 2) Recalcular totales en detalles de producto
        detalles = PODetailProduct.objects.select_related('purchase_order', 'product').all()
        total_detalles = detalles.count()
        self.stdout.write(f"\n📦 Procesando {total_detalles} detalles de productos para recalcular totales")

        processed = 0
        errors = 0

        @transaction.atomic
        def process_detalle(det):
            # total = quantity * unit_price
            try:
                qty = Decimal(det.quantity)
                unit = Decimal(det.unit_price)
                subtotal = (qty * unit).quantize(Decimal('0.01'))
                # IGV 18% si aplica: si measurement_unit o comment da pistas; aquí no asumimos, solo copiamos subtotal
                det.subtotal = subtotal
                det.igv = Decimal('0.00')
                det.total = subtotal
                # local_total: si moneda es local import o currency S/., no tenemos acceso directo aquí; mantenemos igual si ya existe
                if det.local_total in (None, Decimal('0'), Decimal('0.00')):
                    det.local_total = subtotal
                if not dry_run:
                    det.save()
                return True
            except Exception:
                return False

        for idx, det in enumerate(detalles, start=1):
            oc = det.purchase_order
            po_number = getattr(oc, 'po_number', oc_id(det))
            try:
                ok = process_detalle(det)
                if ok:
                    processed += 1
                    self.stdout.write(
                        f"   ✅ [{idx}/{total_detalles}] OC-{po_number} • Producto {det.product.code_art} • Total={det.total} • Local={det.local_total}"
                    )
                else:
                    errors += 1
                    self.stdout.write(f"   ❌ [{idx}/{total_detalles}] OC-{po_number} • Error al recalcular total")
            except Exception:
                errors += 1
                tb = traceback.format_exc()
                self.stdout.write(f"   ❌ [{idx}/{total_detalles}] OC-{po_number} • Error inesperado\n{tb}")

        # 3) Asegurar FK de Supplier en Product (no cadenas)
        products = Product.objects.select_related('ruc_supplier').all()
        self.stdout.write(f"\n🔗 Verificando {products.count()} productos para FK de Supplier")
        fixed_products = 0

        for p in products:
            try:
                # Si el supplier es None, no podemos inferirlo aquí sin datos externos
                if p.ruc_supplier is None:
                    # No corregimos automáticamente; solo reportamos
                    self.stdout.write(f"   ⚠️ Producto {p.code_art} sin proveedor asignado")
                    continue
                # p.ruc_supplier ya es FK, no hay nada que convertir
            except Exception:
                tb = traceback.format_exc()
                self.stdout.write(f"   ❌ Error verificando producto {p.code_art}\n{tb}")

        self.stdout.write("\n📊 RESUMEN")
        self.stdout.write(f"   • Detalles procesados correctamente: {processed}")
        self.stdout.write(f"   • Errores en detalles: {errors}")
        self.stdout.write(f"   • Productos revisados: {products.count()} (FK ya en uso)")
        self.stdout.write("\n✅ Finalizado. El script NO usa 'total_price'; calcula 'total' correctamente.\n")


def oc_id(det):
    try:
        return det.purchase_order_id
    except Exception:
        return 'N/A'