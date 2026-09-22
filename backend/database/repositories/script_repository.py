from backend.database.connection import (
    get_db_connection,
    get_db_cursor
)


def create_script(
    name,
    description,
    category,
    created_by
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    query = """
        INSERT INTO scripts
        (
            name,
            description,
            category,
            created_by
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s
        )
    """

    cursor.execute(
        query,
        (
            name,
            description,
            category,
            created_by
        )
    )

    connection.commit()

    script_id = cursor.lastrowid

    cursor.close()
    connection.close()

    return script_id


def get_script_by_id(script_id):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    query = """
        SELECT *
        FROM scripts
        WHERE id = %s
    """

    cursor.execute(query, (script_id,))

    script = cursor.fetchone()

    cursor.close()
    connection.close()

    return script


def get_script_by_name(name):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    query = """
        SELECT *
        FROM scripts
        WHERE name = %s
    """

    cursor.execute(query, (name,))

    script = cursor.fetchone()

    cursor.close()
    connection.close()

    return script


def get_all_scripts():
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    query = """
        SELECT
            s.*,
            u.full_name AS created_by_name
        FROM scripts s
        LEFT JOIN users u
            ON s.created_by = u.id
        ORDER BY s.name
    """

    cursor.execute(query)

    scripts = cursor.fetchall()

    cursor.close()
    connection.close()

    return scripts


def get_active_scripts():
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    query = """
        SELECT *
        FROM scripts
        WHERE is_active = TRUE
        ORDER BY name
    """

    cursor.execute(query)

    scripts = cursor.fetchall()

    cursor.close()
    connection.close()

    return scripts


def update_script(
    script_id,
    name,
    description,
    category,
    current_version
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    query = """
        UPDATE scripts
        SET
            name = %s,
            description = %s,
            category = %s,
            current_version = %s
        WHERE id = %s
    """

    cursor.execute(
        query,
        (
            name,
            description,
            category,
            current_version,
            script_id
        )
    )

    connection.commit()

    cursor.close()
    connection.close()


def set_script_active(
    script_id,
    is_active
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    query = """
        UPDATE scripts
        SET
            is_active = %s
        WHERE id = %s
    """

    cursor.execute(
        query,
        (
            is_active,
            script_id
        )
    )

    connection.commit()

    cursor.close()
    connection.close()


def delete_script(script_id):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    query = """
        DELETE
        FROM scripts
        WHERE id = %s
    """

    cursor.execute(query, (script_id,))

    connection.commit()

    cursor.close()
    connection.close()

def update_current_version(
    script_id,
    current_version
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    query = """
        UPDATE scripts
        SET current_version = %s
        WHERE id = %s
    """

    cursor.execute(
        query,
        (
            current_version,
            script_id
        )
    )

    connection.commit()

    cursor.close()
    connection.close()