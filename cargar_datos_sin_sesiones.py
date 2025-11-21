"""
Script para cargar datos desde JSON excluyendo sesiones
"""

import json
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core.management import call_command
from io import StringIO
import sys

def cargar_datos_sin_sesiones(archivo_json):
    """
    Carga datos desde JSON excluyendo sesiones
    """
    print(f"[*] Leyendo {archivo_json}...")
    
    # Leer JSON
    with open(archivo_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"[OK] JSON cargado: {len(data)} registros")
    
    # Filtrar sesiones y corregir valores null en bank_reference
    data_filtrado = []
    for item in data:
        if item.get('model') == 'sessions.session':
            continue
        
        # Corregir bank_reference: cambiar null a string vacío
        if item.get('model') == 'projects.clientinvoice':
            fields = item.get('fields', {})
            if fields.get('bank_reference') is None:
                fields['bank_reference'] = ''
        
        data_filtrado.append(item)
    
    sesiones_eliminadas = len(data) - len(data_filtrado)
    print(f"[OK] Sesiones eliminadas: {sesiones_eliminadas}")
    print(f"[OK] Registros restantes: {len(data_filtrado)}")
    
    # Guardar JSON temporal sin sesiones
    archivo_temp = archivo_json.replace('.json', '_sin_sesiones.json')
    with open(archivo_temp, 'w', encoding='utf-8') as f:
        json.dump(data_filtrado, f, ensure_ascii=False, indent=4)
    
    print(f"[*] Guardando JSON temporal: {archivo_temp}")
    
    # Cargar datos
    print(f"\n[*] Cargando datos en la base de datos...")
    try:
        # Capturar salida
        out = StringIO()
        err = StringIO()
        
        call_command('loaddata', archivo_temp, stdout=out, stderr=err)
        
        salida = out.getvalue()
        errores = err.getvalue()
        
        if salida:
            print(salida)
        if errores and 'Traceback' in errores:
            print(f"[ERROR] {errores}")
            return False
        elif errores:
            print(f"[WARN] {errores}")
        
        print(f"[OK] Datos cargados exitosamente!")
        
        # Limpiar archivo temporal
        if os.path.exists(archivo_temp):
            os.remove(archivo_temp)
            print(f"[OK] Archivo temporal eliminado")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error al cargar datos: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    archivo_json = 'datos_eyl_corregido.json'
    
    if len(sys.argv) > 1:
        archivo_json = sys.argv[1]
    
    print("=" * 60)
    print("CARGA DE DATOS SIN SESIONES")
    print("=" * 60)
    print(f"Archivo: {archivo_json}")
    print("=" * 60)
    
    exito = cargar_datos_sin_sesiones(archivo_json)
    
    if exito:
        print("\n" + "=" * 60)
        print("[OK] CARGA COMPLETADA EXITOSAMENTE")
        print("=" * 60)
        
        # Verificar datos cargados
        from projects.models import Projects, PurchaseOrder, Costumer
        from tasks.models import Task
        
        print(f"\nDatos en la base de datos:")
        print(f"  - Proyectos: {Projects.objects.count()}")
        print(f"  - Clientes: {Costumer.objects.count()}")
        print(f"  - Purchase Orders: {PurchaseOrder.objects.count()}")
        print(f"  - Tareas: {Task.objects.count()}")
        print("=" * 60)
    else:
        print("\n[ERROR] ERROR EN LA CARGA")
        sys.exit(1)

