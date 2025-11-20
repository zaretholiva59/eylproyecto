#!/usr/bin/env python
"""
Script para corregir los datos de Chance:
1. Mover códigos de proyecto de extra_cost_centers a cod_projects
2. Actualizar los Projects correspondientes
"""

import os
import django
import sys

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from projects.models import Chance, Projects

def fix_chance_data():
    print("🔧 Corrigiendo datos de Chance...")
    
    # Buscar todos los Chances que tengan datos en extra_cost_centers
    chances_con_extra = Chance.objects.filter(extra_cost_centers__isnull=False).exclude(extra_cost_centers=[])
    
    print(f"📊 Encontrados {len(chances_con_extra)} Chances con extra_cost_centers")
    
    fixed_count = 0
    
    for chance in chances_con_extra:
        print(f"\\n📝 Procesando Chance actual: {chance.cod_projects}")
        print(f"   extra_cost_centers actual: {chance.extra_cost_centers}")
        
        if chance.extra_cost_centers and len(chance.extra_cost_centers) > 0:
            # Tomar el primer código de extra_cost_centers como el nuevo cod_projects
            nuevo_cod_projects = chance.extra_cost_centers[0]
            
            print(f"   Nuevo cod_projects será: {nuevo_cod_projects}")
            
            # Verificar si ya existe un Chance con ese código
            if Chance.objects.filter(cod_projects=nuevo_cod_projects).exists():
                print(f"   ⚠️  Ya existe un Chance con código {nuevo_cod_projects}, saltando...")
                continue
            
            # Guardar los datos antiguos
            cod_projects_antiguo = chance.cod_projects
            
            try:
                # 1. Actualizar el cod_projects del Chance
                # Como cod_projects es PK, necesitamos crear uno nuevo y eliminar el antiguo
                chance_nuevo = Chance.objects.create(
                    cod_projects=nuevo_cod_projects,
                    info_costumer=chance.info_costumer,
                    staff_presale=chance.staff_presale,
                    cost_center=nuevo_cod_projects,  # ✅ Usar el nuevo código como cost_center
                    com_exe=chance.com_exe,
                    regis_date=chance.regis_date,
                    dres_chance=chance.dres_chance,
                    date_aprox_close=chance.date_aprox_close,
                    currency=chance.currency,
                    exchange_rate=chance.exchange_rate,
                    cost_aprox_chance=chance.cost_aprox_chance,
                    material_cost=chance.material_cost,
                    labor_cost=chance.labor_cost,
                    subcontracted_cost=chance.subcontracted_cost,
                    overhead_cost=chance.overhead_cost,
                    estimated_duration=chance.estimated_duration,
                    extra_cost_centers=chance.extra_cost_centers[1:] if len(chance.extra_cost_centers) > 1 else []  # ✅ Quitar el primer elemento
                )
                
                print(f"   ✅ Creado nuevo Chance: {chance_nuevo.cod_projects}")
                
                # 2. Actualizar o crear el Projects correspondiente
                Projects.objects.update_or_create(
                    cod_projects=chance_nuevo,
                    defaults={
                        'state_projects': 'Planeado',
                        'cost_center': nuevo_cod_projects,  # ✅ Usar el nuevo código
                        'estimated_duration': chance_nuevo.estimated_duration
                    }
                )
                
                print(f"   ✅ Actualizado Projects con cost_center: {nuevo_cod_projects}")
                
                # 3. Eliminar el Chance antiguo
                chance.delete()
                print(f"   ✅ Eliminado Chance antiguo: {cod_projects_antiguo}")
                
                fixed_count += 1
                
            except Exception as e:
                print(f"   ❌ Error al procesar {cod_projects_antiguo}: {str(e)}")
    
    print(f"\\n🎉 Proceso completado. {fixed_count} Chances corregidos.")

if __name__ == "__main__":
    fix_chance_data()