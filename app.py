import qrcode
import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import urllib.parse


import psycopg2


from flask import Flask, session
app = Flask(__name__)
app.secret_key = 'your-secret-key'
print("✅ التطبيق بدأ التشغيل بنجاح على Render")





  
def generate_qr(course_id, course_name, student_id="S1001"):
    # تأمين رابط Cloudflare
    base_url = "https://qr-code.onrender.com"




    


    # اسم الملف (نظيف وسهل التعرف عليه)
    sanitized_name = course_name.replace(" ", "_")  # لتجنب مشاكل المسافات
    qr_filename = f"{sanitized_name}_{course_id}.png"
    qr_path = os.path.join("static", "qrcodes", qr_filename)

    # إنشاء المجلد إذا ما كان موجود
    os.makedirs(os.path.dirname(qr_path), exist_ok=True)

    # رابط الحضور ضمن Cloudflare
    qr_url = f"{base_url}/confirm_attendance?course_id={course_id}&student_id={student_id}"

    # حذف الملف القديم إن وُجد
    if os.path.exists(qr_path):
        os.remove(qr_path)

    # توليد وحفظ الرمز
    qr = qrcode.make(qr_url)
    qr.save(qr_path)

    return qr_filename

import pandas as pd
from flask import send_file
from io import BytesIO

def generate_missing_qr():
    # 1. الاتصال بقاعدة البيانات
  def generate_missing_qr():
    db = get_db_connection()
    cursor = db.cursor()
    
    cursor.execute("SELECT id, course_name FROM courses WHERE qr_code IS NULL OR qr_code = ''")
    courses = cursor.fetchall()

    print(f"🔍 عُثر على {len(courses)} مادة بدون QR")

    for course in courses:
        qr_filename = generate_qr(course[0], course[1])
        cursor.execute("UPDATE courses SET qr_code = %s WHERE id = %s", (qr_filename, course[0]))
        print(f"✅ توليد QR للمادة: {course[1]} → {qr_filename}")

    db.commit()
    cursor.close()
    db.close()
    print("🎯 اكتملت العملية")
    rsor = db.cursor(dictionary=True)

    # 2. اختيار المواد يلي ما إلها QR
    cursor.execute("SELECT id, course_name FROM courses WHERE qr_code IS NULL OR qr_code = ''")
    courses = cursor.fetchall()

    print(f"📦 العثور على {len(courses)} مادة بدون QR")

    # 3. توليد وتحديث
    for course in courses:
        qr_filename = generate_qr(course["id"], course["course_name"])
        cursor.execute("UPDATE courses SET qr_code = %s WHERE id = %s", (qr_filename, course["id"]))
        print(f"✅ توليد QR للمادة: {course['course_name']} → {qr_filename}")

    db.commit()
    cursor.close()
    db.close()
    print("🎯 اكتملت العملية.")

from flask import Flask, render_template
import psycopg2

app = Flask(__name__)
app.secret_key = "mysecret"

@app.route("/")
def home():
    return render_template("student_login.html")



# شغّل توليد QR بعد تعريف كل شي
if __name__ == "__main__":
    generate_missing_qr()


# ✅ الاتصال بقاعدة البيانات
import os
import psycopg2


def get_db_connection():
    return psycopg2.connect(

        dbname="neondb",
        user="neondb_owner",
        password="npg_VU8tyFNlW0IK",    
        host="ep-withered-snow-aeck2exl-pooler.c-2.us-east-2.aws.neon.tech",
        port="5432",
        sslmode="require"
    )



if __name__ == "__main__":
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1;")
    print("نتيجة الاتصال:", cur.fetchone())
    cur.close()
    conn.close()
   



