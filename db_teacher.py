import psycopg2
from neon_conn import get_neon_connection as get_db_connection

def get_all_teachers():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM teachers")
    teachers = cur.fetchall()
    cur.close()
    conn.close()
    return teachers

def get_teacher_by_id(teacher_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM teachers WHERE id = %s", (teacher_id,))
    teacher = cur.fetchone()
    cur.close()
    conn.close()
    return teacher

def add_teacher(name, email, subject):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO teachers (name, email, subject) VALUES (%s, %s, %s)",
        (name, email, subject)
    )
    conn.commit()
    cur.close()
    conn.close()

def update_teacher(teacher_id, name, email, subject):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE teachers SET name = %s, email = %s, subject = %s WHERE id = %s",
        (name, email, subject, teacher_id)
    )
    conn.commit()
    cur.close()
    conn.close()

def delete_teacher(teacher_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM teachers WHERE id = %s", (teacher_id,))
    conn.commit()
    cur.close()
    conn.close()
