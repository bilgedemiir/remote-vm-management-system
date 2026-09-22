from backend.database.connection import (
    get_db_connection,
    get_db_cursor
)


def save_execution_result(
    execution_id,
    exit_code,
    stdout,
    stderr,
    duration_ms=None,
    executed_by=None
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        query = """
            INSERT INTO execution_results
            (
                execution_id,
                exit_code,
                stdout,
                stderr,
                duration_ms,
                executed_by
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            ON DUPLICATE KEY UPDATE
                exit_code = VALUES(exit_code),
                stdout = VALUES(stdout),
                stderr = VALUES(stderr),
                duration_ms = VALUES(duration_ms),
                executed_by = VALUES(executed_by),
                received_at = CURRENT_TIMESTAMP
        """

        cursor.execute(
            query,
            (
                execution_id,
                exit_code,
                stdout,
                stderr,
                duration_ms,
                executed_by
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


def get_result_by_execution(execution_id):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        query = """
            SELECT *
            FROM execution_results
            WHERE execution_id = %s
        """

        cursor.execute(
            query,
            (execution_id,)
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


def delete_result(execution_id):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        query = """
            DELETE FROM execution_results
            WHERE execution_id = %s
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