# ✅ إدارة الطلاب
@app.route("/students")
def students():
    search_id = request.args.get("search_id")
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    if search_id:
        cursor.execute("""
            SELECT students.id, students.full_name, students.university_id,
                   departments.department_name, years.year_name
            FROM students
            JOIN departments ON students.department_id = departments.id
            JOIN years ON students.year_id = years.id
            WHERE students.university_id = %s
        """, (search_id,))
    else:
        cursor.execute("""
            SELECT students.id, students.full_name, students.university_id,
                   departments.department_name, years.year_name
            FROM students
            JOIN departments ON students.department_id = departments.id
            JOIN years ON students.year_id = years.id
        """)

    students_list = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template("students.html", students=students_list)


@app.route("/add_student", methods=["POST"])
def add_student():
    full_name = request.form["full_name"]
    university_id = request.form["university_id"]
    department_id = request.form["department_id"]
    year_id = request.form["year_id"]

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("INSERT INTO students (full_name, university_id, department_id, year_id) VALUES (%s, %s, %s, %s)", 
               (full_name, university_id, department_id, year_id))

    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('students'))

@app.route("/delete_student/<int:id>")
def delete_student(id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM students WHERE id = %s", (id,))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('students'))


@app.route("/edit_student/<int:id>", methods=["POST"])
def edit_student(id):
    full_name = request.form["full_name"]
    university_id = request.form["university_id"]
    department_id = request.form.get("department_id")


    year_id = request.form["year_id"]

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE students SET full_name = %s, university_id = %s,
        department_id = %s, year_id = %s WHERE id = %s
    """, (full_name, university_id, department_id, year_id, id))
    db.commit()
    cursor.close()
    db.close()

    return redirect(url_for("students"))






# ✅ إدارة الأقسام
@app.route("/departments")
def departments():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM departments")
    departments_list = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template("departments.html", departments=departments_list)

@app.route("/add_department", methods=["POST"])
def add_department():
    department_name = request.form["department_name"]
    year_id = request.form["year_id"]
     
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("INSERT INTO departments (department_name , year_id) VALUES (%s, %s)", (department_name, year_id))

    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('departments'))


@app.route("/delete_department/<int:id>")
def delete_department(id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM departments WHERE id = %s", (id,))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('departments'))

@app.route("/edit_department/<int:department_id>", methods=["POST"])
def edit_department(department_id):
    department_name = request.form["department_name"]
    year_id = request.form["year_id"]  # ← هذا السطر كان ناقص!

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE departments SET department_name = %s, year_id = %s WHERE id = %s",
        (department_name, year_id, department_id)
    )
    db.commit()
    cursor.close()
    db.close()
    return redirect("/departments")




@app.route("/courses")
def courses():
    search_name = request.args.get("search_name")  # ← إضافة البحث
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    if search_name:
        cursor.execute("""
            SELECT 
                courses.id, courses.course_name, courses.qr_code,
                departments.department_name, departments.id AS department_id,
                years.year_name, years.id AS year_id,
                semesters.semester_name, semesters.id AS semester_id
            FROM courses
            JOIN departments ON courses.department_id = departments.id
            JOIN years ON courses.year_id = years.id
            JOIN semesters ON courses.semester_id = semesters.id
            WHERE courses.course_name LIKE %s
        """, ("%" + search_name + "%",))
    else:
        cursor.execute("""
            SELECT 
                courses.id, courses.course_name, courses.qr_code,
                departments.department_name, departments.id AS department_id,
                years.year_name, years.id AS year_id,
                semesters.semester_name, semesters.id AS semester_id
            FROM courses
            JOIN departments ON courses.department_id = departments.id
            JOIN years ON courses.year_id = years.id
            JOIN semesters ON courses.semester_id = semesters.id
        """)

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

    # إدخال المادة بدون QR بالبداية
    cursor.execute("""
        INSERT INTO courses (course_name, department_id, year_id, semester_id, qr_code)
        VALUES (%s, %s, %s, %s, %s)
    """, (course_name, department_id, year_id, semester_id, None))

    course_id = cursor.lastrowid

    # توليد QR وتحديث القاعدة
    qr_filename = generate_qr(course_id, course_name)
    cursor.execute("UPDATE courses SET qr_code = %s WHERE id = %s", (qr_filename, course_id))

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
    return redirect(url_for('courses'))


@app.route("/edit_course/<int:course_id>", methods=["POST"])
def edit_course(course_id):
    course_name = request.form["course_name"]
    department_id = request.form["department_id"]
    year_id = request.form["year_id"]
    semester_id = request.form["semester_id"]

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("UPDATE courses SET course_name = %s, department_id = %s, year_id = %s,  semester_id = %s WHERE id = %s",
                   (course_name, department_id, year_id, semester_id , course_id))
    db.commit()
    cursor.close()
    db.close()
    return redirect("/courses")




# ✅ إدارة سجل الحضور
@app.route("/attendance")
def attendance():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT students.full_name, courses.course_name, attendance.attendance_date, attendance.status FROM attendance "
                   "JOIN students ON attendance.student_id = students.id "
                   "JOIN courses ON attendance.course_id = courses.id")
    attendance_records = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template("attendance.html", attendance=attendance_records)

@app.route("/add_attendance", methods=["POST"])
def add_attendance():
    student_id = request.form["student_id"]
    course_id = request.form["course_id"]
    date = request.form["date"]
    status = request.form["status"]

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("INSERT INTO attendance (student_id, course_id, attendance_date, status) VALUES (%s, %s, %s, %s)", 
                   (student_id, course_id, date, status))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('attendance'))

@app.route("/delete_attendance/<int:id>")
def delete_attendance(id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM attendance WHERE id = %s", (id,))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('attendance'))

@app.route("/edit_attendance/<int:attendance_id>", methods=["POST"])
def edit_attendance(attendance_id):
    student_id = request.form["student_id"]
    course_id = request.form["course_id"]
    attendance_date = request.form["attendance_date"]
    attendance_time = request.form["attendance_time"]
    db = get_db_connection() 
    cursor = db.cursor()
    cursor.execute("UPDATE attendance SET student_id = %s, course_id = %s, attendance_date = %s, attendance_time = %s WHERE id = %s",
               (student_id, course_id, attendance_date, attendance_time, attendance_id))

    db.commit()
    cursor.close()
    db.close()


    
    return redirect("/attendance")



# ✅ إدارة السنوات والفصول الدراسية
@app.route("/years")
def years():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM years")
    years_list = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template("years.html", years=years_list)

@app.route("/add_year", methods=["POST"])
def add_year():
    year_name = request.form["year_name"]
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("INSERT INTO years (year_name) VALUES (%s)", (year_name,))

    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('years'))

@app.route("/delete_year/<int:id>")
def delete_year(id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM years WHERE id = %s", (id,))

    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('years'))

@app.route("/edit_year/<int:id>", methods=["POST"])
def edit_year(id):
    year_name = request.form["year_name"]
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("UPDATE years SET year_name = %s WHERE id = %s", (year_name, id))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('years'))




@app.route("/semesters")
def semesters():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""SELECT semesters.id, semesters.semester_name, years.year_name,
                      semesters.department_name, semesters.start_date, semesters.end_date
                      FROM semesters
                      JOIN years ON semesters.year_id = years.id
                      """)


    semesters_list = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template("semesters.html", semesters=semesters_list)

