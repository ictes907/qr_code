import qrcode
import os
from db_student import get_db_connection

def generate_qr_for_courses():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, course_name FROM courses")
    courses = cur.fetchall()

    qr_folder = "static/qr_code/qr_images"
    os.makedirs(qr_folder, exist_ok=True)

    for course in courses:
        course_id = course[0]
        course_name = course[1]

        qr_link = f"https://qr-attendance-app-tgfx.onrender.com/confirm_attendance?course_id={course_id}"

        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_link)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        filename = f"{qr_folder}/course_{course_id}.png"
        img.save(filename)

        cur.execute("UPDATE courses SET qr_code = %s WHERE id = %s", (qr_link, course_id))
        conn.commit()

        print(f"✅ تم حفظ الرمز في: {filename}")

    cur.close()
    conn.close()
    print("🎉 تم توليد جميع الرموز بنجاح")
