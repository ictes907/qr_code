def get_mamp_connection():
    import pymysql
    return pymysql.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="root",
        database="attendance_system"
    )