@app.route("/add_semester", methods=["POST"])
def add_semester():  # ← أضف هذا السطر
    semester_name = request.form["semester_name"]
    year_id = request.form["year_id"]
    department_name = request.form["department_name"]

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("""INSERT INTO semesters (semester_name, year_id, department_name)
                       VALUES (%s, %s, %s)""", (semester_name, year_id, department_name))

    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('semesters'))



@app.route("/delete_semester/<int:id>")
def delete_semester(id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM semesters WHERE id = %s", (id,))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('semesters'))



@app.route("/edit_semester/<int:id>", methods=["POST"])
def edit_semester(id):
    start_date = request.form["start_date"]
    end_date = request.form["end_date"]
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("UPDATE semesters SET start_date = %s , end_date = %s WHERE id = %s", (start_date, end_date, id))


    db.commit()
    cursor.close()
    db.close()
    
    return redirect("/semesters")

@app.route("/teacher_login", methods=["POST"])
def teacher_login():
    university_id = request.form["university_id"]
    password = request.form["password"]

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM teachers WHERE university_id = %s", (university_id,))
    teacher = cursor.fetchone()
    cursor.close()
    db.close()

    if teacher and teacher["password"] == password:
        session["teacher_id"] = teacher["id"]  # حفظ رقم المدرّس
        return redirect("/dashboard")
    else:
        return render_template("login.html", error=True)

@app.route("/login", methods=["POST"])
def login_post():
    university_id = request.form.get("university_id")
    password = request.form.get("password")

    if not university_id or not password:
        return render_template("login.html", error="يرجى تعبئة كل الحقول")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM teachers WHERE university_id = %s AND password = %s", (university_id, password))
    teacher = cursor.fetchone()
    cursor.close()
    db.close()

    if teacher:
        session["teacher_id"] = teacher["id"]
        return redirect("/dashboard")
    else:
        return render_template("login.html", error="الرقم الجامعي أو كلمة المرور غير صحيحة")


@app.route("/login")
def login_get():
    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    teacher_id = session.get("teacher_id")  # تأكد أنه موجود
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT t.full_name, t.university_id, t.education_level,
               d.department_name, y.year_name
        FROM teachers t
        LEFT JOIN departments d ON t.department_id = d.id
        LEFT JOIN years y ON t.year_id = y.id
        WHERE t.id = %s
    """, (teacher_id,))
    
    teacher_info = cursor.fetchone()

    cursor.close()
    db.close()

    return render_template("dashboard.html", teacher=teacher_info)





@app.route("/teachers")
def show_teachers():
    search_id = request.args.get("search_id")
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    if search_id:
        cursor.execute("""
            SELECT t.full_name, t.university_id, t.education_level,
                   d.department_name, y.year_name
            FROM teachers t
            LEFT JOIN departments d ON t.department_id = d.id
            LEFT JOIN years y ON t.year_id = y.id
            WHERE t.university_id = %s
        """, (search_id,))
    else:
        cursor.execute("""
            SELECT t.full_name, t.university_id, t.education_level,
                   d.department_name, y.year_name
            FROM teachers t
            LEFT JOIN departments d ON t.department_id = d.id
            LEFT JOIN years y ON t.year_id = y.id
        """)

    teachers = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template("teachers.html", teachers=teachers)









@app.route("/export_teachers")
def export_teachers():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            teachers.full_name AS 'الاسم الكامل',
            teachers.university_id AS 'الرقم الجامعي',
            teachers.education_level AS 'المؤهل العلمي',
            departments.department_name AS 'القسم',
            GROUP_CONCAT(years.year_name SEPARATOR ', ') AS 'السنين'
        FROM teachers
        LEFT JOIN departments ON teachers.department_id = departments.id
        LEFT JOIN years ON FIND_IN_SET(years.id, teachers.year_ids)
        GROUP BY teachers.id
    """)
    data = cursor.fetchall()
    cursor.close()
    db.close()

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Teachers")
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="teachers.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.route("/export_students")
def export_students():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students")
    data = cursor.fetchall()
    cursor.close()
    db.close()

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Students")
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="students.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@app.route("/export_attendance")
def export_attendance():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM attendance")  # عدّل حسب أعمدة الجدول
    data = cursor.fetchall()
    cursor.close()
    db.close()

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Attendance")
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="attendance.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.route("/export_departments")
def export_departments():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM departments")
    data = cursor.fetchall()
    cursor.close()
    db.close()

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Departments")
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="departments.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@app.route("/export_courses")
def export_courses():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM courses")
    data = cursor.fetchall()
    cursor.close()
    db.close()

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Courses")
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="courses.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.route("/export_semesters")
def export_semesters():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM semesters")
    data = cursor.fetchall()
    cursor.close()
    db.close()

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Semesters")
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="semesters.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.route("/export_years")
def export_years():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM years")
    data = cursor.fetchall()
    cursor.close()
    db.close()

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Years")
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="years.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@app.route("/register")
def register():
    # تحميل الأقسام والسنوات لعرضها بالصفحة
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM departments")
    departments = cursor.fetchall()

    cursor.execute("SELECT * FROM years")
    years = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("register.html", departments=departments, years=years)


