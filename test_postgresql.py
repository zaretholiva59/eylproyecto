import psycopg2
from core import settings

print("=== CONFIGURACIÓN ACTUAL ===")
print("ENGINE:", settings.DATABASES['default']['ENGINE'])
print("NAME:", settings.DATABASES['default']['NAME'])
print("USER:", settings.DATABASES['default']['USER'])
print("HOST:", settings.DATABASES['default']['HOST'])
print("PORT:", settings.DATABASES['default']['PORT'])

print("\n=== PROBANDO CONEXIÓN ===")
try:
    conn = psycopg2.connect(
        dbname=settings.DATABASES['default']['NAME'],
        user=settings.DATABASES['default']['USER'],
        password=settings.DATABASES['default']['PASSWORD'],
        host=settings.DATABASES['default']['HOST'],
        port=settings.DATABASES['default']['PORT']
    )
    print("✅ CONEXIÓN EXITOSA A POSTGRESQL")
    conn.close()
except Exception as e:
    print("❌ ERROR EN CONEXIÓN:", e)
    print("Tipo de error:", type(e).__name__)