import hashlib

from backend.database.connection import (
    get_db_connection,
    get_db_cursor
)


def calculate_script_hash(script_content):
    return hashlib.sha256(
        script_content.encode("utf-8")
    ).hexdigest()


def create_script_version(
    script_id,
    version_number,
    title,
    script_content,
    created_by,
    change_log
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    script_hash = calculate_script_hash(script_content)

    query = """
        INSERT INTO script_versions
        (
            script_id,
            version_number,
            title,
            script_content,
            script_hash,
            created_by,
            change_log
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
    """

    cursor.execute(
        query,
        (
            script_id,
            version_number,
            title,
            script_content,
            script_hash,
            created_by,
            change_log
        )
    )

    connection.commit()

    version_id = cursor.lastrowid

    cursor.close()
    connection.close()

    return version_id


def get_version_by_id(version_id):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    query = """
        SELECT *
        FROM script_versions
        WHERE id = %s
    """

    cursor.execute(query, (version_id,))

    version = cursor.fetchone()

    cursor.close()
    connection.close()

    return version


def get_versions(script_id):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    query = """
        SELECT *
        FROM script_versions
        WHERE script_id = %s
        ORDER BY version_number DESC
    """

    cursor.execute(query, (script_id,))

    versions = cursor.fetchall()

    cursor.close()
    connection.close()

    return versions


def get_latest_version(script_id):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    query = """
        SELECT *
        FROM script_versions
        WHERE script_id = %s
        ORDER BY version_number DESC
        LIMIT 1
    """

    cursor.execute(query, (script_id,))

    version = cursor.fetchone()

    cursor.close()
    connection.close()

    return version


def get_next_version_number(script_id):
    latest = get_latest_version(script_id)

    if latest is None:
        return 1

    return latest["version_number"] + 1


def delete_version(version_id):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    query = """
        DELETE
        FROM script_versions
        WHERE id = %s
    """

    cursor.execute(query, (version_id,))

    connection.commit()

    cursor.close()
    connection.close()