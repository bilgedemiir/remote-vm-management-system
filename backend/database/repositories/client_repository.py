from datetime import (
    datetime,
    timedelta
)
from backend.database.connection import (
    get_db_connection,
    get_db_cursor
)


def create_client(
    uuid,
    hostname,
    ip_address,
    agent_version,
    ipv6_address,
    mac_address,
    domain_name,
    default_gateway,
    dns_servers,
    windows_version,
    build_number,
    architecture,
    logged_in_user,
    uptime,
    cpu_name,
    cpu_core_count,
    logical_processor_count,
    cpu_usage,
    ram_usage_percent,
    disk_usage_percent,
    tcp_connection_count,
    udp_endpoint_count,
    python_version,
    listening_port_count=None,
    virtualization=None
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        query = """
            INSERT INTO clients
            (
                uuid,
                hostname,
                ip_address,
                agent_version,
                ipv6_address,
                mac_address,
                domain_name,
                default_gateway,
                dns_servers,
                windows_version,
                build_number,
                architecture,
                logged_in_user,
                uptime,
                cpu_name,
                cpu_core_count,
                logical_processor_count,
                cpu_usage,
                ram_usage_percent,
                disk_usage_percent,
                tcp_connection_count,
                udp_endpoint_count,
                listening_port_count,
                virtualization,
                python_version,
                status,
                last_seen,
                system_info_updated_at
            )
            VALUES
            (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                'online',
                NOW(),
                NOW()
            )
        """

        cursor.execute(
            query,
            (
                uuid,
                hostname,
                ip_address,
                agent_version,
                ipv6_address,
                mac_address,
                domain_name,
                default_gateway,
                dns_servers,
                windows_version,
                build_number,
                architecture,
                logged_in_user,
                uptime,
                cpu_name,
                cpu_core_count,
                logical_processor_count,
                cpu_usage,
                ram_usage_percent,
                disk_usage_percent,
                tcp_connection_count,
                udp_endpoint_count,
                listening_port_count,
                virtualization,
                python_version
            )
        )

        connection.commit()

        return cursor.lastrowid

    finally:
        cursor.close()
        connection.close()


def get_client_by_uuid(uuid):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        query = """
            SELECT *
            FROM clients
            WHERE uuid = %s
        """

        cursor.execute(query, (uuid,))

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


def get_client_by_id(client_id):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        query = """
            SELECT *
            FROM clients
            WHERE id = %s
        """

        cursor.execute(query, (client_id,))

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


def get_all_clients():
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        query = """
            SELECT *
            FROM clients
            ORDER BY hostname
        """

        cursor.execute(query)

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def update_client_status(
    client_id,
    status
):
    status = str(
        status or ""
    ).strip().lower()

    if status not in {
        "online",
        "offline"
    }:
        raise ValueError(
            "Geçersiz istemci durumu."
        )

    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        if status == "online":
            query = """
                UPDATE clients
                SET
                    status = 'online',
                    last_seen = NOW()
                WHERE id = %s
            """

        else:
            query = """
                UPDATE clients
                SET
                    status = 'offline'
                WHERE id = %s
            """

        cursor.execute(
            query,
            (client_id,)
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def update_client_last_seen(client_id):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        query = """
            UPDATE clients
            SET
                last_seen = NOW(),
                status = 'online'
            WHERE id = %s
        """

        cursor.execute(
            query,
            (client_id,)
        )

        connection.commit()

    finally:
        cursor.close()
        connection.close()


def update_client_system_info(
    client_id,
    system_info
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        query = """
            UPDATE clients
            SET
                uptime = %s,
                cpu_name = %s,
                cpu_core_count = %s,
                logical_processor_count = %s,
                cpu_usage = %s,
                ram_usage_percent = %s,
                disk_usage_percent = %s,
                tcp_connection_count = %s,
                udp_endpoint_count = %s,
                listening_port_count = %s,
                python_version = %s,
                virtualization = %s,
                status = 'online',
                last_seen = NOW(),
                system_info_updated_at = NOW()
            WHERE id = %s
        """

        cursor.execute(
            query,
            (
                system_info.get("uptime"),
                system_info.get("cpu_name"),
                system_info.get("cpu_core_count"),
                system_info.get(
                    "logical_processor_count"
                ),
                system_info.get("cpu_usage"),
                system_info.get(
                    "ram_usage_percent"
                ),
                system_info.get(
                    "disk_usage_percent"
                ),
                system_info.get(
                    "tcp_connection_count"
                ),
                system_info.get(
                    "udp_endpoint_count"
                ),
                system_info.get(
                    "listening_port_count"
                ),
                system_info.get("python_version"),
                system_info.get("virtualization"),
                client_id
            )
        )

        connection.commit()

    finally:
        cursor.close()
        connection.close()


def update_client_ip(
    client_id,
    ip_address
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        query = """
            UPDATE clients
            SET
                ip_address = %s
            WHERE id = %s
        """

        cursor.execute(
            query,
            (
                ip_address,
                client_id
            )
        )

        connection.commit()

    finally:
        cursor.close()
        connection.close()


def update_client(
    client_id,
    hostname,
    ip_address,
    agent_version,
    ipv6_address,
    mac_address,
    domain_name,
    default_gateway,
    dns_servers,
    windows_version,
    build_number,
    architecture,
    logged_in_user,
    uptime,
    cpu_name,
    cpu_core_count,
    logical_processor_count,
    cpu_usage,
    ram_usage_percent,
    disk_usage_percent,
    tcp_connection_count,
    udp_endpoint_count,
    python_version,
    listening_port_count=None,
    virtualization=None
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        query = """
            UPDATE clients
            SET
                hostname = %s,
                ip_address = %s,
                agent_version = %s,
                ipv6_address = %s,
                mac_address = %s,
                domain_name = %s,
                default_gateway = %s,
                dns_servers = %s,
                windows_version = %s,
                build_number = %s,
                architecture = %s,
                logged_in_user = %s,
                uptime = %s,
                cpu_name = %s,
                cpu_core_count = %s,
                logical_processor_count = %s,
                cpu_usage = %s,
                ram_usage_percent = %s,
                disk_usage_percent = %s,
                tcp_connection_count = %s,
                udp_endpoint_count = %s,
                listening_port_count = %s,
                virtualization = %s,
                python_version = %s,
                status = 'online',
                last_seen = NOW(),
                system_info_updated_at = NOW()
            WHERE id = %s
        """

        cursor.execute(
            query,
            (
                hostname,
                ip_address,
                agent_version,
                ipv6_address,
                mac_address,
                domain_name,
                default_gateway,
                dns_servers,
                windows_version,
                build_number,
                architecture,
                logged_in_user,
                uptime,
                cpu_name,
                cpu_core_count,
                logical_processor_count,
                cpu_usage,
                ram_usage_percent,
                disk_usage_percent,
                tcp_connection_count,
                udp_endpoint_count,
                listening_port_count,
                virtualization,
                python_version,
                client_id
            )
        )

        connection.commit()

    finally:
        cursor.close()
        connection.close()


def delete_client(client_id):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        query = """
            DELETE
            FROM clients
            WHERE id = %s
        """

        cursor.execute(
            query,
            (client_id,)
        )

        connection.commit()

    finally:
        cursor.close()
        connection.close()


def count_clients():
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        query = """
            SELECT COUNT(*) AS total
            FROM clients
        """

        cursor.execute(query)

        result = cursor.fetchone()

        return result["total"]

    finally:
        cursor.close()
        connection.close()


def count_online_clients():
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        query = """
            SELECT COUNT(*) AS total
            FROM clients
            WHERE status = 'online'
        """

        cursor.execute(query)

        result = cursor.fetchone()

        return result["total"]

    finally:
        cursor.close()
        connection.close()


def get_last_active_client():
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        query = """
            SELECT
                hostname,
                last_seen
            FROM clients
            ORDER BY last_seen DESC
            LIMIT 1
        """

        cursor.execute(query)

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


def build_client_filters(
    search="",
    status=""
):
    conditions = []
    parameters = []

    if search:
        search_value = f"%{search}%"

        conditions.append(
            """
            (
                hostname LIKE %s
                OR ip_address LIKE %s
                OR uuid LIKE %s
                OR logged_in_user LIKE %s
                OR mac_address LIKE %s
            )
            """
        )

        parameters.extend(
            [
                search_value,
                search_value,
                search_value,
                search_value,
                search_value
            ]
        )

    if status in ("online", "offline"):
        conditions.append(
            "status = %s"
        )

        parameters.append(status)

    if conditions:
        where_clause = (
            "WHERE " + " AND ".join(conditions)
        )
    else:
        where_clause = ""

    return where_clause, parameters


def get_paginated_clients(
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
            build_client_filters(
                search=search,
                status=status
            )
        )

        query = f"""
            SELECT *
            FROM clients
            {where_clause}
            ORDER BY
                CASE
                    WHEN status = 'online' THEN 0
                    ELSE 1
                END,
                last_seen DESC,
                hostname ASC
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


def count_filtered_clients(
    search="",
    status=""
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        where_clause, parameters = (
            build_client_filters(
                search=search,
                status=status
            )
        )

        query = f"""
            SELECT COUNT(*) AS total
            FROM clients
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


def mark_all_clients_offline():
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            UPDATE clients
            SET status = 'offline'
            WHERE status = 'online'
            """
        )

        affected_count = cursor.rowcount

        connection.commit()

        return affected_count

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def mark_stale_clients_offline(
    timeout_seconds=40
):
    timeout_seconds = max(
        int(timeout_seconds),
        1
    )

    stale_before = (
        datetime.now()
        - timedelta(
            seconds=timeout_seconds
        )
    )

    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            UPDATE clients
            SET status = 'offline'
            WHERE status = 'online'
              AND (
                  last_seen IS NULL
                  OR last_seen < %s
              )
            """,
            (stale_before,)
        )

        affected_count = cursor.rowcount

        connection.commit()

        return affected_count

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()