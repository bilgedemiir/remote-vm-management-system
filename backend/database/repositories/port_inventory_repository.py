from backend.database.connection import (
    get_db_connection,
    get_db_cursor
)


def replace_client_port_inventory(
    client_id,
    ports
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            SELECT
                protocol,
                local_address,
                local_port,
                state,
                pid,
                process_name
            FROM client_port_inventory
            WHERE client_id = %s
            """,
            (client_id,)
        )

        previous_ports = cursor.fetchall()

        previous_by_key = {}

        for previous_port in previous_ports:
            previous_key = (
                previous_port["protocol"],
                previous_port["local_address"],
                previous_port["local_port"]
            )

            previous_by_key[
                previous_key
            ] = previous_port

        values = []
        seen_inventory_records = set()
        current_by_key = {}

        for port_data in ports:
            if not isinstance(
                port_data,
                dict
            ):
                continue

            protocol = str(
                port_data.get("protocol")
                or ""
            ).strip().upper()

            if protocol not in {
                "TCP",
                "UDP"
            }:
                continue

            local_address = str(
                port_data.get("local_address")
                or ""
            ).strip()

            if not local_address:
                local_address = "0.0.0.0"

            try:
                local_port = int(
                    port_data.get("local_port")
                )

            except (
                TypeError,
                ValueError
            ):
                continue

            if not 1 <= local_port <= 65535:
                continue

            state = str(
                port_data.get("state")
                or ""
            ).strip().upper()

            if not state:
                state = (
                    "LISTENING"
                    if protocol == "TCP"
                    else "BOUND"
                )

            if (
                protocol == "TCP"
                and state in {
                    "LISTEN",
                    "LISTENING"
                }
            ):
                state = "LISTENING"

            elif (
                protocol == "UDP"
                and state in {
                    "NONE",
                    "BOUND"
                }
            ):
                state = "BOUND"

            raw_pid = port_data.get("pid")

            try:
                pid = (
                    int(raw_pid)
                    if raw_pid is not None
                    else None
                )

            except (
                TypeError,
                ValueError
            ):
                pid = None

            process_name = str(
                port_data.get("process_name")
                or ""
            ).strip()

            inventory_record_key = (
                protocol,
                local_address,
                local_port,
                pid
            )

            if (
                inventory_record_key
                in seen_inventory_records
            ):
                continue

            seen_inventory_records.add(
                inventory_record_key
            )

            normalized_port = {
                "protocol": protocol,
                "local_address": (
                    local_address[:64]
                ),
                "local_port": local_port,
                "state": state[:30],
                "pid": pid,
                "process_name": (
                    process_name[:255]
                    or None
                )
            }

            values.append(
                (
                    client_id,
                    normalized_port[
                        "protocol"
                    ],
                    normalized_port[
                        "local_address"
                    ],
                    normalized_port[
                        "local_port"
                    ],
                    normalized_port[
                        "state"
                    ],
                    normalized_port[
                        "pid"
                    ],
                    normalized_port[
                        "process_name"
                    ]
                )
            )

            port_identity_key = (
                normalized_port["protocol"],
                normalized_port[
                    "local_address"
                ],
                normalized_port["local_port"]
            )

            current_by_key[
                port_identity_key
            ] = normalized_port

        has_previous_inventory = bool(
            previous_ports
        )

        event_values = []

        if has_previous_inventory:
            previous_keys = set(
                previous_by_key
            )

            current_keys = set(
                current_by_key
            )

            opened_keys = {
                port_key
                for port_key in (
                    current_keys
                    - previous_keys
                )
                if (
                    port_key[0] == "TCP"
                    or port_key[2] < 49152
                )
            }

            closed_keys = {
                port_key
                for port_key in (
                    previous_keys
                    - current_keys
                )
                if (
                    port_key[0] == "TCP"
                    or port_key[2] < 49152
                )
            }

            for opened_key in sorted(
                opened_keys
            ):
                opened_port = current_by_key[
                    opened_key
                ]

                event_values.append(
                    (
                        client_id,
                        "OPENED",
                        opened_port["protocol"],
                        opened_port[
                            "local_address"
                        ],
                        opened_port["local_port"],
                        opened_port["state"],
                        opened_port["pid"],
                        opened_port[
                            "process_name"
                        ]
                    )
                )

            for closed_key in sorted(
                closed_keys
            ):
                closed_port = previous_by_key[
                    closed_key
                ]

                event_values.append(
                    (
                        client_id,
                        "CLOSED",
                        closed_port["protocol"],
                        closed_port[
                            "local_address"
                        ],
                        closed_port["local_port"],
                        closed_port["state"],
                        closed_port["pid"],
                        closed_port[
                            "process_name"
                        ]
                    )
                )

        cursor.execute(
            """
            DELETE FROM client_port_inventory
            WHERE client_id = %s
            """,
            (client_id,)
        )

        if values:
            cursor.executemany(
                """
                INSERT INTO client_port_inventory
                (
                    client_id,
                    protocol,
                    local_address,
                    local_port,
                    state,
                    pid,
                    process_name,
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
                    %s,
                    NOW()
                )
                """,
                values
            )

        if event_values:
            cursor.executemany(
                """
                INSERT INTO client_port_events
                (
                    client_id,
                    event_type,
                    protocol,
                    local_address,
                    local_port,
                    state,
                    pid,
                    process_name,
                    detected_at
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
                    %s,
                    NOW()
                )
                """,
                event_values
            )

        connection.commit()

        return len(values)

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def get_client_port_inventory(
    client_id
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            SELECT
                id,
                protocol,
                local_address,
                local_port,
                state,
                pid,
                process_name,
                collected_at
            FROM client_port_inventory
            WHERE client_id = %s
            ORDER BY
                CASE
                    WHEN protocol = 'TCP'
                        THEN 0
                    ELSE 1
                END,
                local_port ASC,
                local_address ASC
            """,
            (client_id,)
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def get_paginated_client_ports(
    client_id,
    page,
    per_page,
    search="",
    protocol=""
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        page = max(
            int(page),
            1
        )

        per_page = max(
            int(per_page),
            1
        )

        offset = (
            page - 1
        ) * per_page

        parameters = [
            client_id
        ]

        where_clause = """
            WHERE client_id = %s
        """

        if protocol in {
            "TCP",
            "UDP"
        }:
            where_clause += """
                AND protocol = %s
            """

            parameters.append(
                protocol
            )

        if search:
            search_value = (
                f"%{search}%"
            )

            where_clause += """
                AND (
                    local_address LIKE %s
                    OR CAST(
                        local_port AS CHAR
                    ) LIKE %s
                    OR process_name LIKE %s
                    OR state LIKE %s
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
                protocol,
                local_address,
                local_port,
                state,
                pid,
                process_name,
                collected_at
            FROM client_port_inventory
            {where_clause}
            ORDER BY
                CASE
                    WHEN protocol = 'TCP'
                        THEN 0
                    ELSE 1
                END,
                local_port ASC,
                local_address ASC
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


def count_client_ports(
    client_id,
    search="",
    protocol=""
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        parameters = [
            client_id
        ]

        where_clause = """
            WHERE client_id = %s
        """

        if protocol in {
            "TCP",
            "UDP"
        }:
            where_clause += """
                AND protocol = %s
            """

            parameters.append(
                protocol
            )

        if search:
            search_value = (
                f"%{search}%"
            )

            where_clause += """
                AND (
                    local_address LIKE %s
                    OR CAST(
                        local_port AS CHAR
                    ) LIKE %s
                    OR process_name LIKE %s
                    OR state LIKE %s
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
            FROM client_port_inventory
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


def get_client_port_summary(
    client_id
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(
                    CASE
                        WHEN protocol = 'TCP'
                            THEN 1
                        ELSE 0
                    END
                ) AS tcp_total,
                SUM(
                    CASE
                        WHEN protocol = 'UDP'
                            THEN 1
                        ELSE 0
                    END
                ) AS udp_total,
                MAX(collected_at) AS collected_at
            FROM client_port_inventory
            WHERE client_id = %s
            """,
            (client_id,)
        )

        result = cursor.fetchone()

        return {
            "total": (
                result["total"] or 0
            ),
            "tcp_total": (
                result["tcp_total"] or 0
            ),
            "udp_total": (
                result["udp_total"] or 0
            ),
            "collected_at": result[
                "collected_at"
            ]
        }

    finally:
        cursor.close()
        connection.close()

def get_paginated_client_port_events(
    client_id,
    page,
    per_page,
    search="",
    protocol="",
    event_type=""
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        page = max(
            int(page),
            1
        )

        per_page = max(
            int(per_page),
            1
        )

        offset = (
            page - 1
        ) * per_page

        parameters = [
            client_id
        ]

        where_clause = """
            WHERE client_id = %s
        """

        if protocol in {
            "TCP",
            "UDP"
        }:
            where_clause += """
                AND protocol = %s
            """

            parameters.append(
                protocol
            )

        if event_type in {
            "OPENED",
            "CLOSED"
        }:
            where_clause += """
                AND event_type = %s
            """

            parameters.append(
                event_type
            )

        if search:
            search_value = (
                f"%{search}%"
            )

            where_clause += """
                AND (
                    local_address LIKE %s
                    OR CAST(
                        local_port AS CHAR
                    ) LIKE %s
                    OR process_name LIKE %s
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
                event_type,
                protocol,
                local_address,
                local_port,
                state,
                pid,
                process_name,
                detected_at
            FROM client_port_events
            {where_clause}
            ORDER BY
                detected_at DESC,
                id DESC
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


def count_client_port_events(
    client_id,
    search="",
    protocol="",
    event_type=""
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        parameters = [
            client_id
        ]

        where_clause = """
            WHERE client_id = %s
        """

        if protocol in {
            "TCP",
            "UDP"
        }:
            where_clause += """
                AND protocol = %s
            """

            parameters.append(
                protocol
            )

        if event_type in {
            "OPENED",
            "CLOSED"
        }:
            where_clause += """
                AND event_type = %s
            """

            parameters.append(
                event_type
            )

        if search:
            search_value = (
                f"%{search}%"
            )

            where_clause += """
                AND (
                    local_address LIKE %s
                    OR CAST(
                        local_port AS CHAR
                    ) LIKE %s
                    OR process_name LIKE %s
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
            FROM client_port_events
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


def get_client_port_event_summary(
    client_id
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(
                    CASE
                        WHEN event_type = 'OPENED'
                            THEN 1
                        ELSE 0
                    END
                ) AS opened_total,
                SUM(
                    CASE
                        WHEN event_type = 'CLOSED'
                            THEN 1
                        ELSE 0
                    END
                ) AS closed_total,
                MAX(detected_at) AS last_event_at
            FROM client_port_events
            WHERE client_id = %s
            """,
            (client_id,)
        )

        result = cursor.fetchone()

        return {
            "total": (
                result["total"] or 0
            ),
            "opened_total": (
                result["opened_total"] or 0
            ),
            "closed_total": (
                result["closed_total"] or 0
            ),
            "last_event_at": result[
                "last_event_at"
            ]
        }

    finally:
        cursor.close()
        connection.close()