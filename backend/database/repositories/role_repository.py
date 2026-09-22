from backend.database.connection import (
    get_db_connection,
    get_db_cursor
)


def get_role_by_id(role_id):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    cursor.execute(
        """
        SELECT *
        FROM roles
        WHERE id=%s
        """,
        (role_id,)
    )

    role = cursor.fetchone()

    cursor.close()
    connection.close()

    return role


def get_role_by_name(name):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    cursor.execute(
        """
        SELECT *
        FROM roles
        WHERE name=%s
        """,
        (name,)
    )

    role = cursor.fetchone()

    cursor.close()
    connection.close()

    return role


def get_all_roles():
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    cursor.execute(
        """
        SELECT *
        FROM roles
        ORDER BY id
        """
    )

    roles = cursor.fetchall()

    cursor.close()
    connection.close()

    return roles