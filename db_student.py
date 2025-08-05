import psycopg2

def get_db_connection():
    return psycopg2.connect(
        host="ep-withered-snow-aeck2exl-pooler.c-2.us-east-2.aws.neon.tech",
        database="neondb",
        user="neondb_owner",
        password="npg_2ogfihcX5JEO",
        port="5432",
        sslmode="require"
    )
