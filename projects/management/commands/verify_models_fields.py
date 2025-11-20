from django.core.management.base import BaseCommand
from django.apps import apps


class Command(BaseCommand):
    help = "Verifica y lista campos reales de Supplier, Product y PODetailProduct"

    def handle(self, *args, **options):
        models_to_check = [
            ('projects', 'Supplier'),
            ('projects', 'Product'),
            ('projects', 'PODetailProduct'),
        ]

        self.stdout.write("\n🔍 VERIFICACIÓN DE MODELOS Y CAMPOS")
        self.stdout.write("=" * 80)

        for app_label, model_name in models_to_check:
            model = apps.get_model(app_label, model_name)
            fields = model._meta.get_fields()
            self.stdout.write(f"\n📦 Modelo: {app_label}.{model_name}")
            self.stdout.write("Campos:")
            for f in fields:
                # Mostrar nombre y tipo
                try:
                    field_type = f.__class__.__name__
                except Exception:
                    field_type = type(f).__name__
                # Indicar FK si aplica
                rel = ''
                if hasattr(f, 'remote_field') and f.remote_field:
                    rel = f" → FK a {f.remote_field.model.__name__}"
                self.stdout.write(f"  • {f.name} ({field_type}){rel}")

        self.stdout.write("\n❗ Comprobación de campo inexistente 'total_price' en PODetailProduct:")
        podetail_cls = apps.get_model('projects', 'PODetailProduct')
        has_total_price = any(f.name == 'total_price' for f in podetail_cls._meta.get_fields())
        if has_total_price:
            self.stdout.write("  ⚠️ Encontrado 'total_price' (esto no debería estar)")
        else:
            self.stdout.write("  ✅ 'total_price' NO existe. Use 'total' o 'subtotal' según corresponda.")

        # Resumen útil
        self.stdout.write("\n✅ Verificación completada. Use estos nombres exactos en sus scripts.")