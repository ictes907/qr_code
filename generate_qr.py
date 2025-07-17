import qrcode

url = "http://localhost:5000/confirm_attendance?course_id=4&student_id=S1001"
img = qrcode.make(url)
img.save("test_qr.png")
