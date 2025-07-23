import os
import psycopg2
import qrcode

def get_db_connection():
    return psycopg2.connect(
        host="YOUR_HOST",
        database="YOUR_DB_NAME",
        user="YOUR_DB_USER",
        password="YOUR_DB_PASSWORD"
    )

def generate_qr_images():
    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("SELECT id, qr_code FROM courses")
    courses = cursor.fetchall()

    os.makedirs("static/qr", exist_ok=True)

    for course_id, qr_link in courses:
        filename = f"qr_course_{course_id}.png"
        filepath = os.path.join("static/qr", filename)

        img = qrcode.make(qr_link)
        img.save(filepath)

        print(f"✅ تولّدت الصورة: {filename}")

    cursor.close()
    db.close()

generate_qr_images()
