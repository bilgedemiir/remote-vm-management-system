from backend.database.connection import (
    get_db_connection,
    get_db_cursor
)


def create_log(
    level,
    event_type,
    message,
    user_id=None,
    client_id=None,
    execution_id=None,
    ip_address=None
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    query = """
        INSERT INTO logs
        (
            level,
            event_type,
            user_id,
            client_id,
            execution_id,
            ip_address,
            message,
            created_at
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            NOW()
        )
    """

    cursor.execute(
        query,
        (
            level,
            event_type,
            user_id,
            client_id,
            execution_id,
            ip_address,
            message
        )
    )

    connection.commit()

    log_id = cursor.lastrowid

    cursor.close()
    connection.close()

    return log_id


def get_log_by_id(log_id):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    query = """
        SELECT *
        FROM logs
        WHERE id = %s
    """

    cursor.execute(query, (log_id,))

    log = cursor.fetchone()

    cursor.close()
    connection.close()

    return log


def get_all_logs():
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    query = """
        SELECT
            logs.id,
            logs.level,
            logs.event_type AS log_type,
            logs.message AS description,
            logs.user_id,
            logs.client_id,
            logs.execution_id,
            logs.created_at,
            logs.ip_address,
            users.username,
            clients.hostname
        FROM logs
        LEFT JOIN users
            ON logs.user_id = users.id
        LEFT JOIN clients
            ON logs.client_id = clients.id
        ORDER BY logs.created_at DESC
    """

    cursor.execute(query)

    logs = cursor.fetchall()

    cursor.close()
    connection.close()

    return logs


def get_logs_by_client(client_id):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    query = """
        SELECT *
        FROM logs
        WHERE client_id = %s
        ORDER BY created_at DESC
    """

    cursor.execute(query, (client_id,))

    logs = cursor.fetchall()

    cursor.close()
    connection.close()

    return logs


def get_logs_by_user(user_id):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    query = """
        SELECT *
        FROM logs
        WHERE user_id = %s
        ORDER BY created_at DESC
    """

    cursor.execute(query, (user_id,))

    logs = cursor.fetchall()

    cursor.close()
    connection.close()

    return logs


def get_logs_by_execution(execution_id):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    query = """
        SELECT *
        FROM logs
        WHERE execution_id = %s
        ORDER BY created_at DESC
    """

    cursor.execute(query, (execution_id,))

    logs = cursor.fetchall()

    cursor.close()
    connection.close()

    return logs


def get_logs_by_level(level):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    query = """
        SELECT *
        FROM logs
        WHERE level = %s
        ORDER BY created_at DESC
    """

    cursor.execute(query, (level,))

    logs = cursor.fetchall()

    cursor.close()
    connection.close()

    return logs


def delete_old_logs(days):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    query = """
        DELETE
        FROM logs
        WHERE created_at < DATE_SUB(NOW(), INTERVAL %s DAY)
    """

    cursor.execute(query, (days,))

    connection.commit()

    deleted = cursor.rowcount

    cursor.close()
    connection.close()

    return deleted


def build_log_filters(
    search="",
    event_type="",
    level="",
    start_date="",
    end_date=""
):
    conditions = []
    parameters = []

    if search:
        search_value = f"%{search}%"

        conditions.append(
            """
            (
                logs.message LIKE %s
                OR logs.ip_address LIKE %s
                OR users.username LIKE %s
                OR clients.hostname LIKE %s
            )
            """
        )

        parameters.extend(
            [
                search_value,
                search_value,
                search_value,
                search_value
            ]
        )

    if event_type:
        conditions.append(
            "logs.event_type = %s"
        )
        parameters.append(event_type)

    if level:
        conditions.append(
            "logs.level = %s"
        )
        parameters.append(level)

    if start_date:
        conditions.append(
            "DATE(logs.created_at) >= %s"
        )
        parameters.append(start_date)

    if end_date:
        conditions.append(
            "DATE(logs.created_at) <= %s"
        )
        parameters.append(end_date)

    if conditions:
        where_clause = (
            "WHERE " + " AND ".join(conditions)
        )
    else:
        where_clause = ""

    return where_clause, parameters


def get_paginated_logs(
    page,
    per_page,
    search="",
    event_type="",
    level="",
    start_date="",
    end_date=""
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        page = max(page, 1)
        per_page = max(per_page, 1)

        offset = (page - 1) * per_page

        where_clause, parameters = build_log_filters(
            search=search,
            event_type=event_type,
            level=level,
            start_date=start_date,
            end_date=end_date
        )

        query = f"""
            SELECT
                logs.id,
                logs.level,
                logs.event_type AS log_type,
                logs.message AS description,
                logs.user_id,
                logs.client_id,
                logs.execution_id,
                logs.created_at,
                logs.ip_address,
                users.username,
                clients.hostname,
                clients.ip_address AS client_ip_address
            FROM logs
            LEFT JOIN users
                ON logs.user_id = users.id
            LEFT JOIN clients
                ON logs.client_id = clients.id
            {where_clause}
            ORDER BY logs.created_at DESC
            LIMIT %s OFFSET %s
        """

        parameters.extend(
            [
                per_page,
                offset
            ]
        )

        cursor.execute(
            query,
            tuple(parameters)
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def count_filtered_logs(
    search="",
    event_type="",
    level="",
    start_date="",
    end_date=""
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        where_clause, parameters = build_log_filters(
            search=search,
            event_type=event_type,
            level=level,
            start_date=start_date,
            end_date=end_date
        )

        query = f"""
            SELECT COUNT(*) AS total
            FROM logs
            LEFT JOIN users
                ON logs.user_id = users.id
            LEFT JOIN clients
                ON logs.client_id = clients.id
            {where_clause}
        """

        cursor.execute(
            query,
            tuple(parameters)
        )

        result = cursor.fetchone()

        return result["total"]

    finally:
        cursor.close()
        connection.close()


def get_log_event_types():
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        query = """
            SELECT DISTINCT event_type
            FROM logs
            WHERE event_type IS NOT NULL
            ORDER BY event_type
        """

        cursor.execute(query)

        return [
            row["event_type"]
            for row in cursor.fetchall()
        ]

    finally:
        cursor.close()
        connection.close()