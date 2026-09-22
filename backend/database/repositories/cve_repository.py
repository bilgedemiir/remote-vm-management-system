from backend.database.connection import (
    get_db_connection,
    get_db_cursor
)


def replace_client_cve_findings(
    client_id,
    findings
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            DELETE FROM client_cve_findings
            WHERE client_id = %s
            """,
            (client_id,)
        )

        insert_query = """
            INSERT INTO client_cve_findings
            (
                client_id,
                app_name,
                app_version,
                cve_id,
                severity,
                cvss_score,
                description,
                reference_url,
                scanned_at
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
        """

        values = []

        for finding in findings:
            app_name = str(
                finding.get("app_name") or ""
            ).strip()

            cve_id = str(
                finding.get("cve_id") or ""
            ).strip()

            if not app_name or not cve_id:
                continue

            values.append(
                (
                    client_id,
                    app_name[:255],
                    str(
                        finding.get("app_version") or ""
                    )[:100] or None,
                    cve_id[:30],
                    str(
                        finding.get("severity") or ""
                    )[:20] or None,
                    finding.get("cvss_score"),
                    finding.get("description"),
                    str(
                        finding.get("reference_url") or ""
                    )[:500] or None
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


def get_cve_findings_by_client(client_id):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            SELECT
                id,
                app_name,
                app_version,
                cve_id,
                severity,
                cvss_score,
                description,
                reference_url,
                scanned_at
            FROM client_cve_findings
            WHERE client_id = %s
            ORDER BY
                cvss_score DESC,
                cve_id ASC
            """,
            (client_id,)
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def count_cve_findings(client_id):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM client_cve_findings
            WHERE client_id = %s
            """,
            (client_id,)
        )

        result = cursor.fetchone()

        return result["total"]

    finally:
        cursor.close()
        connection.close()