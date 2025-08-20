import psycopg2
from neon_conn import get_neon_connection as get_db_connection

def get_all_students():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM students")
    students = cur.fetchall()
    cur.close()
    conn.close()
    return students

def get_student_by_id(student_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM students WHERE id = %s", (student_id,))
    student = cur.fetchone()
    cur.close()
    conn.close()
    return student

def add_student(name, email, qr_code):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO students (name, email, qr_code) VALUES (%s, %s, %s)",
        (name, email, qr_code)
    )
    conn.commit()
    cur.close()
    conn.close()

def update_student(student_id, name, email, qr_code):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE students SET name = %s, email = %s, qr_code = %s WHERE id = %s",
        (name, email, qr_code, student_id)
    )
    conn.commit()
    cur.close()
    conn.close()

def delete_student(student_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM students WHERE id = %s", (student_id,))
    conn.commit()
    cur.close()
    conn.close()
