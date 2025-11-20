#!/usr/bin/env python
"""
Script para crear Chances faltantes basados en extra_cost_centers.
Cada código en extra_cost_centers debe ser un Chance independiente.
"""

import os
import django
import sys

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from projects.models import Chance, Projects, Costumer

def create_missing_chances():
    print("🔍 Buscando códigos faltantes en extra_cost_centers...")
    
    # Buscar todos los Chances que tengan datos en extra_cost_centers
    chances_con_extra = Chance.objects.filter(extra_cost_centers__isnull=False).exclude(extra_cost_centers=[])
    
    created_count = 0
    
    for chance in chances_con_extra:
        print(f"\\n📝 Procesando Chance: {chance.cod_projects}")
        print(f"   extra_cost_centers: {chance.extra_cost_centers}")
        
        # Procesar cada código en extra_cost_centers
        for codigo in chance.extra_cost_centers:
            if codigo and codigo.strip():  # Si el código no está vacío
                print(f"   Verificando código: {codigo}")
                
                # Verificar si ya existe un Chance con ese código
                if Chance.objects.filter(cod_projects=codigo).exists():
                    print(f"   ⚠️  Ya existe Chance con código {codigo}, saltando...")
                    continue
                
                try:
                    # Crear nuevo Chance con el código de extra_cost_centers
                    nuevo_chance = Chance.objects.create(
                        cod_projects=codigo,
                        info_costumer=chance.info_costumer,  # Usar el mismo cliente
                        staff_presale=chance.staff_presale,  # Usar el mismo staff
                        cost_center=codigo,  # ✅ El código es el centro de costo
                        com_exe=chance.com_exe,  # Usar el mismo com_exe
                        regis_date=chance.regis_date,  # Usar la misma fecha
                        dres_chance=f"{chance.dres_chance} - {codigo}",  # Descripción modificada
                        date_aprox_close=chance.date_aprox_close,  # Usar la misma fecha
                        currency=chance.currency,  # Usar la misma moneda
                        exchange_rate=chance.exchange_rate,  # Usar el mismo tipo de cambio
                        cost_aprox_chance=chance.cost_aprox_chance,  # Usar el mismo costo
                        material_cost=chance.material_cost,
                        labor_cost=chance.labor_cost,
                        subcontracted_cost=chance.subcontracted_cost,
                        overhead_cost=chance.overhead_cost,
                        estimated_duration=chance.estimated_duration,
                        extra_cost_centers=[]  # ✅ Vaciar extra_cost_centers
                    )
                    
                    print(f"   ✅ Creado nuevo Chance: {nuevo_chance.cod_projects}")
                    
                    # Crear el Projects correspondiente automáticamente (se crea con el save())
                    # El save() del Chance ya crea el Projects con cost_center = cod_projects
                    
                    created_count += 1
                    
                except Exception as e:
                    print(f"   ❌ Error al crear Chance {codigo}: {str(e)}")
    
    # Limpiar extra_cost_centers de los Chances originales (ya procesamos todos)
    for chance in chances_con_extra:
        chance.extra_cost_centers = []
        chance.save()
        print(f"   🧹 Limpiado extra_cost_centers de {chance.cod_projects}")
    
    print(f"\\n🎉 Proceso completado. {created_count} nuevos Chances creados.")

if __name__ == "__main__":
    create_missing_chances()