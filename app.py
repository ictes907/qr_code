from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
import psycopg2
import os
import pandas as pd
from io import BytesIO
import urllib.parse

app = Flask(__name__)
app.secret_key = "your-secret-key"

# الاتصال بقاعدة بيانات Neon
def get_db_connection():
    return psycopg2.connect(
        dbname="neondb",
        user="neondb_owner",
        password="npg_VU8tyFN1WØIK",
        host="ep-withered-snow-aeck2ex1-pooler.c-2.us-east-2.aws.neon.tech",
        port="5432",
        sslmode="require"
    )
@app.route("/")
def home():
    return render_template("student_login.html")

@app.route("/student_login", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        university_id = request.form.get("university_id", "").strip()

        if not full_name or not university_id:
            return render_template("student_login.html", error="يرجى تعبئة جميع الحقول")

        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM students WHERE full_name = %s AND university_id = %s", 
                       (full_name, university_id))
        student = cursor.fetchone()
        cursor.close()
        db.close()

        if student:
            session["student_id"] = student[0]
            session["student_name"] = student[1]
            return redirect("/student_dashboard")
        else:
            return render_template("student_login.html", error="البيانات غير صحيحة")
    return render_template("student_login.html")

@app.route("/student_dashboard")
def student_dashboard():
    if "student_id" not in session:
        return redirect("/")

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM years")
    years = cursor.fetchall()
    cursor.execute("SELECT * FROM departments")
    departments = cursor.fetchall()
    cursor.execute("SELECT * FROM semesters")
    semesters = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template("student_dashboard.html",
                           student_name=session["student_name"],
                           years=years,
                           departments=departments,
                           semesters=semesters)
@app.route("/login", methods=["GET", "POST"])
def login_teacher():
    if request.method == "POST":
        university_id = request.form.get("university_id")
        password = request.form.get("password")

        if not university_id or not password:
            return render_template("login.html", error="يرجى تعبئة جميع الحقول")

        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT id, full_name, password FROM teachers WHERE university_id = %s", (university_id,))
        teacher = cursor.fetchone()
        cursor.close()
        db.close()

        if teacher and teacher[2] == password:
            session["teacher_id"] = teacher[0]
            return redirect("/dashboard")
        else:
            return render_template("login.html", error="البيانات غير صحيحة")
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "teacher_id" not in session:
        return redirect("/login")

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT full_name FROM teachers WHERE id = %s", (session["teacher_id"],))
    teacher = cursor.fetchone()
    cursor.close()
    db.close()

    return render_template("dashboard.html", teacher=teacher)
@app.route("/students")
def students():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template("students.html", students=students)

@app.route("/add_student", methods=["POST"])
def add_student():
    full_name = request.form["full_name"]
    university_id = request.form["university_id"]
    department_id = request.form["department_id"]
    year_id = request.form["year_id"]

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO students (full_name, university_id, department_id, year_id) VALUES (%s, %s, %s, %s)",
        (full_name, university_id, department_id, year_id))
    db.commit()
    cursor.close()
    db.close()
    return redirect("/students")

@app.route("/edit_student/<int:id>", methods=["POST"])
def edit_student(id):
    full_name = request.form["full_name"]
    university_id = request.form["university_id"]
    department_id = request.form["department_id"]
    year_id = request.form["year_id"]

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE students SET full_name = %s, university_id = %s, department_id = %s, year_id = %s WHERE id = %s",
        (full_name, university_id, department_id, year_id, id))
    db.commit()
    cursor.close()
    db.close()
    return redirect("/students")

@app.route("/delete_student/<int:id>")
def delete_student(id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM students WHERE id = %s", (id,))
    db.commit()
    cursor.close()
    db.close()
    return redirect("/students")
@app.route("/departments")
def departments():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM departments")
    departments = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template("departments.html", departments=departments)

@app.route("/add_department", methods=["POST"])
def add_department():
    department_name = request.form["department_name"]
    year_id = request.form["year_id"]

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO departments (department_name, year_id) VALUES (%s, %s)",
        (department_name, year_id))
    db.commit()
    cursor.close()
    db.close()
    return redirect("/departments")

