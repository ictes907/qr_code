from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from neon_conn import get_neon_connection as get_db_connection
from qr_generator import generate_qr_for_course
import psycopg2
import pymysql
import qrcode
import pandas as pd
from io import BytesIO
from datetime import datetime
import urllib.parse
import os

from flask import Flask
app = Flask(__name__)
app.secret_key = "your-secret-key"

QR_FOLDER = "static/qr_codes"
os.makedirs(QR_FOLDER, exist_ok=True)

# هنا تكتب كل الراوتات والدوال




@app.route("/")
def home():
    return render_template("student_login.html")
     
from db_student import get_db_connection

@app.route("/student_login", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        try:
            full_name = request.form.get("full_name", "").strip()
            university_id = request.form.get("university_id", "").strip()

            # التحقق من القيم
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
        except Exception as e:
            return f"<h3>❌ خطأ داخلي:<br>{e}</h3>"

    return render_template("student_login.html")


@app.route("/debug_db")
def debug_db():
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM students")
        count = cursor.fetchone()[0]
        cursor.close()
        db.close()
        return f"<h3>✅ الاتصال ناجح، عدد الطلاب: {count}</h3>"
    except Exception as e:
        return f"<h3>❌ فشل الاتصال:<br>{e}</h3>"

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


@app.route("/student_courses", methods=["GET"])
def student_courses():
    if "student_id" not in session:
        return redirect("/")

    year_id = request.args.get("year_id")
    department_id = request.args.get("department_id")
    semester_id = request.args.get("semester_id")

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("""
        SELECT id, course_name, qr_code
        FROM courses
        WHERE year_id = %s AND department_id = %s AND semester_id = %s
    """, (year_id, department_id, semester_id))

    courses = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template("student_courses.html", courses=courses)




@app.route('/scan_qr')
def scan_qr():
    return render_template('scan_qr.html')




# الاتصال بقاعدة بيانات Neon
def get_db_connection():
    return psycopg2.connect(
        dbname="neondb",
        user="neondb_owner",
        password="npg_2ogfihcX5JEO",
        host="ep-withered-snow-aeck2exl-pooler.c-2.us-east-2.aws.neon.tech",
        port="5432",
        sslmode="require"
    )


@app.route("/register_attendance")
def register_attendance():
    course_id = request.args.get("course_id")
    student_id = session.get("student_id")

    if not student_id:
        return redirect("/")

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("INSERT INTO attendance (student_id, course_id) VALUES (%s, %s)",
                   (student_id, course_id))

    db.commit()
    cursor.close()
    db.close()

    return "<h3>✅ تم تسجيل حضورك بنجاح للمادة رقم {}!</h3>".format(course_id)


@app.route("/show_password")
def print_password():
    try:
        conn = get_db_connection()
        # لو الاتصال نجح، نعرض الكلمة المستخدمة
        return "<h3>✅ الاتصال نجح فعليًا، والكلمة ضمن الكود تعمل</h3>"
    except Exception as e:
        return f"<h3>❌ فشل الاتصال، والخطأ:<br>{e}</h3>"
@app.route("/debug_lists")
def debug_lists():
    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM years")
    y_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM departments")
    d_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM semesters")
    s_count = cursor.fetchone()[0]

    cursor.close()
    db.close()

    return f"<h3>📊 عدد السنوات: {y_count} | الأقسام: {d_count} | الفصول: {s_count}</h3>"


@app.route("/inspect_years")
def inspect_years():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM years LIMIT 5")
    rows = cursor.fetchall()
    cursor.close()
    db.close()

    return f"<pre>{rows}</pre>"




@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        university_id = request.form["university_id"]
        password = request.form["password"]

        # افحص الحساب داخل جدول المدرّسين
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT id FROM teachers WHERE university_id = %s AND password = %s", (university_id, password))
        teacher = cursor.fetchone()
        cursor.close(); db.close()

        if teacher:
            session["teacher_id"] = teacher[0]
            return redirect("/dashboard")
        else:
            return "<h3>❌ بيانات غير صحيحة</h3>"

    # عرض نموذج تسجيل الدخول
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



@app.route('/add_course', methods=['POST'])
def add_course():
    course_name = request.form['course_name']
    department_id = request.form['department_id']
    year_id = request.form['year_id']
    semester_id = request.form['semester_id']

    db = get_db_connection()
    cursor = db.cursor()

    # 1. حفظ المادة بدون QR مؤقتًا
    cursor.execute("""
        INSERT INTO courses (course_name, qr_code, department_id, year_id, semester_id)
        VALUES (%s, %s, %s, %s, %s)
    """, (course_name, "", department_id, year_id, semester_id))
    course_id = cursor.fetchone()[0] if cursor.description else cursor.lastrowid
    db.commit()

    # 2. توليد رابط الحضور
    qr_link = f"https://qr-attendance-app-tgfx.onrender.com/confirm_attendance?course_id={course_id}"

    # 3. توليد صورة QR
    qr = qrcode.make(qr_link)
    filename = os.path.join(QR_FOLDER, f"course_{course_id}.png")
    qr.save(filename)

    # 4. تحديث qr_code في قاعدة البيانات
    cursor.execute("UPDATE courses SET qr_code = %s WHERE id = %s", (qr_link, course_id))
    db.commit()

    cursor.close()
    db.close()

    return f"تم حفظ المادة وتوليد رمز QR بنجاح! ✅<br><img src='/{filename}' width='200'>"

# صفحة الإدخال
@app.route('/new_course')
def new_course():
    return render_template('new_course.html')  # ← أنشئ نموذج HTML بسيط





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


# توليد رمز لمادة واحدة
generate_qr_for_course(course_id=5)

# توليد رمز من رابط مخصص
generate_qr_for_course(course_id=5, qr_link="https://example.com/custom_link")

# توليد رموز لجميع المواد
generate_qr_for_course()


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


@app.route('/confirm_attendance')
def confirm_attendance():
    course_id = request.args.get('course_id')
    student_id = session.get('student_id')

    if not course_id or not student_id:
        return "❌ خطأ: لا يوجد بيانات كافية لتسجيل الحضور"

    conn = get_db_connection()
    cursor = conn.cursor()

    # حفظ الحضور
    cursor.execute("""
        INSERT INTO attendance (student_id, course_id, timestamp)
        VALUES (%s, %s, %s)
    """, (student_id, course_id, datetime.now()))
    conn.commit()

    # جلب بيانات المادة والطالب
    cursor.execute("SELECT course_name FROM courses WHERE id = %s", (course_id,))
    course_name = cursor.fetchone()[0]

    cursor.execute("SELECT name FROM students WHERE id = %s", (student_id,))
    student_name = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return render_template("attendance_success.html",
                           course_name=course_name,
                           student_name=student_name,
                           time=datetime.now().strftime("%Y-%m-%d %H:%M"))




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



@app.route('/complete-update')
def complete_update():
    # 1. حذف رموز QR من مجلد معين
    qr_folder = 'static/qr_codes'
    for filename in os.listdir(qr_folder):
        if filename.endswith('.png'):
            os.remove(os.path.join(qr_folder, filename))

    # 2. تسجيل الحضور في قاعدة البيانات (مثال باستخدام SQLite)
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO attendance (student_id, status) VALUES (?, ?)", ("12345", "present"))
    conn.commit()
    conn.close()

    # 3. عرض صفحة تأكيد
    return render_template('complete_update.html')




@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/sync_all")
def sync_all_route():
    import sync_all
    sync_all.sync_all("mampe_to_neon")  # أو "neon_to_mampe"
    return "<h3>✅ تمت المزامنة الكاملة بنجاح</h3>"



# 🔚 في آخر الملف:
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = "0.0.0.0" if "RENDER" in os.environ else "127.0.0.1"
    app.run(host=host, port=port, debug=True)
