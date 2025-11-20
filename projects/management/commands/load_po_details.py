#!/usr/bin/env python
"""
Comando Django para cargar detalles de productos desde CSV
Orden: 5 (Último - después de todo lo demás)
"""

import csv
import os
from django.core.management.base import BaseCommand, CommandError
from projects.models import PurchaseOrder, PODetailProduct, Product

class Command(BaseCommand):
    help = 'Carga detalles de productos desde archivo CSV (Orden: 5 - Último)'

    def add_arguments(self, parser):
        parser.add_argument('archivo_csv', type=str, help='Archivo CSV con detalles de productos')

    def handle(self, *args, **options):
        archivo_csv = options['archivo_csv']
        
        if not os.path.exists(archivo_csv):
            raise CommandError(f'Archivo no encontrado: {archivo_csv}')
        
        self.stdout.write(self.style.WARNING(f'📊 Cargando detalles de productos desde: {archivo_csv}'))
        
        detalles_creados = 0
        detalles_existentes = 0
        errores = 0
        pos_no_encontradas = 0
        
        with open(archivo_csv, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    # Limpiar y validar datos
                    po_number = str(row.get('purchase_order', '')).strip()
                    product_name = str(row.get('product_name', '')).strip()
                    quantity_str = str(row.get('quantity', '1')).strip()
                    unit_price_str = str(row.get('unit_price', '0')).strip()
                    measurement_unit = str(row.get('measurement_unit', 'unit')).strip()
                    currency = str(row.get('currency', 'USD')).strip().upper()
                    
                    if not po_number or not product_name:
                        self.stdout.write(self.style.WARNING(f'⚠️  Fila {row_num}: PO Number o Product Name faltante'))
                        errores += 1
                        continue
                    
                    # Parsear cantidad y precio
                    try:
                        quantity = float(quantity_str)
                    except:
                        quantity = 1.0
                    
                    try:
                        unit_price = float(unit_price_str)
                    except:
                        unit_price = 0.0
                    
                    # Buscar Purchase Order
                    try:
                        po = PurchaseOrder.objects.get(po_number=po_number)
                    except PurchaseOrder.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f'❌ Purchase Order no encontrada: {po_number}'))
                        pos_no_encontradas += 1
                        continue
                    
                    # Buscar o crear Product
                    product, product_creado = Product.objects.get_or_create(
                        name_product=product_name,
                        defaults={
                            'code_product': product_name[:20].upper().replace(' ', '_'),
                            'measurement_unit': measurement_unit
                        }
                    )
                    
                    if product_creado:
                        self.stdout.write(self.style.SUCCESS(f'✅ Producto creado: {product_name}'))
                    
                    # Crear o actualizar detalle
                    detalle, creado = PODetailProduct.objects.get_or_create(
                        purchase_order=po,
                        product=product,
                        defaults={
                            'quantity': quantity,
                            'unit_price': unit_price,
                            'measurement_unit': measurement_unit,
                            'currency': currency
                        }
                    )
                    
                    if creado:
                        detalles_creados += 1
                        self.stdout.write(self.style.SUCCESS(f'✅ Detalle creado: {product_name} en OC {po_number}'))
                    else:
                        detalles_existentes += 1
                        # Actualizar si es necesario
                        actualizado = False
                        if detalle.quantity != quantity:
                            detalle.quantity = quantity
                            actualizado = True
                        if detalle.unit_price != unit_price:
                            detalle.unit_price = unit_price
                            actualizado = True
                        if detalle.measurement_unit != measurement_unit:
                            detalle.measurement_unit = measurement_unit
                            actualizado = True
                        if detalle.currency != currency:
                            detalle.currency = currency
                            actualizado = True
                        
                        if actualizado:
                            detalle.save()
                            self.stdout.write(self.style.WARNING(f'⚠️  Detalle actualizado: {product_name} en OC {po_number}'))
                        else:
                            self.stdout.write(self.style.WARNING(f'⚠️  Detalle existente: {product_name} en OC {po_number}'))
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Error fila {row_num}: {str(e)}'))
                    errores += 1
        
        # Resumen
        self.stdout.write(self.style.SUCCESS(f"\n📈 RESUMEN DE CARGA DE DETALLES:"))
        self.stdout.write(self.style.SUCCESS(f"✅ Creados: {detalles_creados}"))
        self.stdout.write(self.style.SUCCESS(f"⚠️  Existentes: {detalles_existentes}"))
        if pos_no_encontradas > 0:
            self.stdout.write(self.style.ERROR(f"❌ Purchase Orders no encontradas: {pos_no_encontradas}"))
        if errores > 0:
            self.stdout.write(self.style.ERROR(f"❌ Errores: {errores}"))
        
        # Calcular totales automáticamente
        self.stdout.write(self.style.WARNING(f"\n🧮 ACTUALIZANDO TOTALES DE ÓRDENES DE COMPRA..."))
        total_pos_actualizadas = 0
        
        for po in PurchaseOrder.objects.all():
            total_anterior = po.total_amount or 0
            total_nuevo = 0
            
            for detalle in po.podetailproduct_set.all():
                subtotal = detalle.quantity * detalle.unit_price
                total_nuevo += subtotal
            
            if total_anterior != total_nuevo:
                po.total_amount = total_nuevo
                po.save()
                total_pos_actualizadas += 1
        
        self.stdout.write(self.style.SUCCESS(f"✅ Totales actualizados en {total_pos_actualizadas} órdenes de compra"))
        
        self.stdout.write(self.style.SUCCESS(f"\n🎉 ¡CARGA COMPLETA!"))
        self.stdout.write(self.style.SUCCESS(f"Todos los datos han sido cargados en orden jerárquico:"))
        self.stdout.write(self.style.SUCCESS(f"1. ✅ Clientes"))
        self.stdout.write(self.style.SUCCESS(f"2. ✅ Proveedores"))
        self.stdout.write(self.style.SUCCESS(f"3. ✅ Projects"))
        self.stdout.write(self.style.SUCCESS(f"4. ✅ Órdenes de Compra"))
        self.stdout.write(self.style.SUCCESS(f"5. ✅ Detalles de Productos"))
        
        self.stdout.write(self.style.WARNING(f"\n🎯 VERIFICA EN EL ADMIN:"))
        self.stdout.write(self.style.WARNING(f"Revisa que todo se haya cargado correctamente en /admin/"))