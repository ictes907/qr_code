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

QR_FOLDER = "static/qrcodes"
os.makedirs(QR_FOLDER, exist_ok=True)

def generate_qr_for_course(course_id, course_name, department_id, year_id, semester_id):
    qr_data = f"https://qr-code-7jof.onrender.com/confirm_attendance?course_id={course_id}"
    qr = qrcode.make(qr_data)

    filename = f"static/qrcodes/course_{course_id}.png"
    qr.save(filename)
    return filename


@app.route("/generate_qr_for_courses")
def generate_qr_for_courses():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # جلب المواد التي لا تحتوي على QR
        cursor.execute("SELECT id FROM courses WHERE qr_code IS NULL OR qr_code = ''")
        courses = cursor.fetchall()

        qr_folder = "static/qr_codes"
        os.makedirs(qr_folder, exist_ok=True)

        saved_files = []

        for course_id, course_name in courses:
            # توليد رابط الحضور
            qr_url = f"https://qr-code-7jof.onrender.com/attend?course_id={course_id}"
            img = qrcode.make(qr_url)

            # حفظ الصورة
            qr_path = f"{qr_folder}/course_{course_id}.png"
            img.save(qr_path)

            # تحديث قاعدة البيانات
            cursor.execute("UPDATE courses SET qr_code = %s WHERE id = %s", (qr_path, course_id))
            conn.commit()

            saved_files.append(f'<img src="/{qr_path}" alt="{course_name}" width="200">')

        cursor.close()
        conn.close()

        return "<h3>تم توليد الرموز التالية:</h3>" + "<br>".join(saved_files)

    except Exception as e:
        return f"حدث خطأ: {e}"



@app.route("/show_qr_codes")
def show_qr_codes():
    qr_files = os.listdir(QR_FOLDER)
    qr_paths = [os.path.join(QR_FOLDER, file) for file in qr_files]
    return render_template("show_qr.html", qr_paths=qr_paths)




# راوت تسجيل الحضور عبر QR
@app.route("/attend")
def attend():
    course_id = request.args.get("course_id")
    student_id = request.args.get("student_id")  # اختياري

    if not course_id:
        return "❌ المعرف غير موجود"

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO attendance (course_id, attendance_date, status)
        VALUES (%s, NOW(), 'present')
    """, (course_id,))
    conn.commit()

    cursor.close()
    conn.close()

    return "✅ تم تسجيل حضورك بنجاح"

# باقي الراوتات مثل /attendance وغيره...




@app.route("/")
def home():
    return render_template("student_login.html")
     


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

    # استلام البيانات من الرابط
    year_name = request.args.get("year_name", "").strip()
    department_name = request.args.get("department_name", "").strip()
    semester_name = request.args.get("semester_name", "").strip()

    # التحقق من وجود القيم الثلاثة بعد التنظيف
    if not year_name or not department_name or not semester_name:
        return render_template("student_courses.html", courses=[], error="❌ البيانات المطلوبة غير مكتملة")

    # الاتصال بقاعدة البيانات
    db = get_db_connection()
    cursor = db.cursor()

    # استعلام المواد المطابقة حسب الأسماء
    cursor.execute("""
        SELECT course_name, qr_code
        FROM courses
        WHERE TRIM(year_name) = %s AND TRIM(department_name) = %s AND TRIM(semester_name) = %s
    """, (year_name, department_name, semester_name))

    # تحويل النتائج إلى قواميس
    courses = [{"course_name": row[0], "qr_code": row[1]} for row in cursor.fetchall()]

    cursor.close()
    db.close()

    # عرض النتائج أو رسالة فارغة
    return render_template("student_courses.html", courses=courses)









@app.route('/scan_qr')
def scan_qr():
    return render_template('scan_qr.html')






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



@app.route('/dashboard')
def dashboard():
    if 'teacher_id' not in session:
        return redirect('/login')

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""
        SELECT full_name, university_id, education_level
        FROM teachers
        WHERE id = %s
    """, (session["teacher_id"],))

    columns = [desc[0] for desc in cursor.description]
    data = cursor.fetchone()
    teacher = dict(zip(columns, data))

    cursor.close()
    db.close()

    return render_template("dashboard.html", teacher=teacher)



