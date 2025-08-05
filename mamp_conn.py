import psycopg2

def get_mamp_connection():
    return psycopg2.connect(
        host="localhost",       # أو عنوان السيرفر
        database="attendance_system",    # اسم قاعدة Mambe
        user="host",        # اسم المستخدم
        password="",
        port=5432               # المنفذ الافتراضي
    )
