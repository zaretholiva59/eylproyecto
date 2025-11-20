#!/usr/bin/env python3
"""
Script para separar Excel mezclado en archivos CSV jerárquicos
Orden de carga:
1. Clientes
2. Proveedores  
3. Projects (Chances)
4. Órdenes de Compra
5. Detalles de Productos
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

def separar_excel_jerarquia(archivo_excel):
    """
    Separa archivo Excel mezclado en CSV jerárquicos
    """
    print(f"📊 Leyendo Excel: {archivo_excel}")
    
    # Leer Excel
    try:
        df = pd.read_excel(archivo_excel)
        print(f"✅ Excel leído: {len(df)} filas encontradas")
    except Exception as e:
        print(f"❌ Error leyendo Excel: {e}")
        return
    
    # Limpiar nombres de columnas (eliminar espacios y convertir a minúsculas)
    df.columns = df.columns.astype(str).str.strip().str.lower()

    # Si la mayoría de columnas son 'unnamed', intentar detectar automáticamente la fila de encabezados
    try:
        total_cols = len(df.columns)
        unnamed_count = sum([str(col).startswith('unnamed') for col in df.columns])
        if total_cols > 0 and unnamed_count / total_cols > 0.5:
            print("🔎 Encabezados no detectados correctamente. Intentando auto-detección de fila de encabezados...")
            df_no_header = pd.read_excel(archivo_excel, header=None)

            # Buscar fila candidata a encabezado en las primeras 10 filas
            expected_markers = {
                'cliente','solicitante','proveedor','ruc',
                'código de proyecto o negocio','codigo de proyecto',
                'código ceco','ceco',
                'n° de orden de compra','orden de compra','oc',
                'description','descripcion','producto',
                'cantidad','q','qty',
                'p.u.','precio unitario','unit_price',
                'moneda','currency',
                'fecha','fecha emision','f. emision de oc'
            }

            best_idx = None
            best_score = 0
            max_rows_to_check = min(10, len(df_no_header))
            for idx in range(max_rows_to_check):
                row_vals = df_no_header.iloc[idx].astype(str).str.strip().str.lower().tolist()
                score = sum(1 for v in row_vals if v in expected_markers)
                if score > best_score:
                    best_score = score
                    best_idx = idx

            # Si encontramos una fila con al menos 2 coincidencias, la usamos como encabezado
            if best_idx is not None and best_score >= 2:
                df = pd.read_excel(archivo_excel, header=best_idx)
                df.columns = df.columns.astype(str).str.strip().str.lower()
                print(f"✅ Encabezado detectado en fila {best_idx+1} con {best_score} coincidencias.")
            else:
                print("⚠️ No se pudo detectar fila de encabezados automáticamente. Usando encabezado por defecto.")
    except Exception as e:
        print(f"❌ Error en auto-detección de encabezados: {e}")

    print("📋 Columnas encontradas:", list(df.columns))
    
    # 1. EXTRAER CLIENTES ÚNICOS
    print("\n🏢 Extrayendo CLIENTES...")
    if 'cliente' in df.columns and 'solicitante' in df.columns:
        clientes = df[['cliente', 'solicitante']].drop_duplicates()
        clientes.columns = ['com_name', 'contac_costumer']
        
        # Generar RUC aleatorio si no existe (formato peruano)
        clientes['ruc_costumer'] = range(20123456789, 20123456789 + len(clientes))
        clientes['ruc_costumer'] = clientes['ruc_costumer'].astype(str)
        
        # Reordenar columnas
        clientes = clientes[['ruc_costumer', 'com_name', 'contac_costumer']]
        
        clientes.to_csv('clientes.csv', index=False)
        print(f"✅ clientes.csv creado: {len(clientes)} clientes únicos")
    else:
        print("⚠️  No se encontraron columnas 'cliente' y 'solicitante'")
    
    # 2. EXTRAER PROVEEDORES ÚNICOS
    print("\n🏭 Extrayendo PROVEEDORES...")
    if 'proveedor' in df.columns and 'ruc' in df.columns:
        proveedores = df[['proveedor', 'ruc']].drop_duplicates()
        proveedores.columns = ['name_supplier', 'ruc_supplier']
        
        # Agregar dirección genérica
        proveedores['address_supplier'] = 'Dirección ' + proveedores['name_supplier'].str[:20]
        
        # Reordenar columnas
        proveedores = proveedores[['ruc_supplier', 'name_supplier', 'address_supplier']]
        
        proveedores.to_csv('suppliers.csv', index=False)
        print(f"✅ suppliers.csv creado: {len(proveedores)} proveedores únicos")
    else:
        print("⚠️  No se encontraron columnas 'proveedor' y 'ruc'")
    
    # 3. EXTRAER PROJECTS ÚNICOS
    print("\n📋 Extrayendo PROJECTS...")
    project_cols = []
    # Variantes para código de proyecto
    if 'código de proyecto o negocio' in df.columns:
        project_cols.append('código de proyecto o negocio')
    elif 'codigo de proyecto o negocio' in df.columns:
        project_cols.append('codigo de proyecto o negocio')
    elif 'codigo de proyecto' in df.columns:
        project_cols.append('codigo de proyecto')
    elif 'project' in df.columns:
        project_cols.append('project')
    
    # Variantes para CECO
    if 'código ceco' in df.columns:
        project_cols.append('código ceco')
    elif 'codigo ceco' in df.columns:
        project_cols.append('codigo ceco')
    elif 'ceco' in df.columns:
        project_cols.append('ceco')
        
    if 'cliente' in df.columns:
        project_cols.append('cliente')
    
    if len(project_cols) >= 2:
        projects = df[project_cols].drop_duplicates()
        
        # Renombrar columnas
        col_mapping = {}
        if 'código de proyecto o negocio' in projects.columns:
            col_mapping['código de proyecto o negocio'] = 'cod_projects'
        elif 'codigo de proyecto o negocio' in projects.columns:
            col_mapping['codigo de proyecto o negocio'] = 'cod_projects'
        elif 'codigo de proyecto' in projects.columns:
            col_mapping['codigo de proyecto'] = 'cod_projects'
        elif 'project' in projects.columns:
            col_mapping['project'] = 'cod_projects'
            
        if 'código ceco' in projects.columns:
            col_mapping['código ceco'] = 'cost_center'
        elif 'codigo ceco' in projects.columns:
            col_mapping['codigo ceco'] = 'cost_center'
        elif 'ceco' in projects.columns:
            col_mapping['ceco'] = 'cost_center'
            
        if 'cliente' in projects.columns:
            col_mapping['cliente'] = 'cliente_ruc'
        
        projects = projects.rename(columns=col_mapping)
        
        # Agregar campos faltantes
        projects['descripcion'] = 'Proyecto ' + projects['cod_projects'].astype(str)
        projects['presupuesto'] = 50000  # Presupuesto genérico
        
        # Si falta cliente_ruc, usar RUC genérico
        if 'cliente_ruc' not in projects.columns:
            projects['cliente_ruc'] = '20123456789'
        
        # Reordenar columnas
        projects = projects[['cod_projects', 'cost_center', 'cliente_ruc', 'descripcion', 'presupuesto']]
        
        projects.to_csv('projects.csv', index=False)
        print(f"✅ projects.csv creado: {len(projects)} projects únicos")
    else:
        print("⚠️  No se encontraron suficientes columnas para projects")
    
    # 4. EXTRAER ÓRDENES DE COMPRA ÚNICAS
    print("\n📦 Extrayendo ÓRDENES DE COMPRA...")
    oc_cols = []
    if 'n° de orden de compra' in df.columns:
        oc_cols.append('n° de orden de compra')
    elif 'orden de compra' in df.columns:
        oc_cols.append('orden de compra')
    elif 'oc' in df.columns:
        oc_cols.append('oc')
        
    # Variantes para código de proyecto
    if 'código de proyecto o negocio' in df.columns:
        oc_cols.append('código de proyecto o negocio')
    elif 'codigo de proyecto o negocio' in df.columns:
        oc_cols.append('codigo de proyecto o negocio')
    elif 'codigo de proyecto' in df.columns:
        oc_cols.append('codigo de proyecto')
    elif 'project' in df.columns:
        oc_cols.append('project')
        
    if 'f. emision de oc' in df.columns:
        oc_cols.append('f. emision de oc')
    elif 'fecha emision' in df.columns:
        oc_cols.append('fecha emision')
    elif 'fecha' in df.columns:
        oc_cols.append('fecha')
    
    if len(oc_cols) >= 2:
        ocs = df[oc_cols].drop_duplicates()
        
        # Renombrar columnas
        col_mapping = {}
        if 'n° de orden de compra' in ocs.columns:
            col_mapping['n° de orden de compra'] = 'po_number'
        elif 'orden de compra' in ocs.columns:
            col_mapping['orden de compra'] = 'po_number'
        elif 'oc' in ocs.columns:
            col_mapping['oc'] = 'po_number'
            
        if 'código de proyecto o negocio' in ocs.columns:
            col_mapping['código de proyecto o negocio'] = 'project_code'
        elif 'codigo de proyecto o negocio' in ocs.columns:
            col_mapping['codigo de proyecto o negocio'] = 'project_code'
        elif 'codigo de proyecto' in ocs.columns:
            col_mapping['codigo de proyecto'] = 'project_code'
        elif 'project' in ocs.columns:
            col_mapping['project'] = 'project_code'
            
        if 'f. emision de oc' in ocs.columns:
            col_mapping['f. emision de oc'] = 'issue_date'
        elif 'fecha emision' in ocs.columns:
            col_mapping['fecha emision'] = 'issue_date'
        elif 'fecha' in ocs.columns:
            col_mapping['fecha'] = 'issue_date'
        
        ocs = ocs.rename(columns=col_mapping)
        
        # Agregar campos faltantes
        ocs['currency'] = 'USD'
        ocs['exchange_rate'] = 1.0
        ocs['local_import'] = 'local'

        # Si no existe project_code, crear columna vacía para continuar el proceso
        if 'project_code' not in ocs.columns:
            ocs['project_code'] = ''
        
        # Formatear fechas
        if 'issue_date' in ocs.columns:
            ocs['issue_date'] = pd.to_datetime(ocs['issue_date'], errors='coerce').dt.strftime('%Y-%m-%d')
            # Si hay fechas inválidas o nulas, usar fecha actual
            fecha_actual = datetime.now().strftime('%Y-%m-%d')
            ocs['issue_date'] = ocs['issue_date'].fillna(fecha_actual)
            # También reemplazar fechas claramente inválidas (como fechas futuras muy lejanas o pasadas muy antiguas)
            ocs['issue_date'] = ocs['issue_date'].apply(lambda x: fecha_actual if x and (x < '2020-01-01' or x > '2030-01-01') else x)
        else:
            ocs['issue_date'] = datetime.now().strftime('%Y-%m-%d')
        
        # Reordenar columnas
        ocs = ocs[['po_number', 'project_code', 'issue_date', 'currency', 'exchange_rate', 'local_import']]
        
        ocs.to_csv('purchase_orders.csv', index=False)
        print(f"✅ purchase_orders.csv creado: {len(ocs)} órdenes únicas")
    else:
        print("⚠️  No se encontraron suficientes columnas para órdenes de compra")
    
    # 5. EXTRAER DETALLES DE PRODUCTOS (todas las líneas)
    print("\n🔧 Extrayendo DETALLES DE PRODUCTOS...")
    detail_cols = []
    
    if 'n° de orden de compra' in df.columns:
        detail_cols.append('n° de orden de compra')
    elif 'orden de compra' in df.columns:
        detail_cols.append('orden de compra')
    elif 'oc' in df.columns:
        detail_cols.append('oc')
        
    if 'description' in df.columns:
        detail_cols.append('description')
    elif 'descripcion' in df.columns:
        detail_cols.append('descripcion')
    elif 'producto' in df.columns:
        detail_cols.append('producto')
        
    if 'q' in df.columns:
        detail_cols.append('q')
    elif 'cantidad' in df.columns:
        detail_cols.append('cantidad')
    elif 'qty' in df.columns:
        detail_cols.append('qty')
        
    if 'p.u.' in df.columns:
        detail_cols.append('p.u.')
    elif 'precio unitario' in df.columns:
        detail_cols.append('precio unitario')
    elif 'unit_price' in df.columns:
        detail_cols.append('unit_price')
        
    if 'currency' in df.columns:
        detail_cols.append('currency')
    elif 'moneda' in df.columns:
        detail_cols.append('moneda')
    
    if len(detail_cols) >= 3:
        detalles = df[detail_cols].copy()
        
        # Renombrar columnas
        col_mapping = {}
        if 'n° de orden de compra' in detalles.columns:
            col_mapping['n° de orden de compra'] = 'purchase_order'
        elif 'orden de compra' in detalles.columns:
            col_mapping['orden de compra'] = 'purchase_order'
        elif 'oc' in detalles.columns:
            col_mapping['oc'] = 'purchase_order'
            
        if 'description' in detalles.columns:
            col_mapping['description'] = 'product_name'
        elif 'descripcion' in detalles.columns:
            col_mapping['descripcion'] = 'product_name'
        elif 'producto' in detalles.columns:
            col_mapping['producto'] = 'product_name'
            
        if 'q' in detalles.columns:
            col_mapping['q'] = 'quantity'
        elif 'cantidad' in detalles.columns:
            col_mapping['cantidad'] = 'quantity'
        elif 'qty' in detalles.columns:
            col_mapping['qty'] = 'quantity'
            
        if 'p.u.' in detalles.columns:
            col_mapping['p.u.'] = 'unit_price'
        elif 'precio unitario' in detalles.columns:
            col_mapping['precio unitario'] = 'unit_price'
        elif 'unit_price' in detalles.columns:
            col_mapping['unit_price'] = 'unit_price'
            
        if 'currency' in detalles.columns:
            col_mapping['currency'] = 'currency'
        elif 'moneda' in detalles.columns:
            col_mapping['moneda'] = 'currency'
        
        detalles = detalles.rename(columns=col_mapping)
        
        # Agregar campos faltantes
        detalles['measurement_unit'] = 'unit'
        
        # Limpiar datos numéricos
        detalles['quantity'] = pd.to_numeric(detalles['quantity'], errors='coerce').fillna(1)
        detalles['unit_price'] = pd.to_numeric(detalles['unit_price'], errors='coerce').fillna(0)
        
        # Si falta currency, usar USD
        if 'currency' not in detalles.columns:
            detalles['currency'] = 'USD'
        
        # Reordenar columnas
        detalles = detalles[['purchase_order', 'product_name', 'quantity', 'unit_price', 'measurement_unit', 'currency']]
        
        detalles.to_csv('po_details.csv', index=False)
        print(f"✅ po_details.csv creado: {len(detalles)} líneas de detalle")
    else:
        print("⚠️  No se encontraron suficientes columnas para detalles")
    
    print("\n" + "="*50)
    print("📊 RESUMEN DE ARCHIVOS CREADOS:")
    for archivo in ['clientes.csv', 'suppliers.csv', 'projects.csv', 'purchase_orders.csv', 'po_details.csv']:
        if os.path.exists(archivo):
            size = os.path.getsize(archivo)
            print(f"✅ {archivo} - {size} bytes")
        else:
            print(f"❌ {archivo} - No creado")
    
    print("\n🎯 SIGUIENTES PASOS:")
    print("1. Revisa los archivos CSV generados")
    print("2. Ajusta los datos si es necesario")
    print("3. Usa los comandos de Django para cargar en orden")
    print("4. Verifica en el admin que todo se haya cargado correctamente")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        archivo_excel = sys.argv[1]
    else:
        # Buscar archivos Excel en el directorio actual
        excel_files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.xls'))]
        if excel_files:
            archivo_excel = excel_files[0]
            print(f"📁 Usando archivo Excel encontrado: {archivo_excel}")
        else:
            print("❌ No se encontró ningún archivo Excel")
            print("Uso: python separar_excel_jerarquia.py tu_archivo.xlsx")
            sys.exit(1)
    
    separar_excel_jerarquia(archivo_excel)