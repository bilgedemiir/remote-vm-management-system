from backend.database.connection import (
    get_db_connection,
    get_db_cursor
)


def get_all_groups():
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            SELECT *
            FROM client_groups
            ORDER BY name
            """
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def get_group_by_id(group_id):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            SELECT *
            FROM client_groups
            WHERE id=%s
            """,
            (group_id,)
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


def create_group(
    name,
    description,
    created_by=None
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            INSERT INTO client_groups
            (
                name,
                description,
                created_by
            )
            VALUES
            (
                %s,
                %s,
                %s
            )
            """,
            (
                name,
                description,
                created_by
            )
        )

        connection.commit()

    finally:
        cursor.close()
        connection.close()


def update_group(
    group_id,
    name,
    description
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            UPDATE client_groups
            SET
                name=%s,
                description=%s
            WHERE id=%s
            """,
            (
                name,
                description,
                group_id
            )
        )

        connection.commit()

    finally:
        cursor.close()
        connection.close()


def delete_group(group_id):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            DELETE
            FROM client_groups
            WHERE id=%s
            """,
            (group_id,)
        )

        connection.commit()

    finally:
        cursor.close()
        connection.close()


def get_client_groups(client_id):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            SELECT
                g.*
            FROM client_groups g
            INNER JOIN client_group_members m
                ON g.id=m.group_id
            WHERE m.client_id=%s
            ORDER BY g.name
            """,
            (client_id,)
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def set_client_groups(
    client_id,
    group_ids,
    added_by=None
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:

        cursor.execute(
            """
            DELETE
            FROM client_group_members
            WHERE client_id=%s
            """,
            (client_id,)
        )

        for group_id in group_ids:

            cursor.execute(
                """
                INSERT INTO client_group_members
                (
                    client_id,
                    group_id,
                    added_by
                )
                VALUES
                (
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    client_id,
                    group_id,
                    added_by
                )
            )

        connection.commit()

    finally:
        cursor.close()
        connection.close()

def get_clients_by_group_ids(group_ids):
    if not group_ids:
        return []

    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        placeholders = ", ".join(
            ["%s"] * len(group_ids)
        )

        query = f"""
            SELECT DISTINCT
                clients.*
            FROM clients
            INNER JOIN client_group_members
                ON client_group_members.client_id = clients.id
            WHERE client_group_members.group_id IN ({placeholders})
            ORDER BY clients.hostname
        """

        cursor.execute(
            query,
            tuple(group_ids)
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

def add_clients_to_groups(
    client_ids,
    group_ids,
    added_by=None
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        added_count = 0

        for client_id in client_ids:
            for group_id in group_ids:

                cursor.execute(
                    """
                    SELECT 1
                    FROM client_group_members
                    WHERE client_id=%s
                      AND group_id=%s
                    """,
                    (
                        client_id,
                        group_id
                    )
                )

                if cursor.fetchone():
                    continue

                cursor.execute(
                    """
                    INSERT INTO client_group_members
                    (
                        client_id,
                        group_id,
                        added_by
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s
                    )
                    """,
                    (
                        client_id,
                        group_id,
                        added_by
                    )
                )

                added_count += 1

        connection.commit()

        return added_count

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()

def get_group_members(group_id):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            SELECT
                c.id,
                c.hostname,
                c.ip_address,
                c.status
            FROM clients c
            INNER JOIN client_group_members m
                ON m.client_id = c.id
            WHERE m.group_id = %s
            ORDER BY c.hostname
            """,
            (group_id,)
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def delete_group_member(
    group_id,
    client_id
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            DELETE
            FROM client_group_members
            WHERE group_id = %s
              AND client_id = %s
            """,
            (
                group_id,
                client_id
            )
        )

        deleted_count = cursor.rowcount

        connection.commit()

        return deleted_count

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()