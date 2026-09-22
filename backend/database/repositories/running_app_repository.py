from backend.database.connection import (
    get_db_connection,
    get_db_cursor
)


def replace_client_running_apps(
    client_id,
    running_apps
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
                DELETE FROM client_running_apps
                WHERE client_id = %s
            """,
            (client_id,)
        )

        query = """
            INSERT INTO client_running_apps
            (
                client_id,
                app_name,
                process_name,
                process_id,
                username,
                memory_mb,
                collected_at
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                NOW()
            )
        """

        values = []

        for app in running_apps:
            app_name = str(
                app.get("app_name") or ""
            ).strip()

            process_id = app.get("process_id")

            if not app_name or process_id is None:
                continue

            values.append(
                (
                    client_id,
                    app_name[:255],
                    str(
                        app.get("process_name") or ""
                    )[:255] or None,
                    int(process_id),
                    str(
                        app.get("username") or ""
                    )[:255] or None,
                    app.get("memory_mb")
                )
            )

        if values:
            cursor.executemany(
                query,
                values
            )

        connection.commit()

        return len(values)

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def get_paginated_running_apps(
    client_id,
    page,
    per_page,
    search=""
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        offset = (page - 1) * per_page
        parameters = [client_id]

        where_clause = """
            WHERE client_id = %s
        """

        if search:
            search_value = f"%{search}%"

            where_clause += """
                AND (
                    app_name LIKE %s
                    OR process_name LIKE %s
                    OR username LIKE %s
                    OR CAST(process_id AS CHAR) LIKE %s
                )
            """

            parameters.extend(
                [
                    search_value,
                    search_value,
                    search_value,
                    search_value
                ]
            )

        query = f"""
            SELECT
                id,
                app_name,
                process_name,
                process_id,
                username,
                memory_mb,
                collected_at
            FROM client_running_apps
            {where_clause}
            ORDER BY memory_mb DESC, app_name ASC
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


def count_running_apps(
    client_id,
    search=""
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        parameters = [client_id]

        where_clause = """
            WHERE client_id = %s
        """

        if search:
            search_value = f"%{search}%"

            where_clause += """
                AND (
                    app_name LIKE %s
                    OR process_name LIKE %s
                    OR username LIKE %s
                    OR CAST(process_id AS CHAR) LIKE %s
                )
            """

            parameters.extend(
                [
                    search_value,
                    search_value,
                    search_value,
                    search_value
                ]
            )

        query = f"""
            SELECT COUNT(*) AS total
            FROM client_running_apps
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