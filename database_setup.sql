CREATE DATABASE attendance_system;
USE attendance_system;

-- جدول السنوات
CREATE TABLE years (
    id INT AUTO_INCREMENT PRIMARY KEY,
    year_name VARCHAR(20) NOT NULL
);

-- جدول الأقسام
CREATE TABLE departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(50) NOT NULL
);

-- جدول الطلاب
CREATE TABLE students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    university_id VARCHAR(20) UNIQUE NOT NULL,
    department_id INT,
    year_id INT,
    FOREIGN KEY (department_id) REFERENCES departments(id),
    FOREIGN KEY (year_id) REFERENCES years(id)
);

-- جدول المواد
CREATE TABLE courses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_name VARCHAR(100) NOT NULL,
    department_id INT,
    year_id INT,
    qr_code TEXT NOT NULL,
    FOREIGN KEY (department_id) REFERENCES departments(id),
    FOREIGN KEY (year_id) REFERENCES years(id)
);

-- جدول الحضور
CREATE TABLE attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    course_id INT,
    attendance_date DATE NOT NULL,
    attendance_time TIME NOT NULL,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (course_id) REFERENCES courses(id)
);
