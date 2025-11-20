#!/usr/bin/env python
"""
Comando Django para cargar proveedores desde CSV
Orden: 2 (Después de clientes)
"""

import csv
import os
from django.core.management.base import BaseCommand, CommandError
from projects.models import Supplier

class Command(BaseCommand):
    help = 'Carga proveedores desde archivo CSV (Orden: 2)'

    def add_arguments(self, parser):
        parser.add_argument('archivo_csv', type=str, help='Archivo CSV con datos de proveedores')

    def handle(self, *args, **options):
        archivo_csv = options['archivo_csv']
        
        if not os.path.exists(archivo_csv):
            raise CommandError(f'Archivo no encontrado: {archivo_csv}')
        
        self.stdout.write(self.style.WARNING(f'📊 Cargando proveedores desde: {archivo_csv}'))
        
        proveedores_creados = 0
        proveedores_existentes = 0
        errores = 0
        
        with open(archivo_csv, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    # Limpiar y validar datos
                    ruc = str(row.get('ruc_supplier', '')).strip()
                    nombre = str(row.get('name_supplier', '')).strip()
                    direccion = str(row.get('address_supplier', 'Dirección no especificada')).strip()
                    
                    if not ruc or not nombre:
                        self.stdout.write(self.style.WARNING(f'⚠️  Fila {row_num}: RUC o Nombre faltante'))
                        errores += 1
                        continue
                    
                    # Verificar si ya existe
                    proveedor, creado = Supplier.objects.get_or_create(
                        ruc_supplier=ruc,
                        defaults={
                            'name_supplier': nombre,
                            'address_supplier': direccion
                        }
                    )
                    
                    if creado:
                        proveedores_creados += 1
                        self.stdout.write(self.style.SUCCESS(f'✅ Proveedor creado: {nombre}'))
                    else:
                        proveedores_existentes += 1
                        # Actualizar datos si es necesario
                        if direccion != 'Dirección no especificada' and proveedor.address_supplier != direccion:
                            proveedor.address_supplier = direccion
                            proveedor.save()
                        self.stdout.write(self.style.WARNING(f'⚠️  Proveedor existente: {nombre}'))
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Error fila {row_num}: {str(e)}'))
                    errores += 1
        
        # Resumen
        self.stdout.write(self.style.SUCCESS(f"\n📈 RESUMEN DE CARGA DE PROVEEDORES:"))
        self.stdout.write(self.style.SUCCESS(f"✅ Creados: {proveedores_creados}"))
        self.stdout.write(self.style.SUCCESS(f"⚠️  Existentes: {proveedores_existentes}"))
        if errores > 0:
            self.stdout.write(self.style.ERROR(f"❌ Errores: {errores}"))
        
        self.stdout.write(self.style.WARNING(f"\n🎯 SIGUIENTE PASO: Cargar projects con:"))
        self.stdout.write(self.style.WARNING(f"python manage.py load_projects projects.csv"))