@app.route("/edit_department/<int:department_id>", methods=["POST"])
def edit_department(department_id):
    department_name = request.form["department_name"]
    year_id = request.form["year_id"]

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE departments SET department_name = %s, year_id = %s WHERE id = %s",
        (department_name, year_id, department_id))
    db.commit()
    cursor.close()
    db.close()
    return redirect("/departments")

@app.route("/delete_department/<int:id>")
def delete_department(id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM departments WHERE id = %s", (id,))
    db.commit()
    cursor.close()
    db.close()
    return redirect("/departments")
@app.route("/years")
def years():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM years")
    years = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template("years.html", years=years)

@app.route("/add_year", methods=["POST"])
def add_year():
    year_name = request.form["year_name"]
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("INSERT INTO years (year_name) VALUES (%s)", (year_name,))
    db.commit()
    cursor.close()
    db.close()
    return redirect("/years")

@app.route("/edit_year/<int:id>", methods=["POST"])
def edit_year(id):
    year_name = request.form["year_name"]
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("UPDATE years SET year_name = %s WHERE id = %s", (year_name, id))
    db.commit()
    cursor.close()
    db.close()
    return redirect("/years")

@app.route("/delete_year/<int:id>")
def delete_year(id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM years WHERE id = %s", (id,))
    db.commit()
    cursor.close()
    db.close()
    return redirect("/years")
@app.route("/courses")
def courses():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM courses")
    courses_list = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template("courses.html", courses=courses_list)

@app.route("/add_course", methods=["POST"])
def add_course():
    course_name = request.form["course_name"]
    department_id = request.form["department_id"]
    year_id = request.form["year_id"]
    semester_id = request.form["semester_id"]

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO courses (course_name, department_id, year_id, semester_id) VALUES (%s, %s, %s, %s)",
        (course_name, department_id, year_id, semester_id))
    course_id = cursor.lastrowid

    # توليد رمز QR للمادة
    qr_filename = generate_qr(course_id, course_name)
    cursor.execute("UPDATE courses SET qr_code = %s WHERE id = %s", (qr_filename, course_id))

    db.commit()
    cursor.close()
    db.close()
    return redirect("/courses")

@app.route("/edit_course/<int:course_id>", methods=["POST"])
def edit_course(course_id):
    course_name = request.form["course_name"]
    department_id = request.form["department_id"]
    year_id = request.form["year_id"]
    semester_id = request.form["semester_id"]

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE courses SET course_name = %s, department_id = %s, year_id = %s, semester_id = %s WHERE id = %s",
        (course_name, department_id, year_id, semester_id, course_id))
    db.commit()
    cursor.close()
    db.close()
    return redirect("/courses")

