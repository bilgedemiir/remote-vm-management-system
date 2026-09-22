from backend.database.repositories.log_repository import (
    create_log,
    get_all_logs,
    get_paginated_logs,
    count_filtered_logs,
    get_log_event_types,
    get_logs_by_client,
    get_logs_by_user,
    get_logs_by_execution,
    get_logs_by_level,
    delete_old_logs
)


def log_info(
    event_type,
    message,
    user_id=None,
    client_id=None,
    execution_id=None,
    ip_address=None
):
    return create_log(
        level="INFO",
        event_type=event_type,
        message=message,
        user_id=user_id,
        client_id=client_id,
        execution_id=execution_id,
        ip_address=ip_address
    )


def log_warning(
    event_type,
    message,
    user_id=None,
    client_id=None,
    execution_id=None,
    ip_address=None
):
    return create_log(
        level="WARNING",
        event_type=event_type,
        message=message,
        user_id=user_id,
        client_id=client_id,
        execution_id=execution_id,
        ip_address=ip_address
    )


def log_error(
    event_type,
    message,
    user_id=None,
    client_id=None,
    execution_id=None,
    ip_address=None
):
    return create_log(
        level="ERROR",
        event_type=event_type,
        message=message,
        user_id=user_id,
        client_id=client_id,
        execution_id=execution_id,
        ip_address=ip_address
    )


def list_logs():
    return get_all_logs()


def list_client_logs(client_id):
    return get_logs_by_client(client_id)


def list_user_logs(user_id):
    return get_logs_by_user(user_id)


def list_execution_logs(execution_id):
    return get_logs_by_execution(execution_id)


def list_logs_by_level(level):
    return get_logs_by_level(level)


def cleanup_logs(days=30):
    return delete_old_logs(days)


def list_paginated_logs(
    page=1,
    per_page=10,
    search="",
    event_type="",
    level="",
    start_date="",
    end_date=""
):
    page = max(page, 1)
    per_page = max(per_page, 1)

    total_records = count_filtered_logs(
        search=search,
        event_type=event_type,
        level=level,
        start_date=start_date,
        end_date=end_date
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

    logs = get_paginated_logs(
        page=page,
        per_page=per_page,
        search=search,
        event_type=event_type,
        level=level,
        start_date=start_date,
        end_date=end_date
    )

    return {
        "logs": logs,
        "page": page,
        "per_page": per_page,
        "total_records": total_records,
        "total_pages": total_pages,
        "has_previous": page > 1,
        "has_next": page < total_pages
    }


def list_log_event_types():
    return get_log_event_types()