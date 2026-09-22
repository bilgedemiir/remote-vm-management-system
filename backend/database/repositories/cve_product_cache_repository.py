from datetime import (
    datetime,
    timedelta
)

from backend.database.connection import (
    get_db_connection,
    get_db_cursor
)


def get_valid_cve_product_cache(
    cache_key
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            SELECT
                id,
                cache_key,
                app_name,
                normalized_app_name,
                app_version,
                cpe_name,
                product_matched,
                findings_json,
                last_checked_at,
                expires_at,
                error_message
            FROM cve_product_cache
            WHERE cache_key = %s
              AND expires_at IS NOT NULL
              AND expires_at > NOW()
            LIMIT 1
            """,
            (cache_key,)
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


def save_cve_product_cache(
    cache_key,
    app_name,
    normalized_app_name,
    app_version,
    cpe_name,
    product_matched,
    findings_json,
    cache_days=7
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        expires_at = (
            datetime.now()
            + timedelta(
                days=max(
                    int(cache_days),
                    1
                )
            )
        )

        cursor.execute(
            """
            INSERT INTO cve_product_cache
            (
                cache_key,
                app_name,
                normalized_app_name,
                app_version,
                cpe_name,
                product_matched,
                findings_json,
                last_checked_at,
                expires_at,
                error_message
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
                NOW(),
                %s,
                NULL
            )
            ON DUPLICATE KEY UPDATE
                app_name = VALUES(app_name),
                normalized_app_name =
                    VALUES(normalized_app_name),
                app_version = VALUES(app_version),
                cpe_name = VALUES(cpe_name),
                product_matched =
                    VALUES(product_matched),
                findings_json =
                    VALUES(findings_json),
                last_checked_at = NOW(),
                expires_at = VALUES(expires_at),
                error_message = NULL
            """,
            (
                cache_key,
                app_name[:255],
                normalized_app_name[:255],
                str(
                    app_version or ""
                )[:100] or None,
                str(
                    cpe_name or ""
                )[:500] or None,
                1 if product_matched else 0,
                findings_json,
                expires_at
            )
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def save_cve_product_cache_error(
    cache_key,
    app_name,
    normalized_app_name,
    app_version,
    error_message,
    retry_after_minutes=30
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        expires_at = (
            datetime.now()
            + timedelta(
                minutes=max(
                    int(retry_after_minutes),
                    1
                )
            )
        )

        cursor.execute(
            """
            INSERT INTO cve_product_cache
            (
                cache_key,
                app_name,
                normalized_app_name,
                app_version,
                cpe_name,
                product_matched,
                findings_json,
                last_checked_at,
                expires_at,
                error_message
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                NULL,
                0,
                '[]',
                NOW(),
                %s,
                %s
            )
            ON DUPLICATE KEY UPDATE
                last_checked_at = NOW(),
                expires_at = VALUES(expires_at),
                error_message =
                    VALUES(error_message)
            """,
            (
                cache_key,
                app_name[:255],
                normalized_app_name[:255],
                str(
                    app_version or ""
                )[:100] or None,
                expires_at,
                str(
                    error_message or ""
                )[:2000]
            )
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def delete_expired_cve_product_cache():
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute(
            """
            DELETE FROM cve_product_cache
            WHERE expires_at IS NOT NULL
              AND expires_at <= NOW()
            """
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