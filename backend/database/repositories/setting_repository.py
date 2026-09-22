from backend.database.connection import (
    get_db_connection,
    get_db_cursor
)


def get_setting(setting_key):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    query = """
        SELECT *
        FROM settings
        WHERE setting_key = %s
    """

    cursor.execute(query, (setting_key,))

    setting = cursor.fetchone()

    cursor.close()
    connection.close()

    return setting


def get_setting_value(setting_key):
    setting = get_setting(setting_key)

    if setting:
        return setting["setting_value"]

    return None


def get_all_settings():
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    query = """
        SELECT *
        FROM settings
        ORDER BY setting_key
    """

    cursor.execute(query)

    settings = cursor.fetchall()

    cursor.close()
    connection.close()

    return settings


def update_setting(
    setting_key,
    setting_value
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    query = """
        UPDATE settings
        SET
            setting_value=%s,
            updated_at=NOW()
        WHERE setting_key=%s
    """

    cursor.execute(
        query,
        (
            setting_value,
            setting_key
        )
    )

    connection.commit()

    cursor.close()
    connection.close()