import qrcode

url = "https://qr-attendance-app-tgfx.onrender.com/confirm_attendance?course_id=2&student_id=S1001"
img = qrcode.make(url)
img.save("static/qr_course_2.png")


