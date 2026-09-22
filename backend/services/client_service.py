from backend.database.repositories.client_repository import (
    create_client,
    get_client_by_uuid,
    get_client_by_id,
    get_all_clients,
    get_paginated_clients,
    count_filtered_clients,
    update_client_status,
    update_client_last_seen,
    update_client_ip,
    count_clients,
    count_online_clients,
    get_last_active_client as repository_get_last_active_client
)
from backend.database.repositories.installed_app_repository import (
    get_paginated_installed_apps,
    count_installed_apps
)
from backend.database.repositories.port_inventory_repository import (
    get_paginated_client_ports,
    count_client_ports,
    get_client_port_summary,
    get_paginated_client_port_events,
    count_client_port_events,
    get_client_port_event_summary
)
from backend.database.repositories.running_app_repository import (
    get_paginated_running_apps,
    count_running_apps
)
from backend.database.repositories.software_update_repository import (
    get_paginated_software_updates,
    count_software_updates
)


def register_client(
    uuid,
    hostname,
    ip_address,
    agent_version
):
    client = get_client_by_uuid(uuid)

    if client is None:
        client_id = create_client(
            uuid,
            hostname,
            ip_address,
            agent_version
        )

        return get_client_by_id(client_id)

    update_client_ip(
        client["id"],
        ip_address
    )

    update_client_status(
        client["id"],
        "online"
    )

    return get_client_by_id(client["id"])


def heartbeat(client_id):
    update_client_last_seen(client_id)

    update_client_status(
        client_id,
        "online"
    )


def disconnect(client_id):
    update_client_status(
        client_id,
        "offline"
    )


def get_client(client_id):
    return get_client_by_id(client_id)


def list_clients():
    return get_all_clients()


def get_client_count():
    return count_clients()


def get_online_client_count():
    return count_online_clients()


def get_last_active_client():
    return repository_get_last_active_client()


def list_paginated_clients(
    page=1,
    per_page=10,
    search="",
    status=""
):
    page = max(page, 1)
    per_page = max(per_page, 1)

    total_records = count_filtered_clients(
        search=search,
        status=status
    )

    total_pages = max(
        1,
        (
            total_records
            + per_page
            - 1
        ) // per_page
    )

    if page > total_pages:
        page = total_pages

    clients = get_paginated_clients(
        page=page,
        per_page=per_page,
        search=search,
        status=status
    )

    return {
        "clients": clients,
        "page": page,
        "per_page": per_page,
        "total_records": total_records,
        "total_pages": total_pages,
        "has_previous": page > 1,
        "has_next": page < total_pages
    }


def list_paginated_installed_apps(
    client_id,
    page=1,
    per_page=10,
    search=""
):
    page = max(page, 1)
    per_page = max(per_page, 1)

    total_records = count_installed_apps(
        client_id=client_id,
        search=search
    )

    total_pages = max(
        1,
        (
            total_records
            + per_page
            - 1
        ) // per_page
    )

    if page > total_pages:
        page = total_pages

    installed_apps = get_paginated_installed_apps(
        client_id=client_id,
        page=page,
        per_page=per_page,
        search=search
    )

    return {
        "items": installed_apps,
        "page": page,
        "per_page": per_page,
        "total_records": total_records,
        "total_pages": total_pages,
        "has_previous": page > 1,
        "has_next": page < total_pages
    }


def list_paginated_client_ports(
    client_id,
    page=1,
    per_page=10,
    search="",
    protocol=""
):
    page = max(
        int(page),
        1
    )

    per_page = max(
        int(per_page),
        1
    )

    protocol = str(
        protocol or ""
    ).strip().upper()

    if protocol not in {
        "",
        "TCP",
        "UDP"
    }:
        protocol = ""

    total_records = count_client_ports(
        client_id=client_id,
        search=search,
        protocol=protocol
    )

    total_pages = max(
        1,
        (
            total_records
            + per_page
            - 1
        ) // per_page
    )

    if page > total_pages:
        page = total_pages

    ports = get_paginated_client_ports(
        client_id=client_id,
        page=page,
        per_page=per_page,
        search=search,
        protocol=protocol
    )

    summary = get_client_port_summary(
        client_id
    )

    return {
        "items": ports,
        "page": page,
        "per_page": per_page,
        "total_records": total_records,
        "total_pages": total_pages,
        "has_previous": page > 1,
        "has_next": page < total_pages,
        "summary": summary
    }


def list_paginated_client_port_events(
    client_id,
    page=1,
    per_page=10,
    search="",
    protocol="",
    event_type=""
):
    page = max(
        int(page),
        1
    )

    per_page = max(
        int(per_page),
        1
    )

    protocol = str(
        protocol or ""
    ).strip().upper()

    if protocol not in {
        "",
        "TCP",
        "UDP"
    }:
        protocol = ""

    event_type = str(
        event_type or ""
    ).strip().upper()

    if event_type not in {
        "",
        "OPENED",
        "CLOSED"
    }:
        event_type = ""

    total_records = (
        count_client_port_events(
            client_id=client_id,
            search=search,
            protocol=protocol,
            event_type=event_type
        )
    )

    total_pages = max(
        1,
        (
            total_records
            + per_page
            - 1
        ) // per_page
    )

    if page > total_pages:
        page = total_pages

    events = (
        get_paginated_client_port_events(
            client_id=client_id,
            page=page,
            per_page=per_page,
            search=search,
            protocol=protocol,
            event_type=event_type
        )
    )

    summary = get_client_port_event_summary(
        client_id
    )

    return {
        "items": events,
        "page": page,
        "per_page": per_page,
        "total_records": total_records,
        "total_pages": total_pages,
        "has_previous": page > 1,
        "has_next": page < total_pages,
        "summary": summary
    }


def list_paginated_running_apps(
    client_id,
    page=1,
    per_page=10,
    search=""
):
    page = max(page, 1)
    per_page = max(per_page, 1)

    total_records = count_running_apps(
        client_id=client_id,
        search=search
    )

    total_pages = max(
        1,
        (
            total_records
            + per_page
            - 1
        ) // per_page
    )

    if page > total_pages:
        page = total_pages

    running_apps = get_paginated_running_apps(
        client_id=client_id,
        page=page,
        per_page=per_page,
        search=search
    )

    return {
        "items": running_apps,
        "page": page,
        "per_page": per_page,
        "total_records": total_records,
        "total_pages": total_pages,
        "has_previous": page > 1,
        "has_next": page < total_pages
    }


def list_paginated_software_updates(
    client_id,
    page=1,
    per_page=10,
    search=""
):
    page = max(page, 1)
    per_page = max(per_page, 1)

    total_records = count_software_updates(
        client_id=client_id,
        search=search
    )

    total_pages = max(
        1,
        (
            total_records
            + per_page
            - 1
        ) // per_page
    )

    if page > total_pages:
        page = total_pages

    updates = get_paginated_software_updates(
        client_id=client_id,
        page=page,
        per_page=per_page,
        search=search
    )

    return {
        "items": updates,
        "page": page,
        "per_page": per_page,
        "total_records": total_records,
        "total_pages": total_pages,
        "has_previous": page > 1,
        "has_next": page < total_pages
    }