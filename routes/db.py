import mysql.connector


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = ""
DB_NAME = "finora"


# ============================================================
# GET DATABASE CONNECTION
# ============================================================

def get_db():
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )

        return connection

    except mysql.connector.Error as e:
        print("DATABASE CONNECTION ERROR:", e)
        raise