@app.route("/students")
def students():
    search_id = request.args.get("search_id")

    conn = get_db_connection()
    cursor = conn.cursor()

    if search_id:
        cursor.execute("""
            SELECT 
                s.id,
                s.full_name,
                s.university_id,
                d.department_name,
                y.year_name,
                s.department_id,
                s.year_id
            FROM students s
            LEFT JOIN departments d ON s.department_id = d.id
            LEFT JOIN years y ON s.year_id = y.id
            WHERE s.university_id = %s
        """, (search_id,))
    else:
        cursor.execute("""
            SELECT 
                s.id,
                s.full_name,
                s.university_id,
                d.department_name,
                y.year_name,
                s.department_id,
                s.year_id
            FROM students s
            LEFT JOIN departments d ON s.department_id = d.id
            LEFT JOIN years y ON s.year_id = y.id
        """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    students_list = []
    for row in rows:
        students_list.append({
            'id': row[0],
            'full_name': row[1],
            'university_id': row[2],
            'department_name': row[3],
            'year_name': row[4],
            'department_id': row[5],
            'year_id': row[6]
        })

    return render_template("students.html", students=students_list)


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
def show_departments():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, department_name, year_id FROM departments")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    departments = []
    for row in rows:
        departments.append({
            'id': row[0],
            'department_name': row[1],
            'year_id': row[2]
        })

    return render_template("departments.html", departments=departments)



@app.route("/add_department", methods=["POST"])
def add_department():
    department_name = request.form["department_name"]
    year_id = request.form["year_id"]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO departments (department_name, year_id)
        VALUES (%s, %s)
    """, (department_name, year_id))
    conn.commit()
    conn.close()

    return redirect("/departments")


@app.route("/edit_department/<int:id>", methods=["POST"])
def edit_department(id):
    department_name = request.form["department_name"]
    year_id = request.form["year_id"]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE departments SET department_name = %s, year_id = %s
        WHERE id = %s
    """, (department_name, year_id, id))
    conn.commit()
    conn.close()

    return redirect("/departments")