@app.route("/register", methods=["POST"])
def register_post():
    full_name = request.form["full_name"]
    university_id = request.form["university_id"]
    education_level = request.form["education_level"]
    password = request.form["password"]
    department_id = request.form["department_id"]
    year_ids = ",".join(request.form.getlist("year_ids"))

    db = get_db_connection()
    cursor = db.cursor()

    # تحقق إذا الرقم الجامعي مكرر
    cursor.execute("SELECT id FROM teachers WHERE university_id = %s", (university_id,))
    if cursor.fetchone():
        cursor.close()
        db.close()
        return render_template("register.html", error="الرقم الجامعي مسجّل مسبقًا")

    # إدخال المدرّس الجديد
    cursor.execute("""
        INSERT INTO teachers (full_name, university_id, education_level, password, department_id, year_ids)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (full_name, university_id, education_level, password, department_id, year_ids))
    db.commit()
    cursor.close()
    db.close()

    # نحفظ بياناته مؤقتًا لتعبئتها لاحقًا بصفحة تسجيل الدخول
    session["last_user"] = {
        "university_id": university_id,
        "password": password
    }

    return redirect("/login")


    # حفظ بيانات المدرّس مؤقتًا في الجلسة لتعبئتها عند العودة
    session["last_user"] = {"university_id": university_id, "password": password}
    return redirect("/login")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")






@app.route("/student_login", methods=["GET", "POST"])
def student_login_page():
    

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        university_id = request.form.get("university_id", "").strip()

        if not full_name or not university_id:
            return render_template("student_login.html", error="يرجى إدخال جميع الحقول")

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM students WHERE full_name = %s AND university_id = %s", (full_name, university_id))
        student = cursor.fetchone()
        cursor.close()
        db.close()

        if student:
            session["student_id"] = student["id"]
            session["student_name"] = student["full_name"]
            return redirect("/student_dashboard")
        else:
            return render_template("student_login.html", error="الاسم أو الرقم غير صحيح")

    return render_template("student_login.html")





@app.route("/student_dashboard")
def student_dashboard():
    # التحقق من أن الطالب مسجل دخول
    if "student_id" not in session:
        return redirect("/student_login")

    # الاتصال بقاعدة البيانات
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # جلب السنوات والأقسام والفصول
    cursor.execute("SELECT * FROM years")
    years = cursor.fetchall()

    cursor.execute("SELECT * FROM departments")
    departments = cursor.fetchall()

    cursor.execute("SELECT * FROM semesters")
    semesters = cursor.fetchall()

    cursor.close()
    db.close()

    # عرض صفحة الطالب مع البيانات
    return render_template(
        "student_dashboard.html",
        student_name=session["student_name"],
        years=years,
        departments=departments,
        semesters=semesters
    )



@app.route("/student_courses")
def student_courses():
    year_id = request.args.get("year_id")
    semester_id = request.args.get("semester_id")
    department_id = request.args.get("department_id")

    if not year_id or not semester_id:
        return "يرجى اختيار السنة والفصل على الأقل.", 400

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # بناء الاستعلام بناءً على إذا القسم موجود أو لا
    if department_id:
        query = """
            SELECT * FROM courses
            WHERE year_id = %s AND semester_id = %s AND department_id = %s
        """
        cursor.execute(query, (year_id, semester_id, department_id))
    else:
        query = """
            SELECT * FROM courses
            WHERE year_id = %s AND semester_id = %s AND department_id IS NULL
        """
        cursor.execute(query, (year_id, semester_id))

    courses = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template("student_courses.html", courses=courses)
from flask import render_template, request
import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="attendance_system"
    )

@app.route("/confirm_attendance")
def confirm_attendance():
    course_id = request.args.get("course_id")
    student_id = request.args.get("student_id")

    if not course_id or not student_id:
        return "البيانات ناقصة", 400

    db = get_db_connection()
    cursor = db.cursor()

    # تحقق من الطالب والمادة (اختياري لكن مهم)
    cursor.execute("SELECT full_name FROM students WHERE id = %s", (student_id,))
    student = cursor.fetchone()

    cursor.execute("SELECT course_name FROM courses WHERE id = %s", (course_id,))
    course = cursor.fetchone()

    if not student or not course:
        cursor.close()
        db.close()
        return "الطالب أو المادة غير موجودة", 404

    # إدخال سجل الحضور
    cursor.execute("""
        INSERT INTO attendance (course_id, student_id, attendance_date)
        VALUES (%s, %s, CURDATE())
    """, (course_id, student_id))

    db.commit()
    cursor.close()
    db.close()

    return render_template("attendance_success.html", student=student[0], course=course[0])




@app.route('/record_attendance', methods=['POST'])
def record_attendance():
    data = request.get_json()
    qr_url = data.get('url', '')

    # الاتصال بقاعدة البيانات
    db = get_db_connection()
    cursor = db.cursor()

    # استخراج البيانات من الرابط
    parsed = urllib.parse.urlparse(qr_url)
    params = urllib.parse.parse_qs(parsed.query)

    course_id = params.get('course_id', [''])[0]
    student_id = params.get('student_id', [''])[0]

    # تحقق من وجود الطالب والمادة
    cursor.execute("SELECT full_name, university_id FROM students WHERE id = %s", (student_id,))
    student = cursor.fetchone()

    cursor.execute("SELECT course_name FROM courses WHERE id = %s", (course_id,))
    course = cursor.fetchone()

    if student and course:
        # تحقق من عدم تسجيل الحضور مسبقًا (تم تصحيح اسم العمود من timestamp إلى attendance_date)
        cursor.execute("""
            SELECT id FROM attendance
            WHERE student_university_id = %s AND course_name = %s AND DATE(attendance_date) = CURDATE()
        """, (student[1], course[0]))
        existing = cursor.fetchone()

        if not existing:
            cursor.execute("""
                INSERT INTO attendance (student_name, student_university_id, course_name, status, attendance_date)
                VALUES (%s, %s, %s, 'حاضر', CURDATE())
            """, (student[0], student[1], course[0]))
            db.commit()
            cursor.close()
            db.close()
            return jsonify({"status": "ok"})
        else:
            cursor.close()
            db.close()
            return jsonify({"status": "duplicate"})

    cursor.close()
    db.close()
    return jsonify({"status": "fail"})




    
from flask import Flask, request
import os
import psycopg2  # ← تأكد إنها موجودة لو بتستخدم Neon




app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(
        dbname="neondb",
        user="neondb_owner",
        password="npg_VU8tyFNlW0IK",
        host="ep-withered-snow-aeck2exl-pooler.c-2.us-east-2.aws.neon.tech",
        port="5432",
        sslmode="require"
    )

@app.route("/scan_qr")
def scan_qr():

    student_id = request.args.get("student_id")
    course_id = request.args.get("course_id")

    if not student_id or not course_id:
        return "❌ بيانات ناقصة"

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO attendance (student_id, course_id, attendance_date, attendance_time, status)
        VALUES (%s, %s, CURRENT_DATE, CURRENT_TIME, 'حاضر');
    """, (student_id, course_id))
    conn.commit()
    cur.close()
    conn.close()

    return f"✔️ تم تسجيل حضور الطالب {student_id} للمادة {course_id}"



if __name__ == '__main__':
    import os
   
    ...







