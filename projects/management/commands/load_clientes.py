#!/usr/bin/env python
"""
Comando Django para cargar clientes desde CSV
Orden: 1 (Primero)
"""

import csv
import os
from django.core.management.base import BaseCommand, CommandError
from projects.models import Costumer

class Command(BaseCommand):
    help = 'Carga clientes desde archivo CSV (Orden: 1)'

    def add_arguments(self, parser):
        parser.add_argument('archivo_csv', type=str, help='Archivo CSV con datos de clientes')

    def handle(self, *args, **options):
        archivo_csv = options['archivo_csv']
        
        if not os.path.exists(archivo_csv):
            raise CommandError(f'Archivo no encontrado: {archivo_csv}')
        
        self.stdout.write(self.style.WARNING(f'📊 Cargando clientes desde: {archivo_csv}'))
        
        clientes_creados = 0
        clientes_existentes = 0
        errores = 0
        
        with open(archivo_csv, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    # Limpiar y validar datos
                    ruc = str(row.get('ruc_costumer', '')).strip()
                    nombre = str(row.get('com_name', '')).strip()
                    contacto = str(row.get('contac_costumer', '')).strip()
                    
                    if not ruc or not nombre:
                        self.stdout.write(self.style.WARNING(f'⚠️  Fila {row_num}: RUC o Nombre faltante'))
                        errores += 1
                        continue
                    
                    # Verificar si ya existe
                    cliente, creado = Costumer.objects.get_or_create(
                        ruc_costumer=ruc,
                        defaults={
                            'com_name': nombre,
                            'contac_costumer': contacto
                        }
                    )
                    
                    if creado:
                        clientes_creados += 1
                        self.stdout.write(self.style.SUCCESS(f'✅ Cliente creado: {nombre}'))
                    else:
                        clientes_existentes += 1
                        # Actualizar datos si es necesario
                        if contacto and cliente.contac_costumer != contacto:
                            cliente.contac_costumer = contacto
                            cliente.save()
                        self.stdout.write(self.style.WARNING(f'⚠️  Cliente existente: {nombre}'))
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Error fila {row_num}: {str(e)}'))
                    errores += 1
        
        # Resumen
        self.stdout.write(self.style.SUCCESS(f"\n📈 RESUMEN DE CARGA DE CLIENTES:"))
        self.stdout.write(self.style.SUCCESS(f"✅ Creados: {clientes_creados}"))
        self.stdout.write(self.style.SUCCESS(f"⚠️  Existentes: {clientes_existentes}"))
        if errores > 0:
            self.stdout.write(self.style.ERROR(f"❌ Errores: {errores}"))
        
        self.stdout.write(self.style.WARNING(f"\n🎯 SIGUIENTE PASO: Cargar proveedores con:"))
        self.stdout.write(self.style.WARNING(f"python manage.py load_suppliers suppliers.csv"))