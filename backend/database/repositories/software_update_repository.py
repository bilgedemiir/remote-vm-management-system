from backend.database.connection import (
    get_db_connection,
    get_db_cursor
)


def replace_client_software_updates(
    client_id,
    updates
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            DELETE
            FROM client_software_updates
            WHERE client_id = %s
            """,
            (client_id,)
        )

        insert_query = """
            INSERT INTO client_software_updates
            (
                client_id,
                package_name,
                package_id,
                installed_version,
                available_version,
                source,
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

        for update in updates:
            package_name = str(
                update.get("package_name")
                or ""
            ).strip()

            package_id = str(
                update.get("package_id")
                or ""
            ).strip()

            if not package_name or not package_id:
                continue

            values.append(
                (
                    client_id,
                    package_name[:255],
                    package_id[:255],
                    str(
                        update.get(
                            "installed_version"
                        )
                        or ""
                    )[:100] or None,
                    str(
                        update.get(
                            "available_version"
                        )
                        or ""
                    )[:100] or None,
                    str(
                        update.get("source")
                        or ""
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

def get_paginated_software_updates(
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
                    package_name LIKE %s
                    OR package_id LIKE %s
                    OR installed_version LIKE %s
                    OR available_version LIKE %s
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
                package_name,
                package_id,
                installed_version,
                available_version,
                source,
                collected_at
            FROM client_software_updates
            {where_clause}
            ORDER BY package_name ASC
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


def count_software_updates(
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
                    package_name LIKE %s
                    OR package_id LIKE %s
                    OR installed_version LIKE %s
                    OR available_version LIKE %s
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
            FROM client_software_updates
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

def get_software_update_by_id(
    update_id,
    client_id
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            SELECT
                id,
                client_id,
                package_name,
                package_id,
                installed_version,
                available_version,
                source,
                collected_at
            FROM client_software_updates
            WHERE id = %s
              AND client_id = %s
            """,
            (
                update_id,
                client_id
            )
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()