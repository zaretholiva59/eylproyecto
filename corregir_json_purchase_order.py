"""
Script para corregir datos_eyl.json:
1. Cambiar las PKs de PurchaseOrder de IDs numéricos a po_number
2. Actualizar todas las referencias ForeignKey de purchase_order
3. Limpiar las primeras líneas inválidas del JSON
"""

import json
import re

def limpiar_json_entrada(contenido):
    """Elimina las primeras líneas de WARNING antes del JSON válido"""
    # Buscar el inicio del array JSON
    inicio_json = contenido.find('[')
    if inicio_json > 0:
        return contenido[inicio_json:]
    return contenido

def corregir_json_purchase_order(archivo_entrada, archivo_salida):
    """
    Corrige el JSON:
    - Cambia PKs de PurchaseOrder de números a po_number
    - Actualiza referencias ForeignKey de purchase_order
    """
    print(f"[*] Leyendo {archivo_entrada}...")
    
    # Leer y limpiar el archivo
    with open(archivo_entrada, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    contenido_limpio = limpiar_json_entrada(contenido)
    
    try:
        data = json.loads(contenido_limpio)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Error al parsear JSON: {e}")
        return False
    
    print(f"[OK] JSON cargado: {len(data)} registros")
    
    # Paso 1: Crear mapeo de IDs antiguos a po_numbers
    id_to_po_number = {}
    purchase_orders = []
    otros_registros = []
    
    for item in data:
        if item.get('model') == 'projects.purchaseorder':
            old_pk = item.get('pk')
            po_number = item.get('fields', {}).get('po_number')
            
            if po_number and old_pk is not None:
                # Guardar el mapeo
                id_to_po_number[int(old_pk)] = po_number
                # Cambiar la PK a po_number
                item['pk'] = po_number
                purchase_orders.append(item)
            else:
                otros_registros.append(item)
        else:
            otros_registros.append(item)
    
    print(f"[OK] Mapeo creado: {len(id_to_po_number)} PurchaseOrders")
    print(f"   Ejemplos: {dict(list(id_to_po_number.items())[:3])}")
    
    # Paso 2: Actualizar referencias ForeignKey en modelos relacionados
    modelos_actualizados = {
        'projects.podetailproduct': 0,
        'projects.podetailsupplier': 0,
        'projects.invoice': 0,
    }
    
    for item in otros_registros:
        modelo = item.get('model', '')
        
        if modelo in ['projects.podetailproduct', 'projects.podetailsupplier', 'projects.invoice']:
            fields = item.get('fields', {})
            purchase_order_ref = fields.get('purchase_order')
            
            if purchase_order_ref is not None:
                # Si es un número, buscar el po_number correspondiente
                if isinstance(purchase_order_ref, int):
                    po_number = id_to_po_number.get(purchase_order_ref)
                    if po_number:
                        fields['purchase_order'] = po_number
                        modelos_actualizados[modelo] += 1
                    else:
                        print(f"[ADVERTENCIA] No se encontro po_number para ID {purchase_order_ref} en {modelo}")
                        # Dejar vacío para que sea NULL
                        fields['purchase_order'] = None
                elif isinstance(purchase_order_ref, str):
                    # Si ya es un string, asumir que es un po_number válido
                    pass
    
    print(f"\n[OK] Referencias actualizadas:")
    for modelo, cantidad in modelos_actualizados.items():
        if cantidad > 0:
            print(f"   - {modelo}: {cantidad} referencias")
    
    # Paso 3: Reconstruir el JSON con el orden correcto
    # Primero las dependencias, luego PurchaseOrders, luego los que dependen de ellos
    datos_corregidos = []
    
    # 1. Modelos base sin dependencias de PurchaseOrder
    modelos_base = [
        'auth.user', 'auth.group', 'auth.permission',
        'sessions.session',
        'projects.costumer', 'projects.supplier', 'projects.product',
        'projects.respon', 'projects.projects', 'projects.chance',
    ]
    
    for item in otros_registros:
        if item.get('model') in modelos_base:
            datos_corregidos.append(item)
    
    # 2. PurchaseOrders
    datos_corregidos.extend(purchase_orders)
    
    # 3. Modelos que dependen de PurchaseOrder
    for item in otros_registros:
        if item.get('model') in ['projects.podetailproduct', 'projects.podetailsupplier', 'projects.invoice']:
            datos_corregidos.append(item)
    
    # 4. Resto de modelos
    modelos_resto = [
        'projects.presale', 'projects.billing', 'projects.clientinvoice',
        'projects.earnedvalue', 'projects.projectbaseline', 'projects.projectmonthlybaseline',
        'projects.projectprogress', 'projects.budgetchange', 'projects.activity',
        'tasks.task', 'projects.invoicedetail',
    ]
    
    for item in otros_registros:
        if item.get('model') not in modelos_base and item.get('model') not in ['projects.podetailproduct', 'projects.podetailsupplier', 'projects.invoice']:
            datos_corregidos.append(item)
    
    # Paso 4: Guardar el JSON corregido
    print(f"\n[*] Guardando JSON corregido en {archivo_salida}...")
    
    with open(archivo_salida, 'w', encoding='utf-8') as f:
        json.dump(datos_corregidos, f, ensure_ascii=False, indent=4)
    
    print(f"[OK] JSON corregido guardado exitosamente!")
    print(f"   Total de registros: {len(datos_corregidos)}")
    print(f"   PurchaseOrders: {len(purchase_orders)}")
    
    return True

if __name__ == '__main__':
    import sys
    
    archivo_entrada = 'datos_eyl.json'
    archivo_salida = 'datos_eyl_corregido.json'
    
    if len(sys.argv) > 1:
        archivo_entrada = sys.argv[1]
    if len(sys.argv) > 2:
        archivo_salida = sys.argv[2]
    
    print("=" * 60)
    print("CORRECCION DE JSON - PurchaseOrder")
    print("=" * 60)
    print(f"Entrada: {archivo_entrada}")
    print(f"Salida: {archivo_salida}")
    print("=" * 60)
    
    exito = corregir_json_purchase_order(archivo_entrada, archivo_salida)
    
    if exito:
        print("\n" + "=" * 60)
        print("[OK] CORRECCION COMPLETADA EXITOSAMENTE")
        print("=" * 60)
        print(f"\nProximos pasos:")
        print(f"   1. Revisa el archivo {archivo_salida}")
        print(f"   2. Si esta correcto, reemplazalo: ren {archivo_salida} {archivo_entrada}")
        print(f"   3. Genera las migraciones: python manage.py makemigrations")
        print(f"   4. Aplica las migraciones: python manage.py migrate")
        print(f"   5. Carga los datos: python manage.py loaddata {archivo_entrada}")
        print("=" * 60)
    else:
        print("\n[ERROR] ERROR EN LA CORRECCION")
        sys.exit(1)

