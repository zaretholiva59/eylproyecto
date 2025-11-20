#!/usr/bin/env python
"""
Comando Django para cargar projects desde CSV
Orden: 3 (Después de clientes y proveedores)
"""

import csv
import os
from django.core.management.base import BaseCommand, CommandError
from projects.models import Chance, Costumer

class Command(BaseCommand):
    help = 'Carga projects desde archivo CSV (Orden: 3) - Crea Chances que se convierten en Projects'

    def add_arguments(self, parser):
        parser.add_argument('archivo_csv', type=str, help='Archivo CSV con datos de projects')

    def handle(self, *args, **options):
        archivo_csv = options['archivo_csv']
        
        if not os.path.exists(archivo_csv):
            raise CommandError(f'Archivo no encontrado: {archivo_csv}')
        
        self.stdout.write(self.style.WARNING(f'📊 Cargando projects desde: {archivo_csv}'))
        
        projects_creados = 0
        projects_existentes = 0
        errores = 0
        clientes_no_encontrados = 0
        
        with open(archivo_csv, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    # Limpiar y validar datos
                    codigo = str(row.get('cod_projects', '')).strip()
                    cost_center = str(row.get('cost_center', '')).strip()
                    cliente_ruc = str(row.get('cliente_ruc', '')).strip()
                    descripcion = str(row.get('descripcion', 'Proyecto sin descripción')).strip()
                    
                    # Presupuesto - manejar diferentes formatos
                    presupuesto_str = str(row.get('presupuesto', '0')).strip()
                    try:
                        presupuesto = float(presupuesto_str.replace(',', '').replace('$', ''))
                    except:
                        presupuesto = 0
                    
                    if not codigo:
                        self.stdout.write(self.style.WARNING(f'⚠️  Fila {row_num}: Código de proyecto faltante'))
                        errores += 1
                        continue
                    
                    # Buscar cliente
                    try:
                        cliente = Costumer.objects.get(ruc_costumer=cliente_ruc)
                    except Costumer.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f'❌ Cliente no encontrado: {cliente_ruc}'))
                        clientes_no_encontrados += 1
                        continue
                    
                    # Crear o actualizar Chance (que se convierte en Project automáticamente)
                    chance, creado = Chance.objects.get_or_create(
                        cod_chance=codigo,
                        defaults={
                            'cost_center': cost_center,
                            'costumer': cliente,
                            'description': descripcion,
                            'budget': presupuesto,
                            'status': 'activo'  # Estado por defecto
                        }
                    )
                    
                    if creado:
                        projects_creados += 1
                        self.stdout.write(self.style.SUCCESS(f'✅ Project creado: {codigo} - {descripcion[:50]}...'))
                    else:
                        projects_existentes += 1
                        # Actualizar datos si es necesario
                        actualizado = False
                        if chance.cost_center != cost_center:
                            chance.cost_center = cost_center
                            actualizado = True
                        if chance.description != descripcion:
                            chance.description = descripcion
                            actualizado = True
                        if chance.budget != presupuesto:
                            chance.budget = presupuesto
                            actualizado = True
                        
                        if actualizado:
                            chance.save()
                            self.stdout.write(self.style.WARNING(f'⚠️  Project actualizado: {codigo}'))
                        else:
                            self.stdout.write(self.style.WARNING(f'⚠️  Project existente: {codigo}'))
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Error fila {row_num}: {str(e)}'))
                    errores += 1
        
        # Resumen
        self.stdout.write(self.style.SUCCESS(f"\n📈 RESUMEN DE CARGA DE PROJECTS:"))
        self.stdout.write(self.style.SUCCESS(f"✅ Creados: {projects_creados}"))
        self.stdout.write(self.style.SUCCESS(f"⚠️  Existentes: {projects_existentes}"))
        if clientes_no_encontrados > 0:
            self.stdout.write(self.style.ERROR(f"❌ Clientes no encontrados: {clientes_no_encontrados}"))
        if errores > 0:
            self.stdout.write(self.style.ERROR(f"❌ Errores: {errores}"))
        
        self.stdout.write(self.style.WARNING(f"\n🎯 SIGUIENTE PASO: Cargar órdenes de compra con:"))
        self.stdout.write(self.style.WARNING(f"python manage.py load_purchase_orders purchase_orders.csv"))