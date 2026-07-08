from database.connection import get_db_connection


def get_all_clients():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM clients ORDER BY id DESC")
    clients = cursor.fetchall()

    cursor.close()
    connection.close()

    return clients


def get_total_client_count():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM clients")
    count = cursor.fetchone()[0]

    cursor.close()
    connection.close()

    return count


def get_client_by_id(client_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = "SELECT * FROM clients WHERE id = %s"
    cursor.execute(query, (client_id,))

    client = cursor.fetchone()

    cursor.close()
    connection.close()

    return client


def register_or_update_client(hostname, ip_address, operating_system):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    check_query = """
        SELECT *
        FROM clients
        WHERE hostname = %s
    """
    cursor.execute(check_query, (hostname,))
    existing_client = cursor.fetchone()

    if existing_client:
        update_query = """
            UPDATE clients
            SET ip_address = %s,
                operating_system = %s,
                status = 'online',
                last_seen = CURRENT_TIMESTAMP
            WHERE hostname = %s
        """
        cursor.execute(update_query, (ip_address, operating_system, hostname))
    else:
        insert_query = """
            INSERT INTO clients (hostname, ip_address, operating_system, status)
            VALUES (%s, %s, %s, 'online')
        """
        cursor.execute(insert_query, (hostname, ip_address, operating_system))

    connection.commit()

    cursor.close()
    connection.close()


def set_client_offline(hostname):
    connection = get_db_connection()
    cursor = connection.cursor()

    query = """
        UPDATE clients
        SET status = 'offline',
            last_seen = CURRENT_TIMESTAMP
        WHERE hostname = %s
    """

    cursor.execute(query, (hostname,))
    connection.commit()

    cursor.close()
    connection.close()