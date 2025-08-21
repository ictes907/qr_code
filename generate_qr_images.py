import qrcode
import os
from db_student import get_db_connection

def generate_qr_for_courses():
    conn = get_db_connection()
    cur = conn.cursor()

    # جلب كل المواد من قاعدة البيانات
    cur.execute("SELECT id, course_name FROM courses")
    courses = cur.fetchall()

    # إنشاء مجلد لحفظ الصور إذا لم يكن موجود
    qr_folder = "static/qr_codes"
    os.makedirs(qr_folder, exist_ok=True)

    for course in courses:
        course_id = course[0]
        course_name = course[1]

        # محتوى الرمز: يمكن أن يكون رابط أو نص معرف المادة
        qr_data = f"course:{course_id}"

        # توليد الرمز
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # حفظ الصورة باسم المادة أو معرفها
        filename = f"{qr_folder}/course_{course_id}.png"
        img.save(filename)

        print(f"✅ تم توليد الرمز للمادة: {course_name} → {filename}")

    cur.close()
    conn.close()
    print("🎉 تم توليد جميع رموز QR بنجاح")

# تشغيل الوظيفة
generate_qr_for_courses()

