import os
import qrcode
from flask import url_for
from db_student import get_db_connection  # أو db_teacher حسب السياق

QR_FOLDER = "static/qrcodes"
os.makedirs(QR_FOLDER, exist_ok=True)

def generate_qr_for_course(course_id):
    # توليد رابط كامل باستخدام url_for
    qr_link = url_for('confirm_attendance', course_id=course_id, _external=True)

    # اسم الملف
    filename = f"course_{course_id}.png"
    path = os.path.join(QR_FOLDER, filename)

    # توليد الرمز
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(qr_link)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(path)

    # تحديث الرابط في قاعدة البيانات
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE courses SET qr_code = %s WHERE id = %s", (qr_link, course_id))
    conn.commit()
    cursor.close()
    conn.close()

    print(f"✅ تم توليد رمز QR للمادة {course_id}: {qr_link}")
    return path
