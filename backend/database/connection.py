import mysql.connector
from backend.config import Config


def get_db_connection():
    return mysql.connector.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME
    )


def get_db_cursor(connection):
    return connection.cursor(dictionary=True)