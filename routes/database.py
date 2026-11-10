import mysql.connector
from mysql.connector import Error


DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "finora_db",
}


def get_db():
    try:
        connection = mysql.connector.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"]
        )

        return connection

    except Error as e:
        print("========================================")
        print("DATABASE ERROR")
        print("========================================")
        print(e)
        print("========================================")
        raise


def test_connection():

    connection = None

    try:

        connection = get_db()

        if connection.is_connected():

            print("========================================")
            print("DATABASE FINORA BERHASIL TERHUBUNG")
            print("========================================")

            cursor = connection.cursor()

            cursor.execute("SELECT DATABASE()")

            result = cursor.fetchone()

            print("Database aktif :", result[0])

            cursor.close()

            return True

    except Error as e:

        print("========================================")
        print("DATABASE FINORA GAGAL TERHUBUNG")
        print("========================================")

        print(e)

        return False

    finally:

        if connection and connection.is_connected():
            connection.close()