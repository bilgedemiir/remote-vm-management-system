from backend.database.connection import (
    get_db_connection,
    get_db_cursor
)


def create_inventory(
    client_id,
    operating_system,
    os_version,
    architecture,
    cpu_name,
    cpu_cores,
    cpu_threads,
    total_ram,
    disk_total,
    disk_free,
    python_version,
    logged_user,
    boot_time
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    query = """
        INSERT INTO client_inventory
        (
            client_id,
            operating_system,
            os_version,
            architecture,
            cpu_name,
            cpu_cores,
            cpu_threads,
            total_ram,
            disk_total,
            disk_free,
            python_version,
            logged_user,
            boot_time,
            last_inventory_update
        )
        VALUES
        (
            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW()
        )
    """

    cursor.execute(
        query,
        (
            client_id,
            operating_system,
            os_version,
            architecture,
            cpu_name,
            cpu_cores,
            cpu_threads,
            total_ram,
            disk_total,
            disk_free,
            python_version,
            logged_user,
            boot_time
        )
    )

    connection.commit()

    cursor.close()
    connection.close()


def get_inventory(client_id):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    query = """
        SELECT *
        FROM client_inventory
        WHERE client_id = %s
    """

    cursor.execute(query, (client_id,))

    inventory = cursor.fetchone()

    cursor.close()
    connection.close()

    return inventory


def update_inventory(
    client_id,
    operating_system,
    os_version,
    architecture,
    cpu_name,
    cpu_cores,
    cpu_threads,
    total_ram,
    disk_total,
    disk_free,
    python_version,
    logged_user,
    boot_time
):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    query = """
        UPDATE client_inventory
        SET
            operating_system=%s,
            os_version=%s,
            architecture=%s,
            cpu_name=%s,
            cpu_cores=%s,
            cpu_threads=%s,
            total_ram=%s,
            disk_total=%s,
            disk_free=%s,
            python_version=%s,
            logged_user=%s,
            boot_time=%s,
            last_inventory_update=NOW()
        WHERE client_id=%s
    """

    cursor.execute(
        query,
        (
            operating_system,
            os_version,
            architecture,
            cpu_name,
            cpu_cores,
            cpu_threads,
            total_ram,
            disk_total,
            disk_free,
            python_version,
            logged_user,
            boot_time,
            client_id
        )
    )

    connection.commit()

    cursor.close()
    connection.close()


def inventory_exists(client_id):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    query = """
        SELECT id
        FROM client_inventory
        WHERE client_id=%s
    """

    cursor.execute(query, (client_id,))

    exists = cursor.fetchone() is not None

    cursor.close()
    connection.close()

    return exists


def save_inventory(
    client_id,
    operating_system,
    os_version,
    architecture,
    cpu_name,
    cpu_cores,
    cpu_threads,
    total_ram,
    disk_total,
    disk_free,
    python_version,
    logged_user,
    boot_time
):
    if inventory_exists(client_id):
        update_inventory(
            client_id,
            operating_system,
            os_version,
            architecture,
            cpu_name,
            cpu_cores,
            cpu_threads,
            total_ram,
            disk_total,
            disk_free,
            python_version,
            logged_user,
            boot_time
        )
    else:
        create_inventory(
            client_id,
            operating_system,
            os_version,
            architecture,
            cpu_name,
            cpu_cores,
            cpu_threads,
            total_ram,
            disk_total,
            disk_free,
            python_version,
            logged_user,
            boot_time
        )