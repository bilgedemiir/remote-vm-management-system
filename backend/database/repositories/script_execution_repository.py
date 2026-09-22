from backend.database.connection import (
    get_db_connection,
    get_db_cursor
)


def create_execution(
    client_id,
    requested_by,
    script_content,
    timeout_seconds=300,
    priority="normal",
    rollback_script=None,
    rollback_of_execution_id=None,
    batch_id=None,
    execution_type="script"
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        query = """
            INSERT INTO script_executions
            (
                script_version_id,
                script_content,
                rollback_script,
                rollback_of_execution_id,
                batch_id,
                execution_type,
                client_id,
                requested_by,
                status,
                priority,
                timeout_seconds
            )
            VALUES
            (
                NULL,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                'pending',
                %s,
                %s
            )
        """

        cursor.execute(
            query,
            (
                script_content,
                rollback_script,
                rollback_of_execution_id,
                batch_id,
                execution_type,
                client_id,
                requested_by,
                priority,
                timeout_seconds
            )
        )

        connection.commit()

        return cursor.lastrowid

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def get_execution_by_id(execution_id):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        query = """
            SELECT
                se.*,
                er.exit_code,
                er.stdout,
                er.stderr,
                er.duration_ms,
                er.executed_by,
                er.received_at
            FROM script_executions AS se
            LEFT JOIN execution_results AS er
                ON er.execution_id = se.id
            WHERE se.id = %s
        """

        cursor.execute(
            query,
            (execution_id,)
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


def get_executions_by_client(client_id):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        query = """
            SELECT
                se.*,
                er.exit_code
            FROM script_executions AS se
            LEFT JOIN execution_results AS er
                ON er.execution_id = se.id
            WHERE se.client_id = %s
            ORDER BY se.queued_at DESC
        """

        cursor.execute(
            query,
            (client_id,)
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def get_pending_executions_by_client(client_id):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        query = """
            SELECT *
            FROM script_executions
            WHERE client_id = %s
              AND status = 'pending'
            ORDER BY
                FIELD(
                    priority,
                    'critical',
                    'high',
                    'normal',
                    'low'
                ),
                queued_at ASC
        """

        cursor.execute(
            query,
            (client_id,)
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def claim_pending_execution(execution_id):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        query = """
            UPDATE script_executions
            SET
                status = 'assigned',
                assigned_at = NOW()
            WHERE id = %s
              AND status = 'pending'
        """

        cursor.execute(
            query,
            (execution_id,)
        )

        connection.commit()
        return cursor.rowcount == 1

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def update_execution_status(execution_id, status):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        query = """
            UPDATE script_executions
            SET status = %s
            WHERE id = %s
        """

        cursor.execute(
            query,
            (
                status,
                execution_id
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


def update_started_time(execution_id):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        query = """
            UPDATE script_executions
            SET
                status = 'running',
                started_at = NOW()
            WHERE id = %s
        """

        cursor.execute(
            query,
            (execution_id,)
        )

        connection.commit()
        return cursor.rowcount > 0

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def update_finished_time(execution_id):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        query = """
            UPDATE script_executions
            SET finished_at = NOW()
            WHERE id = %s
        """

        cursor.execute(
            query,
            (execution_id,)
        )

        connection.commit()
        return cursor.rowcount > 0

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def update_agent_message(execution_id, message):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        query = """
            UPDATE script_executions
            SET agent_message = %s
            WHERE id = %s
        """

        cursor.execute(
            query,
            (
                message,
                execution_id
            )
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def get_recent_executions(limit=10):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        query = """
            SELECT
                se.id,
                se.status,
                se.queued_at,
                se.client_id,
                c.hostname,
                er.exit_code
            FROM script_executions AS se
            INNER JOIN clients AS c
                ON c.id = se.client_id
            LEFT JOIN execution_results AS er
                ON er.execution_id = se.id
            ORDER BY se.queued_at DESC
            LIMIT %s
        """

        cursor.execute(
            query,
            (limit,)
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def build_execution_filters(
    client_id,
    search="",
    status=""
):
    conditions = [
        "se.client_id = %s"
    ]

    parameters = [
        client_id
    ]

    if search:
        search_value = f"%{search}%"

        conditions.append(
            """
            (
                se.script_content LIKE %s
                OR users.username LIKE %s
                OR CAST(se.id AS CHAR) LIKE %s
            )
            """
        )

        parameters.extend(
            [
                search_value,
                search_value,
                search_value
            ]
        )

    if status in (
        "pending",
        "assigned",
        "running",
        "completed",
        "failed"
    ):
        conditions.append(
            "se.status = %s"
        )

        parameters.append(status)

    where_clause = (
        "WHERE " + " AND ".join(conditions)
    )

    return where_clause, parameters


def get_paginated_executions_by_client(
    client_id,
    page,
    per_page,
    search="",
    status=""
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        page = max(page, 1)
        per_page = max(per_page, 1)

        offset = (page - 1) * per_page

        where_clause, parameters = (
            build_execution_filters(
                client_id=client_id,
                search=search,
                status=status
            )
        )

        query = f"""
            SELECT
                se.*,
                users.username,
                er.exit_code
            FROM script_executions AS se
            LEFT JOIN users
                ON users.id = se.requested_by
            LEFT JOIN execution_results AS er
                ON er.execution_id = se.id
            {where_clause}
            ORDER BY se.queued_at DESC
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


def count_filtered_executions_by_client(
    client_id,
    search="",
    status=""
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        where_clause, parameters = (
            build_execution_filters(
                client_id=client_id,
                search=search,
                status=status
            )
        )

        query = f"""
            SELECT COUNT(*) AS total
            FROM script_executions AS se
            LEFT JOIN users
                ON users.id = se.requested_by
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


def set_rollback_execution(
    original_execution_id,
    rollback_execution_id
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        query = """
            UPDATE script_executions
            SET rollback_execution_id = %s
            WHERE id = %s
        """

        cursor.execute(
            query,
            (
                rollback_execution_id,
                original_execution_id
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


def mark_execution_rolled_back(
    original_execution_id
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        query = """
            UPDATE script_executions
            SET
                rolled_back = 1,
                rolled_back_at = NOW()
            WHERE id = %s
        """

        cursor.execute(
            query,
            (original_execution_id,)
        )

        connection.commit()

        return cursor.rowcount > 0

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def create_execution_batch(
    requested_by
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            INSERT INTO script_execution_batches
            (
                requested_by
            )
            VALUES
            (
                %s
            )
            """,
            (requested_by,)
        )

        connection.commit()

        return cursor.lastrowid

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def get_execution_batch_by_id(
    batch_id
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            SELECT
                b.*,
                u.username
            FROM script_execution_batches b
            LEFT JOIN users u
                ON u.id = b.requested_by
            WHERE b.id = %s
            """,
            (batch_id,)
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


def get_executions_by_batch(
    batch_id
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            SELECT
                se.id,
                se.client_id,
                se.script_content,
                se.status,
                se.queued_at,
                se.started_at,
                se.finished_at,
                se.timeout_seconds,

                c.hostname,
                c.ip_address,

                er.exit_code,
                er.duration_ms

            FROM script_executions se

            INNER JOIN clients c
                ON c.id = se.client_id

            LEFT JOIN execution_results er
                ON er.execution_id = se.id

            WHERE se.batch_id = %s

            ORDER BY c.hostname
            """,
            (batch_id,)
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()