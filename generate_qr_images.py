import os
from db import get_db_connection
import psycopg2
import qrcode

def generate_qr_images():
    try:
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("SELECT id, course_name, qr_code FROM courses WHERE qr_code IS NOT NULL")
        courses = cursor.fetchall()

        os.makedirs("static/qr", exist_ok=True)

        for course_id, course_name, qr_link in courses:
            filename = f"{course_name}_{course_id}.png"
            filepath = os.path.join("static/qr", filename)

            img = qrcode.make(qr_link)
            img.save(filepath)

            print(f"✅ تولّدت الصورة: {filename}")

    except Exception as e:
        print(f"❌ خطأ أثناء التوليد: {e}")
    finally:
        cursor.close()
        db.close()


generate_qr_images()
