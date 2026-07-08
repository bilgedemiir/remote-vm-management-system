from database.connection import get_db_connection


def get_commands_by_client_id(client_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT *
        FROM commands
        WHERE client_id = %s
        ORDER BY created_at DESC
    """

    cursor.execute(query, (client_id,))
    commands = cursor.fetchall()

    cursor.close()
    connection.close()

    return commands