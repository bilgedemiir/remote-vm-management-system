import uuid

from backend.database.connection import (
    get_db_connection,
    get_db_cursor
)


VALID_NMAP_SCAN_TYPES = {
    "agent_ports",
    "top_ports"
}


VALID_NMAP_TRIGGER_TYPES = {
    "manual",
    "bulk",
    "automatic"
}


AUTOMATIC_NMAP_COOLDOWN_HOURS = 6


def create_nmap_scan(
    client_id,
    target_ip,
    scan_type="agent_ports",
    trigger_type="manual",
    batch_id=None
):
    scan_type = str(
        scan_type or "agent_ports"
    ).strip().lower()

    if scan_type not in VALID_NMAP_SCAN_TYPES:
        raise ValueError(
            "Geçersiz Nmap tarama türü."
        )

    trigger_type = str(
        trigger_type or "manual"
    ).strip().lower()

    if trigger_type not in VALID_NMAP_TRIGGER_TYPES:
        raise ValueError(
            "Geçersiz Nmap tetikleme türü."
        )

    batch_id = str(batch_id).strip() if batch_id else None

    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            SELECT
                id,
                status
            FROM nmap_scans
            WHERE client_id = %s
              AND status IN (
                  'pending',
                  'running'
              )
            ORDER BY id DESC
            LIMIT 1
            """,
            (client_id,)
        )

        existing_scan = cursor.fetchone()

        if existing_scan:
            return {
                "scan_id": existing_scan["id"],
                "created": False,
                "status": existing_scan["status"],
                "reason": "already_active"
            }

        if trigger_type == "automatic":
            cursor.execute(
                """
                SELECT id
                FROM nmap_scans
                WHERE client_id = %s
                  AND trigger_type = 'automatic'
                  AND requested_at >= NOW() - INTERVAL %s HOUR
                LIMIT 1
                """,
                (client_id, AUTOMATIC_NMAP_COOLDOWN_HOURS)
            )

            recent_auto_scan = cursor.fetchone()

            if recent_auto_scan:
                return {
                    "scan_id": recent_auto_scan["id"],
                    "created": False,
                    "status": "cooldown",
                    "reason": "automatic_cooldown"
                }

        cursor.execute(
            """
            INSERT INTO nmap_scans
            (
                client_id,
                target_ip,
                scan_type,
                trigger_type,
                batch_id,
                status,
                requested_at
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                'pending',
                NOW()
            )
            """,
            (
                client_id,
                target_ip,
                scan_type,
                trigger_type,
                batch_id
            )
        )

        scan_id = cursor.lastrowid

        connection.commit()

        return {
            "scan_id": scan_id,
            "created": True,
            "status": "pending",
            "reason": None
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def claim_next_nmap_scan():
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        connection.start_transaction()

        cursor.execute(
            """
            SELECT
                id,
                client_id,
                target_ip,
                scan_type,
                trigger_type,
                batch_id,
                status,
                requested_at
            FROM nmap_scans
            WHERE status = 'pending'
            ORDER BY requested_at ASC, id ASC
            LIMIT 1
            FOR UPDATE
            """
        )

        scan = cursor.fetchone()

        if scan is None:
            connection.commit()
            return None

        cursor.execute(
            """
            UPDATE nmap_scans
            SET
                status = 'running',
                started_at = NOW(),
                finished_at = NULL,
                error_message = NULL
            WHERE id = %s
            """,
            (scan["id"],)
        )

        connection.commit()

        scan["status"] = "running"

        return scan

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def complete_nmap_scan(
    scan_id,
    client_id,
    results
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            DELETE FROM nmap_port_results
            WHERE scan_id = %s
            """,
            (scan_id,)
        )

        insert_query = """
            INSERT INTO nmap_port_results
            (
                scan_id,
                client_id,
                protocol,
                port_number,
                state,
                service_name,
                product,
                service_version,
                extra_info,
                reason,
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
                %s,
                %s,
                %s,
                NOW()
            )
        """

        values = []

        open_count = 0
        filtered_count = 0
        closed_count = 0

        for result in results:
            state = str(
                result.get("state")
                or "unknown"
            ).strip().lower()

            if state == "open":
                open_count += 1

            elif state == "filtered":
                filtered_count += 1

            elif state == "closed":
                closed_count += 1

            values.append(
                (
                    scan_id,
                    client_id,
                    str(
                        result.get("protocol")
                        or "TCP"
                    ).upper(),
                    int(
                        result["port_number"]
                    ),
                    state[:30],
                    str(
                        result.get("service_name")
                        or ""
                    )[:100] or None,
                    str(
                        result.get("product")
                        or ""
                    )[:255] or None,
                    str(
                        result.get("service_version")
                        or ""
                    )[:100] or None,
                    str(
                        result.get("extra_info")
                        or ""
                    )[:255] or None,
                    str(
                        result.get("reason")
                        or ""
                    )[:100] or None
                )
            )

        if values:
            cursor.executemany(
                insert_query,
                values
            )

        cursor.execute(
            """
            UPDATE nmap_scans
            SET
                status = 'completed',
                scanned_port_count = %s,
                open_port_count = %s,
                filtered_port_count = %s,
                closed_port_count = %s,
                error_message = NULL,
                finished_at = NOW()
            WHERE id = %s
            """,
            (
                len(values),
                open_count,
                filtered_count,
                closed_count,
                scan_id
            )
        )

        connection.commit()

        return {
            "scanned_port_count": len(values),
            "open_port_count": open_count,
            "filtered_port_count": filtered_count,
            "closed_port_count": closed_count
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def fail_nmap_scan(
    scan_id,
    error_message
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            UPDATE nmap_scans
            SET
                status = 'failed',
                error_message = %s,
                finished_at = NOW()
            WHERE id = %s
            """,
            (
                str(
                    error_message or ""
                )[:2000],
                scan_id
            )
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def requeue_interrupted_nmap_scans():
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            UPDATE nmap_scans
            SET
                status = 'pending',
                started_at = NULL,
                error_message = NULL
            WHERE status = 'running'
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


def get_latest_nmap_scan(
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
                target_ip,
                scan_type,
                trigger_type,
                batch_id,
                status,
                scanned_port_count,
                open_port_count,
                filtered_port_count,
                closed_port_count,
                error_message,
                requested_at,
                started_at,
                finished_at
            FROM nmap_scans
            WHERE client_id = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (client_id,)
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


def get_nmap_results_by_scan(
    scan_id
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            SELECT
                id,
                scan_id,
                client_id,
                protocol,
                port_number,
                state,
                service_name,
                product,
                service_version,
                extra_info,
                reason,
                created_at
            FROM nmap_port_results
            WHERE scan_id = %s
            ORDER BY
                protocol ASC,
                port_number ASC
            """,
            (scan_id,)
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def create_nmap_scan_batch():
    batch_uuid = str(uuid.uuid4())

    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            INSERT INTO nmap_scan_batches
            (
                batch_uuid,
                requested_at
            )
            VALUES
            (
                %s,
                NOW()
            )
            """,
            (batch_uuid,)
        )

        batch_id = cursor.lastrowid
        connection.commit()

        return {
            "batch_id": batch_id,
            "batch_uuid": batch_uuid
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()
def get_nmap_scan_batch_by_uuid(
    batch_uuid
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            SELECT
                batch.id,
                batch.batch_uuid,
                batch.requested_at,

                COUNT(
                    scan.id
                ) AS total_clients,

                COALESCE(
                    SUM(
                        CASE
                            WHEN scan.status = 'completed'
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS completed_count,

                COALESCE(
                    SUM(
                        CASE
                            WHEN scan.status = 'pending'
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS pending_count,

                COALESCE(
                    SUM(
                        CASE
                            WHEN scan.status = 'running'
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS running_count,

                COALESCE(
                    SUM(
                        CASE
                            WHEN scan.status = 'failed'
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS failed_count,

                COALESCE(
                    SUM(
                        scan.scanned_port_count
                    ),
                    0
                ) AS scanned_port_count,

                COALESCE(
                    SUM(
                        scan.open_port_count
                    ),
                    0
                ) AS open_port_count,

                COALESCE(
                    SUM(
                        scan.filtered_port_count
                    ),
                    0
                ) AS filtered_port_count,

                COALESCE(
                    SUM(
                        scan.closed_port_count
                    ),
                    0
                ) AS closed_port_count

            FROM nmap_scan_batches AS batch

            LEFT JOIN nmap_scans AS scan
                ON scan.batch_id = batch.id

            WHERE batch.batch_uuid = %s

            GROUP BY
                batch.id,
                batch.batch_uuid,
                batch.requested_at

            LIMIT 1
            """,
            (batch_uuid,)
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()
        
def get_nmap_scans_by_batch(
    batch_id
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            SELECT
                scan.id,
                scan.client_id,
                scan.target_ip,
                scan.scan_type,
                scan.trigger_type,
                scan.status,
                scan.scanned_port_count,
                scan.open_port_count,
                scan.filtered_port_count,
                scan.closed_port_count,
                scan.error_message,
                scan.requested_at,
                scan.started_at,
                scan.finished_at,

                CASE
                    WHEN scan.started_at IS NOT NULL
                     AND scan.finished_at IS NOT NULL
                    THEN TIMESTAMPDIFF(
                        SECOND,
                        scan.started_at,
                        scan.finished_at
                    )
                    ELSE NULL
                END AS duration_seconds,

                client.hostname,
                client.ip_address

            FROM nmap_scans AS scan

            INNER JOIN clients AS client
                ON client.id = scan.client_id

            WHERE scan.batch_id = %s

            ORDER BY
                CASE scan.status
                    WHEN 'running' THEN 1
                    WHEN 'pending' THEN 2
                    WHEN 'failed' THEN 3
                    WHEN 'completed' THEN 4
                    ELSE 5
                END,
                client.hostname ASC
            """,
            (batch_id,)
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def delete_empty_nmap_scan_batch(
    batch_id
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            DELETE FROM nmap_scan_batches
            WHERE id = %s
              AND NOT EXISTS (
                  SELECT 1
                  FROM nmap_scans
                  WHERE batch_id = %s
              )
            """,
            (
                batch_id,
                batch_id
            )
        )

        deleted = cursor.rowcount > 0

        connection.commit()

        return deleted

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()