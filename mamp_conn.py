import psycopg2

def get_mamp_connection():
    return psycopg2.connect(
        host="localhost",
        database="attendance_system",
        user="root",
        password="root",
        port=8889  # حسب إعدادات MAMP
    )
