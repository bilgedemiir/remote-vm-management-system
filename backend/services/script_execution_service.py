from backend.database.repositories.script_execution_repository import (
    create_execution,
    get_execution_by_id,
    get_executions_by_client,
    get_paginated_executions_by_client,
    count_filtered_executions_by_client,
    update_execution_status,
    update_started_time,
    update_finished_time,
    update_agent_message,
    get_recent_executions,
    set_rollback_execution,
    mark_execution_rolled_back,
    create_execution_batch,
    get_execution_batch_by_id,
    get_executions_by_batch
)

from backend.database.repositories.execution_result_repository import (
    save_execution_result
)
from backend.services.script_analyzer import (
    validate_script_or_raise
)
from backend.services.log_service import (
    log_info,
    log_error
)


def queue_script(
    client_id,
    script_content,
    requested_by,
    timeout_seconds=300,
    rollback_script=None,
    rollback_of_execution_id=None,
    batch_id=None,
    execution_type="script"
):
    script_content = script_content.strip()

    if not script_content:
        raise ValueError(
            "Script içeriği boş olamaz."
        )

    execution_type = str(
        execution_type or "script"
    ).strip().lower()

    if execution_type not in (
        "script",
        "software_update"
    ):
        raise ValueError(
            "Geçersiz execution türü."
        )

    rollback_script = (
        rollback_script.strip()
        if rollback_script
        else None
    )

    validate_script_or_raise(
        script_content
    )

    if rollback_script:
        validate_script_or_raise(
            rollback_script
        )

    execution_id = create_execution(
        client_id=client_id,
        requested_by=requested_by,
        script_content=script_content,
        timeout_seconds=timeout_seconds,
        rollback_script=rollback_script,
        rollback_of_execution_id=(
            rollback_of_execution_id
        ),
        batch_id=batch_id,
        execution_type=execution_type
    )

    if execution_type == "software_update":
        event_type = (
            "SOFTWARE_UPDATE_QUEUED"
        )

        log_message = (
            "Yazılım güncellemesi kuyruğa eklendi."
        )

    else:
        event_type = "SCRIPT_QUEUED"

        log_message = (
            "Script çalıştırma kuyruğuna eklendi."
        )

    log_info(
        event_type=event_type,
        message=log_message,
        user_id=requested_by,
        client_id=client_id,
        execution_id=execution_id
    )

    return execution_id


def get_execution(execution_id):
    return get_execution_by_id(execution_id)


def list_client_executions(client_id):
    return get_executions_by_client(client_id)


def execution_started(execution_id):
    update_started_time(execution_id)

    log_info(
        event_type="SCRIPT_STARTED",
        message="Agent scripti çalıştırmaya başladı.",
        execution_id=execution_id
    )


def execution_completed(
    execution_id,
    exit_code,
    stdout,
    stderr,
    duration_ms=None,
    executed_by=None
):
    save_execution_result(
        execution_id=execution_id,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        duration_ms=duration_ms,
        executed_by=executed_by
    )

    update_execution_status(
        execution_id,
        "completed"
    )

    update_finished_time(
        execution_id
    )

    completed_execution = get_execution_by_id(
        execution_id
    )

    if (
        completed_execution
        and completed_execution.get(
            "rollback_of_execution_id"
        )
    ):
        original_execution_id = (
            completed_execution[
                "rollback_of_execution_id"
            ]
        )

        mark_execution_rolled_back(
            original_execution_id
        )

        log_info(
            event_type="ROLLBACK_COMPLETED",
            message=(
                "Rollback işlemi başarıyla tamamlandı."
            ),
            execution_id=execution_id,
            client_id=completed_execution[
                "client_id"
            ]
        )

    log_info(
        event_type="SCRIPT_COMPLETED",
        message="Script başarıyla tamamlandı.",
        execution_id=execution_id
    )


def execution_failed(
    execution_id,
    error_message,
    stdout="",
    exit_code=-1,
    duration_ms=None,
    executed_by=None
):
    save_execution_result(
        execution_id=execution_id,
        exit_code=exit_code,
        stdout=stdout,
        stderr=error_message,
        duration_ms=duration_ms,
        executed_by=executed_by
    )

    update_execution_status(
        execution_id,
        "failed"
    )

    update_finished_time(execution_id)

    log_error(
        event_type="SCRIPT_FAILED",
        message=error_message,
        execution_id=execution_id
    )


def set_agent_message(execution_id, message):
    update_agent_message(
        execution_id,
        message
    )


def list_recent_executions(limit=10):
    return get_recent_executions(limit)


def list_paginated_client_executions(
    client_id,
    page=1,
    per_page=10,
    search="",
    status=""
):
    page = max(page, 1)
    per_page = max(per_page, 1)

    total_records = (
        count_filtered_executions_by_client(
            client_id=client_id,
            search=search,
            status=status
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

    executions = (
        get_paginated_executions_by_client(
            client_id=client_id,
            page=page,
            per_page=per_page,
            search=search,
            status=status
        )
    )

    return {
        "executions": executions,
        "page": page,
        "per_page": per_page,
        "total_records": total_records,
        "total_pages": total_pages,
        "has_previous": page > 1,
        "has_next": page < total_pages
    }


def queue_rollback(
    original_execution_id,
    requested_by
):
    original_execution = get_execution_by_id(
        original_execution_id
    )

    if original_execution is None:
        raise ValueError(
            "Orijinal çalıştırma kaydı bulunamadı."
        )

    if original_execution["status"] != "completed":
        raise ValueError(
            "Yalnızca tamamlanmış scriptler geri alınabilir."
        )

    if original_execution["rolled_back"]:
        raise ValueError(
            "Bu script için rollback zaten çalıştırılmış."
        )

    if original_execution["rollback_execution_id"]:
        raise ValueError(
            "Bu script için rollback zaten kuyruğa eklenmiş."
        )

    rollback_script = (
        original_execution.get(
            "rollback_script"
        )
        or ""
    ).strip()

    if not rollback_script:
        raise ValueError(
            "Bu çalıştırma için rollback scripti bulunmuyor."
        )

    rollback_execution_id = queue_script(
        client_id=original_execution[
            "client_id"
        ],
        script_content=rollback_script,
        requested_by=requested_by,
        timeout_seconds=original_execution.get(
            "timeout_seconds",
            300
        ),
        rollback_of_execution_id=(
            original_execution_id
        )
    )

    set_rollback_execution(
        original_execution_id=(
            original_execution_id
        ),
        rollback_execution_id=(
            rollback_execution_id
        )
    )

    log_info(
        event_type="ROLLBACK_QUEUED",
        message=(
            "Rollback scripti kuyruğa eklendi."
        ),
        user_id=requested_by,
        client_id=original_execution[
            "client_id"
        ],
        execution_id=rollback_execution_id
    )

    return rollback_execution_id


def create_script_batch(requested_by):
    return create_execution_batch(
        requested_by
    )


def get_script_batch(batch_id):
    return get_execution_batch_by_id(
        batch_id
    )


def list_batch_executions(batch_id):
    return get_executions_by_batch(
        batch_id
    )