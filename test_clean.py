import psycopg2

print("=== PRUEBA LIMPIA DE CONEXIÓN ===")
try:
    conn = psycopg2.connect(
        dbname='eyl_db',
        user='postgres', 
        password='postgres',  # Contraseña simple
        host='localhost',
        port='5432'
    )
    print("✅ CONEXIÓN EXITOSA!")
    conn.close()
except Exception as e:
    print(f"❌ ERROR: {e}")
    print(f"Tipo: {type(e).__name__}")