import psycopg2

try:
    conn = psycopg2.connect(
        host="ep-withered-snow-....neon.tech",
        dbname="your_db",
        user="your_user",
        password="your_password",
        sslmode="require"
    )
    print("✅ الاتصال ناجح")
except Exception as e:
    print("❌ فشل الاتصال:", e)
