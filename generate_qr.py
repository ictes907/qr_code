import qrcode

url = "https://qr-attendance-app-tgfx.onrender.com/confirm_attendance?course_id=4&student_id=S1001"
img = qrcode.make(url)
img.save("qr_course_4.png")

