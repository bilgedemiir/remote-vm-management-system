from database.connection import get_db_connection


def find_user_by_username(username):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = "SELECT * FROM users WHERE username = %s"
    cursor.execute(query, (username,))

    user = cursor.fetchone()

    cursor.close()
    connection.close()

    return user