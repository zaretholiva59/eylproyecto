import psycopg

print("=== PROBANDO CONTRASEÑAS ===")
passwords = ['postgres123', 'password', '123456', 'admin', 'Postgres', 'Postgres123', 'root', 'postgresql']

for pwd in passwords:
    try:
        conn = psycopg.connect(dbname='eyl_db', user='postgres', password=pwd, host='localhost')
        print(f'✅ CONTRASEÑA CORRECTA: {pwd}')
        conn.close()
        break
    except Exception as e:
        print(f'❌ Probada: {pwd}')