@app.route("/delete_department/<int:id>", methods=["GET"])
def delete_department(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM departments WHERE id = %s", (id,))
    conn.commit()
    conn.close()

    return redirect("/departments")


@app.route("/years")
def show_years():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, year_name FROM years")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    years = []
    for row in rows:
        years.append({
            'id': row[0],
            'year_name': row[1]
        })

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

@app.route('/courses')
def show_courses():
    search_name = request.args.get('search_name')

    conn = get_db_connection()
    cursor = conn.cursor()

    if search_name:
        cursor.execute("""
            SELECT
                id,
                course_name,
                qr_code,
                department_name,
                semester_name,
                year_name
            FROM courses
            WHERE course_name ILIKE %s
        """, (f"%{search_name}%",))
    else:
        cursor.execute("""
            SELECT
                id,
                course_name,
                qr_code,
                department_name,
                semester_name,
                year_name
            FROM courses
        """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    courses = []
    for row in rows:
        qr_code = row[2]
        qr_link = f"/static/qrcodes/{qr_code}" if qr_code else None
        courses.append({
            'id': row[0],
            'course_name': row[1],
            'qr_code': qr_code,
            'qr_link': qr_link,
            'department_name': row[3],
            'semester_name': row[4],
            'year_name': row[5]
        })

    return render_template('courses.html', courses=courses)




@app.route("/add_course", methods=["POST"])
def add_course():
    course_name = request.form.get('course_name')
    department_name = request.form.get('department_name')
    year_name = request.form.get('year_name')
    semester_name = request.form.get('semester_name')

    conn = get_db_connection()
    cursor = conn.cursor()

    # إدخال المادة بدون QR مؤقتًا
    cursor.execute("""
        INSERT INTO courses (course_name, department_name, year_name, semester_name, qr_code)
        VALUES (%s, %s, %s, %s, %s) RETURNING id
    """, (course_name, department_name, year_name, semester_name, None))
    course_id = cursor.fetchone()[0]
    conn.commit()

    # توليد رمز QR
    qr_url = f"https://qr-code-7jof.onrender.com/confirm_attendance?course_id={course_id}"
    img = qrcode.make(qr_url)

    qr_folder = "static/qrcodes"
    os.makedirs(qr_folder, exist_ok=True)
    qr_filename = f"course_{course_id}.png"
    qr_path = os.path.join(qr_folder, qr_filename)
    img.save(qr_path)

    # تحديث مسار QR في قاعدة البيانات
    cursor.execute("UPDATE courses SET qr_code = %s WHERE id = %s", (qr_filename, course_id))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/courses")




@app.route('/edit_course/<int:id>', methods=['POST'])
def edit_course(id):
    course_name = request.form['course_name']
    department_id = request.form['department_name']
    year_id = request.form['year_name']
    semester_id = request.form['semester_name']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE courses
        SET course_name = %s, department_name = %s, year_name = %s, semester_name = %s
        WHERE id = %s
    """, (course_name, department_name, year_name, semester_name, id))
    conn.commit()
    conn.close()

    return redirect('/courses')

@app.route('/delete_course/<int:id>', methods=['GET'])
def delete_course(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM courses WHERE id = %s", (id,))
    conn.commit()
    conn.close()

    return redirect('/courses')


# صفحة الإدخال
@app.route('/new_course')
def new_course():
    return render_template('new_course.html')  # ← أنشئ نموذج HTML بسيط


@app.route('/generate_qr/<int:course_id>')
def generate_qr_route(course_id):
    from qr_generator import generate_qr_for_course  # تأكد من استيراد الدالة
    generate_qr_for_course(course_id)
    return redirect('/courses')  # يرجع لصفحة عرض المواد



@app.route("/teachers")
def show_teachers():
    search_id = request.args.get("search_id")

    conn = get_db_connection()
    cursor = conn.cursor()

    if search_id:
        cursor.execute("""
            SELECT t.full_name, t.university_id, t.education_level
            FROM teachers t
           
            WHERE t.university_id = %s
        """, (search_id,))
    else:
        cursor.execute("""
            SELECT t.full_name, t.university_id, t.education_level
            FROM teachers t
            
        """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    teachers = []
    for row in rows:
        teachers.append({
            "full_name": row[0],
            "university_id": row[1],
            "education_level": row[2],
            
        })

    return render_template("teachers.html", teachers=teachers)



@app.route("/register", methods=["GET", "POST"])
def register_teacher():
    if request.method == "POST":
        full_name = request.form["full_name"]
        university_id = request.form["university_id"]
        education_level = request.form["education_level"]
        password = request.form["password"]

        db = get_db_connection()
        cursor = db.cursor()

        # التحقق من وجود الرقم الجامعي مسبقًا
        cursor.execute("SELECT id FROM teachers WHERE university_id = %s", (university_id,))
        if cursor.fetchone():
            cursor.close()
            db.close()
            return render_template("register.html", error="الرقم الجامعي مسجّل مسبقًا")

        # إدخال بيانات المدرّس الجديد
        cursor.execute("""
            INSERT INTO teachers (full_name, university_id, education_level, password)
            VALUES (%s, %s, %s, %s)
        """, (full_name, university_id, education_level, password))

        db.commit()
        cursor.close()
        db.close()

        session["last_user"] = {"university_id": university_id, "password": password}
        return redirect("/login")

    # عرض صفحة التسجيل بدون تحميل بيانات إضافية
    return render_template("register.html")








# 📌 عرض جدول الفصول
@app.route('/semesters')
def show_semesters():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, semester_name, year_name, department_name, start_date, end_date
        FROM semesters
    """)
    rows = cursor.fetchall()
    conn.close()

    semesters = [{
        'id': row[0],
        'semester_name': row[1],
        'year_name': row[2],
        'department_name': row[3],
        'start_date': row[4],
        'end_date': row[5]
    } for row in rows]

    return render_template('semesters.html', semesters=semesters)


# ➕ إضافة فصل جديد
@app.route('/add_semester', methods=['POST'])
def add_semester():
    semester_name = request.form.get('semester_name')
    year_name = request.form.get('year_name')
    department_name = request.form.get('department_name')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO semesters (semester_name, year_name, department_name, start_date, end_date)
        VALUES (%s, %s, %s, %s, %s)
    """, (semester_name, year_name, department_name, start_date, end_date))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect('/semesters')

# ✏ تعديل فصل
@app.route('/edit_semester/<int:id>', methods=['POST'])
def edit_semester(id):
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE semesters SET start_date = ?, end_date = ? WHERE id = ?
    """, (start_date, end_date, id))
    conn.commit()
    conn.close()

    return redirect('/semesters')

