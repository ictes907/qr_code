from mamp_conn import get_mamp_connection
from neon_conn import get_neon_connection

# الجداول المراد مزامنتها
tables_to_sync = {
    "years": "id, year_name",
    "departments": "id, department_name, year_id",
    "semesters": "id, semester_name, year_id, department_name, start_date, end_date",
    "courses": "id, course_name, department_id, year_id, semester_id, qr_code",
    "students": "id, full_name, university_id, department_id, year_id",
    "teachers": "id, full_name, university_id, department_id, year_id",
    "attendance": "id, student_id, course_id, attendance_date, attendance_time, status",
}

def sync_table(source_db, target_db, table_name, columns):
    print(f"\n🔄 مزامنة جدول: {table_name}")
    src_cursor = source_db.cursor()
    tgt_cursor = target_db.cursor()

    src_cursor.execute(f"SELECT {columns} FROM {table_name}")
    rows = src_cursor.fetchall()

    # حذف البيانات القديمة في الهدف
    tgt_cursor.execute(f"DELETE FROM {table_name}")

    placeholders = ", ".join(["%s"] * len(columns.split(",")))
    insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

    for row in rows:
        tgt_cursor.execute(insert_query, row)

    target_db.commit()
    src_cursor.close()
    tgt_cursor.close()
    print(f"✅ تم نقل {len(rows)} صف من جدول {table_name}")

def sync_all(direction="mampe_to_neon"):
    if direction == "mampe_to_neon":
        source = get_mamp_connection()
        target = get_neon_connection()
    elif direction == "neon_to_mampe":
        source = get_neon_connection()
        target = get_mamp_connection()
    else:
        raise ValueError("❌ اتجاه غير معروف، استخدم 'mampe_to_neon' أو 'neon_to_mampe'")

    for table, cols in tables_to_sync.items():
        sync_table(source, target, table, cols)

    source.close()
    target.close()
    print("\n🎉 تمت المزامنة الكاملة بنجاح")

# مثال تشغيل
if __name__ == "__main__":
    sync_all("mampe_to_neon")  # أو "neon_to_mampe"
