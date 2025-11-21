import psycopg

print("=== PRUEBA CON PSYCOPG3 ===")
try:
    conn = psycopg.connect(
        dbname='eyl_db',
        user='postgres', 
        password='postgres',
        host='localhost',
        port='5432'
    )
    print("✅ CONEXIÓN EXITOSA CON PSYCOPG3!")
    conn.close()
except Exception as e:
    print(f"❌ ERROR: {e}")
    print(f"Tipo: {type(e).__name__}")