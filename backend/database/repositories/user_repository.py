from backend.database.connection import (
    get_db_connection,
    get_db_cursor
)


def get_user_by_id(user_id):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        query = """
            SELECT
                users.*,
                roles.name AS role_name
            FROM users
            INNER JOIN roles
                ON users.role_id = roles.id
            WHERE users.id = %s
        """

        cursor.execute(query, (user_id,))
        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


def get_user_by_username(username):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        query = """
            SELECT
                users.*,
                roles.name AS role_name
            FROM users
            INNER JOIN roles
                ON users.role_id = roles.id
            WHERE users.username = %s
        """

        cursor.execute(query, (username,))
        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


def get_all_users():
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        query = """
            SELECT
                users.*,
                roles.name AS role_name
            FROM users
            INNER JOIN roles
                ON users.role_id = roles.id
            ORDER BY users.full_name
        """

        cursor.execute(query)
        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def update_last_login(user_id):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        query = """
            UPDATE users
            SET last_login = NOW()
            WHERE id = %s
        """

        cursor.execute(query, (user_id,))
        connection.commit()

        return cursor.rowcount > 0

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def set_user_active(user_id, is_active):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        query = """
            UPDATE users
            SET is_active = %s
            WHERE id = %s
        """

        cursor.execute(
            query,
            (
                is_active,
                user_id
            )
        )

        connection.commit()
        return cursor.rowcount > 0

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()