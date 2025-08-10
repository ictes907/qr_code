# استيراد الاتصال من القاعدتين
from db_teacher import get_db_connection as mysql_conn
from db_student import get_db_connection as pg_conn

def sync_courses():
    mysql_db = mysql_conn()
    pg_db = pg_conn()

    mysql_cursor = mysql_db.cursor()
    pg_cursor = pg_db.cursor()

    # جلب المواد من قاعدة المدرّس
    mysql_cursor.execute("SELECT id, course_name, year_id, department_id, semester_id, qr_code FROM courses")
    courses = mysql_cursor.fetchall()

    # نقل المواد إلى قاعدة الطالب
    for course in courses:
        pg_cursor.execute("""
            INSERT INTO courses (id, course_name, year_id, department_id, semester_id, qr_code)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, course)

    pg_db.commit()
    mysql_cursor.close()
    pg_cursor.close()
    mysql_db.close()
    pg_db.close()

    print("✅ تمت مزامنة المواد بنجاح من المدرّس إلى الطالب")
