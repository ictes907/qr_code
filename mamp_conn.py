def get_mamp_connection():
    import pymysql
    return pymysql.connect(
        host="127.0.0.1",
        port=8889,
        user="root",
        password="root",
        database="attendance_system"
    )

