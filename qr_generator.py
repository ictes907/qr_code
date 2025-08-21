import os
import qrcode
from db_student import get_db_connection  # أو db_teacher حسب نوع المستخدم

QR_FOLDER = "static/qrcodes"
os.makedirs(QR_FOLDER, exist_ok=True)

def generate_qr_for_course(course_id=None, qr_link=None):
    """
    توليد رمز QR لمادة واحدة أو لجميع المواد.
    - إذا تم تمرير course_id فقط → يتم توليد رمز بناءً على الرابط الافتراضي.
    - إذا تم تمرير qr_link → يتم استخدامه مباشرة.
    - إذا لم يتم تمرير شيء → يتم توليد رموز لجميع المواد التي تحتوي على qr_code.
    """
    db = get_db_connection()
    cursor = db.cursor()

    # توليد رمز واحد
    if course_id:
        if not qr_link:
            qr_link = f"https://qr-attendance-app-tgfx.onrender.com/confirm_attendance?course_id={course_id}"

        filename = f"course_{course_id}.png"
        path = os.path.join(QR_FOLDER, filename)

        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_link)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img.save(path)

        print(f"✅ تم توليد رمز QR للمادة {course_id}: {filename}")
        cursor.close()
        db.close()
        return path

    # توليد رموز لجميع المواد
    cursor.execute("SELECT id, qr_code FROM courses WHERE qr_code IS NOT NULL")
    courses = cursor.fetchall()

    for course_id, qr_link in courses:
        filename = f"course_{course_id}.png"
        path = os.path.join(QR_FOLDER, filename)

        qr = qrcode.make(qr_link)
        qr.save(path)

        print(f"📷 تم توليد: {filename}")

    cursor.close()
    db.close()
    print("🎉 تم توليد جميع الرموز بنجاح")
