from db_teacher import get_db_connection as mysql_conn
from db_student import get_db_connection as pg_conn

# ترتيب الجداول حسب العلاقات
tables_to_sync = {
    "years": "id, year_name",
    "departments": "id, department_name, year_id",
    "semesters": "id, semester_name, year_id, department_name, start_date, end_date",
    "courses": "id, course_name, department_id, year_id, semester_id, qr_code",
    "students": "id, full_name, university_id, department_id, year_id",
    "teachers": "id, full_name, university_id, department_id, year_id",
    "attendance": "id, student_id, course_id, attendance_date, attendance_time, status",
}

def sync_table(table_name, columns):
    print(f"\n📤 بدء مزامنة جدول: {table_name}")
    mysql_db = mysql_conn()
    pg_db = pg_conn()
    mysql_cursor = mysql_db.cursor()
    pg_cursor = pg_db.cursor()

    # قراءة الصفوف من قاعدة MAMP
    try:
        mysql_cursor.execute(f"SELECT {columns} FROM {table_name}")
        rows = mysql_cursor.fetchall()
    except Exception as e:
        print(f"❌ فشل في قراءة بيانات من {table_name}: {e}")
        mysql_cursor.close(); mysql_db.close()
        return

    placeholders = ", ".join(["%s"] * len(columns.split(",")))
    insert_query = f"""
        INSERT INTO {table_name} ({columns})
        VALUES ({placeholders})
        ON CONFLICT DO NOTHING
    """

    inserted = 0
    failed = 0

    for row in rows:
        try:
            pg_cursor.execute(insert_query, row)
            inserted += 1
        except Exception as e:
            print(f"⚠️ فشل نقل صف داخل {table_name}: {e}")
            failed += 1

    pg_db.commit()
    mysql_cursor.close(); pg_cursor.close()
    mysql_db.close(); pg_db.close()

    print(f"✅ جدول {table_name}: تم نقل {inserted} صف، تخطي {failed}")
    print("-" * 50)

# تنفيذ النقل لكل الجداول
for tbl, cols in tables_to_sync.items():
    sync_table(tbl, cols)

print("\n🎉 تمت مزامنة جميع بيانات المدرّس إلى الطالب بنجاح")