# 🗑 حذف فصل
@app.route('/delete_semester/<int:id>', methods=['GET'])
def delete_semester(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM semesters WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return redirect('/semesters')




@app.route("/attendance")
def attendance():
    course_name = request.args.get("course_name")
    student_name = request.args.get("student_name")

    db = get_db_connection()
    cursor = db.cursor()

    query = """
        SELECT
            id,
            student_name,
            course_name,
            department_name,
            year_name,
            semester_name,
            attendance_date,
            status
        FROM attendance
    """

    filters = []
    params = []

    if course_name:
        filters.append("course_name = %s")
        params.append(course_name)
    if student_name:
        filters.append("student_name = %s")
        params.append(student_name)

    if filters:
        query += " WHERE " + " AND ".join(filters)

    query += " ORDER BY attendance_date DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    db.close()

    attendance = [{
        'id': row[0],
        'student_name': row[1],
        'course_name': row[2],
        'department_name': row[3],
        'year_name': row[4],
        'semester_name': row[5],
        'date': row[6],
        'status': row[7]
    } for row in rows]

    return render_template("attendance.html", attendance=attendance)



@app.route("/add_attendance", methods=["POST"])
def add_attendance():
    student_name = request.form["student_name"]
    course_name = request.form["course_name"]
    department_name = request.form["department_name"]
    year_name = request.form["year_name"]
    semester_name = request.form["semester_name"]
    date = request.form["date"]
    time = request.form["time"]
    status = request.form["status"]

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO attendance (
            student_name, course_name, department_name,
            year_name, semester_name, attendance_date, attendance_time, status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (student_name, course_name, department_name,
          year_name, semester_name, date, time, status))
    db.commit()
    cursor.close()
    db.close()
    return redirect("/attendance")


@app.route("/edit_attendance/<int:id>", methods=["POST"])
def edit_attendance(id):
    date = request.form["attendance_date"]
    time = request.form["attendance_time"]
    status = request.form["status"]

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE attendance
        SET attendance_date = %s, attendance_time = %s, status = %s
        WHERE id = %s
    """, (date, time, status, id))
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
    course_id = request.args.get('course_id')
    student_id = session.get('student_id')

    if not course_id or not student_id:
        return "❌ خطأ: لا يوجد بيانات كافية لتسجيل الحضور"

    conn = get_db_connection()
    cursor = conn.cursor()

    today = datetime.now().date()

    # تحقق إذا الحضور مسجل مسبقًا
    cursor.execute("""
        SELECT id FROM attendance
        WHERE student_id = %s AND course_id = %s AND attendance_date = %s
    """, (student_id, course_id, today))
    existing = cursor.fetchone()

    if not existing:
        # إذا لم يكن مسجل، نسجل الحضور
        cursor.execute("""
            INSERT INTO attendance (student_id, course_id, attendance_date, attendance_time, status)
            VALUES (%s, %s, %s, %s, %s)
        """, (student_id, course_id, today, datetime.now().time(), 'حاضر'))
        conn.commit()

    # جلب بيانات المادة والطالب
    cursor.execute("SELECT course_name FROM courses WHERE id = %s", (course_id,))
    course_row = cursor.fetchone()
    course_name = course_row[0] if course_row else "مادة غير معروفة"

    cursor.execute("SELECT full_name FROM students WHERE id = %s", (student_id,))
    student_row = cursor.fetchone()
    student_name = student_row[0] if student_row else "طالب غير معروف"

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
    sync_all.sync_all("mamp_to_neon")  # أو "neon_to_mamp"
    return "<h3>✅ تمت المزامنة الكاملة بنجاح</h3>"



# 🔚 في آخر الملف:
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = "0.0.0.0" if "RENDER" in os.environ else "127.0.0.1"
    app.run(host=host, port=port, debug=True)
