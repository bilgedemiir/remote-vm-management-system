from backend.database.connection import (
    get_db_connection,
    get_db_cursor
)


VALID_TRIGGER_TYPES = {
    "manual",
    "automatic",
    "bulk",
    "scheduled"
}


def create_cve_scan_job(
    client_id,
    trigger_type="manual",
    batch_id=None
):
    trigger_type = str(
        trigger_type or "manual"
    ).strip().lower()

    if trigger_type not in VALID_TRIGGER_TYPES:
        raise ValueError(
            "Geçersiz CVE tarama tetikleme türü."
        )

    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            SELECT
                id,
                status
            FROM cve_scan_jobs
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

        existing_job = cursor.fetchone()

        if existing_job:
            return {
                "job_id": existing_job["id"],
                "created": False,
                "status": existing_job["status"]
            }

        cursor.execute(
            """
            INSERT INTO cve_scan_jobs
            (
                client_id,
                batch_id,
                trigger_type,
                status,
                requested_at
            )
            VALUES
            (
                %s,
                %s,
                %s,
                'pending',
                NOW()
            )
            """,
            (
                client_id,
                batch_id,
                trigger_type
            )
        )

        job_id = cursor.lastrowid

        connection.commit()

        return {
            "job_id": job_id,
            "created": True,
            "status": "pending"
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def claim_next_cve_scan_job():
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        connection.start_transaction()

        cursor.execute(
            """
            SELECT
                id,
                client_id,
                batch_id,
                trigger_type,
                status,
                requested_at
            FROM cve_scan_jobs
            WHERE status = 'pending'
            ORDER BY requested_at ASC, id ASC
            LIMIT 1
            FOR UPDATE
            """
        )

        job = cursor.fetchone()

        if job is None:
            connection.commit()
            return None

        cursor.execute(
            """
            UPDATE cve_scan_jobs
            SET
                status = 'running',
                started_at = NOW(),
                finished_at = NULL,
                error_message = NULL
            WHERE id = %s
            """,
            (job["id"],)
        )

        connection.commit()

        job["status"] = "running"

        return job

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def complete_cve_scan_job(
    job_id,
    scanned_apps,
    matched_apps,
    findings_count
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            UPDATE cve_scan_jobs
            SET
                status = 'completed',
                scanned_apps = %s,
                matched_apps = %s,
                findings_count = %s,
                error_message = NULL,
                finished_at = NOW()
            WHERE id = %s
            """,
            (
                scanned_apps,
                matched_apps,
                findings_count,
                job_id
            )
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def fail_cve_scan_job(
    job_id,
    error_message
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            UPDATE cve_scan_jobs
            SET
                status = 'failed',
                error_message = %s,
                finished_at = NOW()
            WHERE id = %s
            """,
            (
                str(error_message or "")[:2000],
                job_id
            )
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def get_latest_cve_scan_job(
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
                batch_id,
                trigger_type,
                status,
                scanned_apps,
                matched_apps,
                findings_count,
                error_message,
                requested_at,
                started_at,
                finished_at
            FROM cve_scan_jobs
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


def requeue_interrupted_cve_scan_jobs():
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            UPDATE cve_scan_jobs
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

def get_cve_scan_jobs_by_batch(
    batch_id
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            SELECT
                job.id,
                job.client_id,
                job.batch_id,
                job.trigger_type,
                job.status,
                job.scanned_apps,
                job.matched_apps,
                job.findings_count,
                job.error_message,
                job.requested_at,
                job.started_at,
                job.finished_at,

                client.hostname,
                client.ip_address,

                CASE
                    WHEN job.started_at IS NULL
                        THEN NULL

                    WHEN job.finished_at IS NOT NULL
                        THEN TIMESTAMPDIFF(
                            SECOND,
                            job.started_at,
                            job.finished_at
                        )

                    ELSE TIMESTAMPDIFF(
                        SECOND,
                        job.started_at,
                        NOW()
                    )
                END AS duration_seconds

            FROM cve_scan_jobs AS job

            INNER JOIN clients AS client
                ON client.id = job.client_id

            WHERE job.batch_id = %s

            ORDER BY
                job.requested_at ASC,
                job.id ASC
            """,
            (batch_id,)
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()