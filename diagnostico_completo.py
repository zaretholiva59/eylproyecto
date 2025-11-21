import os
import sys
import subprocess
import psycopg2
import psycopg

print("=" * 60)
print("DIAGNÓSTICO COMPLETO POSTGRESQL")
print("=" * 60)

# 1. VERIFICAR CONFIGURACIÓN ACTUAL
print("\n1. CONFIGURACIÓN ACTUAL:")
try:
    from core import settings
    db_config = settings.DATABASES['default']
    print(f"   ENGINE: {db_config['ENGINE']}")
    print(f"   NAME: {db_config['NAME']}")
    print(f"   USER: {db_config['USER']}")
    print(f"   HOST: {db_config['HOST']}")
    print(f"   PORT: {db_config['PORT']}")
    print(f"   PASSWORD: {'*' * len(db_config['PASSWORD'])}")
except Exception as e:
    print(f"   ❌ Error leyendo settings: {e}")

# 2. VERIFICAR SERVICIO POSTGRESQL
print("\n2. ESTADO DEL SERVICIO POSTGRESQL:")
try:
    result = subprocess.run(['sc', 'query', 'postgresql-x64-15'], 
                          capture_output=True, text=True, timeout=10)
    if 'RUNNING' in result.stdout:
        print("   ✅ Servicio PostgreSQL ejecutándose")
    else:
        print("   ❌ Servicio PostgreSQL NO ejecutándose")
        print(f"   Salida: {result.stdout}")
except Exception as e:
    print(f"   ❌ Error verificando servicio: {e}")

# 3. VERIFICAR PUERTO 5432
print("\n3. PUERTO 5432:")
try:
    result = subprocess.run(['netstat', '-an'], capture_output=True, text=True)
    if '5432' in result.stdout:
        print("   ✅ Puerto 5432 en uso")
    else:
        print("   ❌ Puerto 5432 NO en uso")
except Exception as e:
    print(f"   ❌ Error verificando puerto: {e}")

# 4. PROBAR CONEXIÓN CON PSYCOPG2
print("\n4. PRUEBA PSYCOPG2:")
try:
    conn = psycopg2.connect(
        dbname='eyl_db',
        user='postgres',
        password='postgres123',
        host='localhost',
        port=5432
    )
    print("   ✅ Conexión psycopg2 EXITOSA")
    conn.close()
except Exception as e:
    print(f"   ❌ Error psycopg2: {e}")

# 5. PROBAR CONEXIÓN CON PSYCOPG3
print("\n5. PRUEBA PSYCOPG3:")
try:
    conn = psycopg.connect(
        dbname='eyl_db',
        user='postgres',
        password='postgres123',
        host='localhost',
        port=5432
    )
    print("   ✅ Conexión psycopg3 EXITOSA")
    conn.close()
except Exception as e:
    print(f"   ❌ Error psycopg3: {e}")

# 6. VERIFICAR ENCODING DEL SISTEMA
print("\n6. CONFIGURACIÓN DE ENCODING:")
print(f"   Encoding por defecto: {sys.getdefaultencoding()}")
try:
    import locale
    print(f"   Encoding local: {locale.getpreferredencoding()}")
except:
    pass

# 7. VERIFICAR ARCHIVOS DE CONFIGURACIÓN
print("\n7. ARCHIVOS DE CONFIGURACIÓN POSTGRESQL:")
pg_paths = [
    r"C:\Program Files\PostgreSQL\15\data\pg_hba.conf",
    r"C:\Program Files\PostgreSQL\15\data\postgresql.conf"
]
for path in pg_paths:
    if os.path.exists(path):
        print(f"   ✅ {path} - EXISTE")
    else:
        print(f"   ❌ {path} - NO EXISTE")

# 8. VERIFICAR BASE DE DATOS EN PGADMIN
print("\n8. BASE DE DATOS EN PGADMIN:")
print("   ℹ️  Verifica manualmente en pgAdmin:")
print("   - Servers → PostgreSQL 15 → Databases")
print("   - Debe existir 'eyl_db'")

# 9. PROBAR CONTRASEÑAS ALTERNATIVAS
print("\n9. ÚLTIMO RESORTE - CONTRASEÑAS:")
passwords = ['postgres', 'postgres123', 'password', '123456']
for pwd in passwords:
    try:
        conn = psycopg2.connect(dbname='eyl_db', user='postgres', password=pwd, host='localhost')
        print(f"   ✅ CONTRASEÑA CORRECTA: {pwd}")
        conn.close()
        break
    except:
        print(f"   ❌ Falló: {pwd}")

print("\n" + "=" * 60)
print("DIAGNÓSTICO COMPLETADO")
print("=" * 60)