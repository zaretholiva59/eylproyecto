#!/usr/bin/env python3
"""
SCRIPT MAESTRO: Carga jerárquica completa de datos
Ejecuta todos los comandos en el orden correcto
"""

import subprocess
import sys
import os
from datetime import datetime

def ejecutar_comando(comando, descripcion):
    """Ejecuta un comando y maneja errores"""
    print(f"\n{'='*60}")
    print(f"🚀 {descripcion}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(comando, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ ÉXITO: {descripcion}")
            if result.stdout:
                print("📊 Salida:")
                print(result.stdout)
            return True
        else:
            print(f"❌ ERROR: {descripcion}")
            if result.stderr:
                print("📛 Error:")
                print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ EXCEPCIÓN: {descripcion}")
        print(f"📛 Error: {str(e)}")
        return False

def verificar_archivos():
    """Verifica que existan todos los archivos necesarios"""
    archivos = [
        'clientes.csv',
        'suppliers.csv', 
        'projects.csv',
        'purchase_orders.csv',
        'po_details.csv'
    ]
    
    print("🔍 Verificando archivos CSV...")
    faltantes = []
    
    for archivo in archivos:
        if os.path.exists(archivo):
            size = os.path.getsize(archivo)
            print(f"✅ {archivo} - {size} bytes")
        else:
            print(f"❌ {archivo} - NO ENCONTRADO")
            faltantes.append(archivo)
    
    return len(faltantes) == 0, faltantes

def main():
    """Función principal"""
    print("🎯 INICIANDO CARGA JERÁRQUICA COMPLETA")
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Verificar archivos
    archivos_ok, faltantes = verificar_archivos()
    
    if not archivos_ok:
        print(f"\n❌ FALTAN ARCHIVOS: {', '.join(faltantes)}")
        print("📝 Asegúrate de haber ejecutado primero:")
        print("python separar_excel_jerarquia.py tu_archivo.xlsx")
        sys.exit(1)
    
    # Definir comandos en orden
    comandos = [
        {
            'comando': 'python manage.py load_clientes clientes.csv',
            'descripcion': 'PASO 1: Cargando CLIENTES'
        },
        {
            'comando': 'python manage.py load_suppliers suppliers.csv',
            'descripcion': 'PASO 2: Cargando PROVEEDORES'
        },
        {
            'comando': 'python manage.py load_projects projects.csv',
            'descripcion': 'PASO 3: Cargando PROJECTS'
        },
        {
            'comando': 'python manage.py load_purchase_orders purchase_orders.csv',
            'descripcion': 'PASO 4: Cargando ÓRDENES DE COMPRA'
        },
        {
            'comando': 'python manage.py load_po_details po_details.csv',
            'descripcion': 'PASO 5: Cargando DETALLES DE PRODUCTOS'
        }
    ]
    
    # Ejecutar comandos en orden
    exitos = 0
    errores = 0
    
    for cmd_info in comandos:
        exito = ejecutar_comando(cmd_info['comando'], cmd_info['descripcion'])
        
        if exito:
            exitos += 1
        else:
            errores += 1
            print(f"\n❌ SE DETIENE LA EJECUCIÓN POR ERROR EN: {cmd_info['descripcion']}")
            print("🛠️  Corrige el error antes de continuar")
            break
    
    # Resumen final
    print(f"\n{'='*60}")
    print("📊 RESUMEN FINAL DE CARGA")
    print(f"{'='*60}")
    print(f"✅ Pasos exitosos: {exitos}")
    print(f"❌ Pasos con error: {errores}")
    
    if errores == 0:
        print(f"\n🎉 ¡CARGA COMPLETA EXITOSA!")
        print(f"📅 Finalizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n🎯 VERIFICA EN EL ADMIN:")
        print(f"http://127.0.0.1:8000/admin/projects/")
        print(f"\n📊 AHORA PUEDES CARGAR DATOS DEL DASHBOARD:")
        print(f"python manage.py load_baseline baseline_template.csv")
        print(f"python manage.py load_activities activities_template.csv")
        print(f"python manage.py load_invoices invoices_template.csv")
    else:
        print(f"\n⚠️  CARGA INCOMPLETA - Corrige los errores y vuelve a ejecutar")
        print(f"Puedes ejecutar comandos individuales:")
        for i, cmd_info in enumerate(comandos, 1):
            print(f"{i}. {cmd_info['comando']}")

if __name__ == "__main__":
    main()