from backend.database.connection import (
    get_db_connection,
    get_db_cursor
)


def replace_client_installed_apps(
    client_id,
    installed_apps
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        delete_query = """
            DELETE FROM client_installed_apps
            WHERE client_id = %s
        """

        cursor.execute(
            delete_query,
            (client_id,)
        )

        insert_query = """
            INSERT INTO client_installed_apps
            (
                client_id,
                app_name,
                app_version,
                publisher,
                install_date,
                collected_at
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                NOW()
            )
        """

        values = []

        for app in installed_apps:
            app_name = str(
                app.get("app_name") or ""
            ).strip()

            if not app_name:
                continue

            values.append(
                (
                    client_id,
                    app_name[:255],
                    str(
                        app.get("app_version") or ""
                    )[:100] or None,
                    str(
                        app.get("publisher") or ""
                    )[:255] or None,
                    str(
                        app.get("install_date") or ""
                    )[:50] or None
                )
            )

        if values:
            cursor.executemany(
                insert_query,
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


def get_installed_apps_by_client(
    client_id
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        query = """
            SELECT
                id,
                app_name,
                app_version,
                publisher,
                install_date,
                collected_at
            FROM client_installed_apps
            WHERE client_id = %s
            ORDER BY app_name ASC
        """

        cursor.execute(
            query,
            (client_id,)
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def get_paginated_installed_apps(
    client_id,
    page,
    per_page,
    search=""
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        page = max(page, 1)
        per_page = max(per_page, 1)
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
                    OR app_version LIKE %s
                    OR publisher LIKE %s
                )
            """

            parameters.extend(
                [
                    search_value,
                    search_value,
                    search_value
                ]
            )

        query = f"""
            SELECT
                id,
                app_name,
                app_version,
                publisher,
                install_date,
                collected_at
            FROM client_installed_apps
            {where_clause}
            ORDER BY app_name ASC
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


def count_installed_apps(
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
                    OR app_version LIKE %s
                    OR publisher LIKE %s
                )
            """

            parameters.extend(
                [
                    search_value,
                    search_value,
                    search_value
                ]
            )

        query = f"""
            SELECT COUNT(*) AS total
            FROM client_installed_apps
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