@app.route("/delete_course/<int:id>")
def delete_course(id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM courses WHERE id = %s", (id,))
    db.commit()
    cursor.close()
    db.close()
    return redirect("/courses")
@app.route("/teachers")
def teachers():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM teachers")
    teachers_list = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template("teachers.html", teachers=teachers_list)

@app.route("/register", methods=["GET", "POST"])
def register_teacher():
    if request.method == "POST":
        full_name = request.form["full_name"]
        university_id = request.form["university_id"]
        education_level = request.form["education_level"]
        password = request.form["password"]
        department_id = request.form["department_id"]
        year_ids = ",".join(request.form.getlist("year_ids"))

        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT id FROM teachers WHERE university_id = %s", (university_id,))
        if cursor.fetchone():
            cursor.close()
            db.close()
            return render_template("register.html", error="الرقم الجامعي مسجّل مسبقًا")

        cursor.execute(
            "INSERT INTO teachers (full_name, university_id, education_level, password, department_id, year_ids) VALUES (%s, %s, %s, %s, %s, %s)",
            (full_name, university_id, education_level, password, department_id, year_ids))
        db.commit()
        cursor.close()
        db.close()

        session["last_user"] = {"university_id": university_id, "password": password}
        return redirect("/login")

    # تحميل الأقسام والسنوات لعرضها بالتسجيل
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM departments")
    departments = cursor.fetchall()
    cursor.execute("SELECT * FROM years")
    years = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template("register.html", departments=departments, years=years)
import qrcode

def generate_qr(course_id, course_name, student_id="S1001"):
    base_url = "https://qr-attendance-app-tgfx.onrender.com"
    sanitized_name = course_name.replace(" ", "_")
    qr_filename = f"{sanitized_name}_{course_id}.png"
    qr_path = os.path.join("static", "qrcodes", qr_filename)

    os.makedirs(os.path.dirname(qr_path), exist_ok=True)
    qr_url = f"{base_url}/confirm_attendance?course_id={course_id}&student_id={student_id}"

    if os.path.exists(qr_path):
        os.remove(qr_path)

    qr = qrcode.make(qr_url)
    qr.save(qr_path)
    return qr_filename
@app.route("/attendance")
def attendance():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("""
        SELECT s.full_name, c.course_name, a.attendance_date, a.status
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        JOIN courses c ON a.course_id = c.id
    """)
    records = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template("attendance.html", attendance=records)

@app.route("/add_attendance", methods=["POST"])
def add_attendance():
    student_id = request.form["student_id"]
    course_id = request.form["course_id"]
    date = request.form["date"]
    status = request.form["status"]

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO attendance (student_id, course_id, attendance_date, status) VALUES (%s, %s, %s, %s)",
        (student_id, course_id, date, status))
    db.commit()
    cursor.close()
    db.close()
    return redirect("/attendance")

@app.route("/edit_attendance/<int:id>", methods=["POST"])
def edit_attendance(id):
    student_id = request.form["student_id"]
    course_id = request.form["course_id"]
    date = request.form["attendance_date"]
    status = request.form["status"]

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE attendance SET student_id = %s, course_id = %s, attendance_date = %s, status = %s WHERE id = %s",
        (student_id, course_id, date, status, id))
    db.commit()
    cursor.close()
    db.close()
    return redirect("/attendance")

@app.route("/delete_attendance/<int:id>")
def delete_attendance(id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM attendance WHERE id = %s", (id,))
    db.commit()
    cursor.close()
    db.close()
    return redirect("/attendance")
@app.route("/confirm_attendance")
def confirm_attendance():
    course_id = request.args.get("course_id")
    student_id = request.args.get("student_id")

    if not course_id or not student_id:
        return "بيانات ناقصة", 400

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("SELECT full_name FROM students WHERE id = %s", (student_id,))
    student = cursor.fetchone()
    cursor.execute("SELECT course_name FROM courses WHERE id = %s", (course_id,))
    course = cursor.fetchone()

    if not student or not course:
        cursor.close()
        db.close()
        return "الطالب أو المادة غير موجودة", 404

    cursor.execute("""
        INSERT INTO attendance (student_id, course_id, attendance_date, status) 
        VALUES (%s, %s, CURRENT_DATE, 'حاضر')
    """, (student_id, course_id))
    db.commit()
    cursor.close()
    db.close()

    return render_template("attendance_success.html", student=student[0], course=course[0])
@app.route("/export_attendance")
def export_attendance():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("""
        SELECT s.full_name, s.university_id, c.course_name, a.attendance_date, a.status
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        JOIN courses c ON a.course_id = c.id
    """)
    data = cursor.fetchall()
    cursor.close()
    db.close()

    df = pd.DataFrame(data, columns=["الاسم الكامل", "الرقم الجامعي", "المادة", "تاريخ الحضور", "الحالة"])
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Attendance")
    output.seek(0)

    return send_file(output, as_attachment=True,
                     download_name="attendance.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
if __name__ == "__main__":
    app.run(debug=True)
