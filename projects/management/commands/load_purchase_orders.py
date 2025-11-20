#!/usr/bin/env python
"""
Comando Django para cargar órdenes de compra desde CSV
Orden: 4 (Después de clientes, proveedores y projects)
"""

import csv
import os
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from projects.models import PurchaseOrder, Chance

class Command(BaseCommand):
    help = 'Carga órdenes de compra desde archivo CSV (Orden: 4)'

    def add_arguments(self, parser):
        parser.add_argument('archivo_csv', type=str, help='Archivo CSV con datos de órdenes de compra')

    def handle(self, *args, **options):
        archivo_csv = options['archivo_csv']
        
        if not os.path.exists(archivo_csv):
            raise CommandError(f'Archivo no encontrado: {archivo_csv}')
        
        self.stdout.write(self.style.WARNING(f'📊 Cargando órdenes de compra desde: {archivo_csv}'))
        
        ocs_creadas = 0
        ocs_existentes = 0
        errores = 0
        projects_no_encontrados = 0
        
        with open(archivo_csv, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    # Limpiar y validar datos
                    po_number = str(row.get('po_number', '')).strip()
                    project_code = str(row.get('project_code', '')).strip()
                    issue_date_str = str(row.get('issue_date', '')).strip()
                    currency = str(row.get('currency', 'USD')).strip().upper()
                    
                    # Exchange rate
                    exchange_rate_str = str(row.get('exchange_rate', '1.0')).strip()
                    try:
                        exchange_rate = float(exchange_rate_str)
                    except:
                        exchange_rate = 1.0
                    
                    local_import = str(row.get('local_import', 'local')).strip().lower()
                    
                    if not po_number or not project_code:
                        self.stdout.write(self.style.WARNING(f'⚠️  Fila {row_num}: PO Number o Project Code faltante'))
                        errores += 1
                        continue
                    
                    # Parsear fecha
                    try:
                        issue_date = datetime.strptime(issue_date_str, '%Y-%m-%d').date()
                    except:
                        issue_date = datetime.now().date()
                    
                    # Buscar project (Chance)
                    try:
                        project = Chance.objects.get(cod_chance=project_code)
                    except Chance.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f'❌ Project no encontrado: {project_code}'))
                        projects_no_encontrados += 1
                        continue
                    
                    # Crear o actualizar Purchase Order
                    po, creado = PurchaseOrder.objects.get_or_create(
                        po_number=po_number,
                        defaults={
                            'project': project,
                            'issue_date': issue_date,
                            'currency': currency,
                            'exchange_rate': exchange_rate,
                            'local_import': local_import,
                            'status': 'pendiente'  # Estado por defecto
                        }
                    )
                    
                    if creado:
                        ocs_creadas += 1
                        self.stdout.write(self.style.SUCCESS(f'✅ OC creada: {po_number} - Project: {project_code}'))
                    else:
                        ocs_existentes += 1
                        # Actualizar datos si es necesario
                        actualizado = False
                        if po.project.cod_chance != project_code:
                            # Buscar nuevo project
                            try:
                                nuevo_project = Chance.objects.get(cod_chance=project_code)
                                po.project = nuevo_project
                                actualizado = True
                            except Chance.DoesNotExist:
                                self.stdout.write(self.style.ERROR(f'❌ Nuevo project no encontrado: {project_code}'))
                                continue
                        
                        if po.currency != currency:
                            po.currency = currency
                            actualizado = True
                        if po.exchange_rate != exchange_rate:
                            po.exchange_rate = exchange_rate
                            actualizado = True
                        if po.local_import != local_import:
                            po.local_import = local_import
                            actualizado = True
                        
                        if actualizado:
                            po.save()
                            self.stdout.write(self.style.WARNING(f'⚠️  OC actualizada: {po_number}'))
                        else:
                            self.stdout.write(self.style.WARNING(f'⚠️  OC existente: {po_number}'))
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Error fila {row_num}: {str(e)}'))
                    errores += 1
        
        # Resumen
        self.stdout.write(self.style.SUCCESS(f"\n📈 RESUMEN DE CARGA DE ÓRDENES DE COMPRA:"))
        self.stdout.write(self.style.SUCCESS(f"✅ Creadas: {ocs_creadas}"))
        self.stdout.write(self.style.SUCCESS(f"⚠️  Existentes: {ocs_existentes}"))
        if projects_no_encontrados > 0:
            self.stdout.write(self.style.ERROR(f"❌ Projects no encontrados: {projects_no_encontrados}"))
        if errores > 0:
            self.stdout.write(self.style.ERROR(f"❌ Errores: {errores}"))
        
        self.stdout.write(self.style.WARNING(f"\n🎯 SIGUIENTE PASO: Cargar detalles de productos con:"))
        self.stdout.write(self.style.WARNING(f"python manage.py load_po_details po_details.csv"))