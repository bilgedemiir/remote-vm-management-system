from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for
)

from backend.database.repositories.script_execution_repository import (
    set_rollback_execution
)
from backend.services.ai_service import (
    generate_rollback_powershell
)
from backend.services.client_service import (
    get_client,
    list_clients
)
from backend.services.group_service import (
    list_clients_for_groups,
    list_groups
)
from backend.services.script_execution_service import (
    create_script_batch,
    get_execution,
    get_script_batch,
    list_batch_executions,
    list_client_executions,
    list_paginated_client_executions,
    queue_rollback,
    queue_script
)
from backend.utils.decorators import (
    login_required,
    operator_required
)


script_execution_bp = Blueprint(
    "script_execution",
    __name__
)


@script_execution_bp.route(
    "/scripts/open-generated",
    methods=["POST"]
)
@operator_required
def open_generated_script():
    script_content = request.form.get(
        "script_content",
        ""
    ).strip()

    client_id = request.form.get(
        "client_id",
        type=int
    )

    if not script_content:
        flash(
            "AI tarafından oluşturulan script boş.",
            "danger"
        )

        if client_id:
            return redirect(
                url_for(
                    "client.client_detail",
                    client_id=client_id
                )
            )

        return redirect(
            url_for("dashboard.dashboard")
        )

    if client_id is None:
        flash(
            "Client bilgisi bulunamadı.",
            "danger"
        )

        return redirect(
            url_for("dashboard.dashboard")
        )

    client = get_client(client_id)

    if client is None:
        flash(
            "Client bulunamadı.",
            "danger"
        )

        return redirect(
            url_for("dashboard.dashboard")
        )

    if client["status"] != "online":
        flash(
            "Client çevrimdışı olduğu için script çalıştırılamaz.",
            "danger"
        )

        return redirect(
            url_for(
                "client.client_detail",
                client_id=client_id
            )
        )

    clients = list_clients()
    groups = list_groups()

    return render_template(
        "scripts_execute.html",
        clients=clients,
        groups=groups,
        script_content=script_content,
        timeout_seconds=300,
        selected_client_id=client_id,
        selected_group_ids=[],
        select_all_online=False
    )


@script_execution_bp.route(
    "/clients/<int:client_id>/execute",
    methods=["GET", "POST"]
)
@script_execution_bp.route(
    "/scripts/execute",
    methods=["GET", "POST"]
)
@operator_required
def execute_script_central(client_id=None):
    clients = list_clients()
    groups = list_groups()

    selected_client_id = request.args.get(
        "client_id",
        type=int
    ) or client_id

    selected_group_ids = []
    select_all_online = False

    if request.method == "POST":
        script_content = request.form.get(
            "script_content",
            ""
        ).strip()

        timeout_seconds = request.form.get(
            "timeout_seconds",
            default=300,
            type=int
        )

        selected_client_ids = request.form.getlist(
            "client_ids"
        )

        selected_group_ids = request.form.getlist(
            "group_ids"
        )

        select_all_online = (
            request.form.get("select_all_online")
            == "1"
        )

        def render_form():
            return render_template(
                "scripts_execute.html",
                clients=clients,
                groups=groups,
                script_content=script_content,
                timeout_seconds=timeout_seconds,
                selected_client_id=selected_client_id,
                selected_group_ids=[
                    int(group_id)
                    for group_id in selected_group_ids
                    if str(group_id).isdigit()
                ],
                select_all_online=select_all_online
            )

        if not script_content:
            flash(
                "Script içeriği boş olamaz.",
                "danger"
            )
            return render_form()

        target_client_ids = set()
        invalid_client_ids = []
        offline_direct_clients = []

        for client_id_item in selected_client_ids:
            try:
                direct_client_id = int(
                    client_id_item
                )
            except (TypeError, ValueError):
                invalid_client_ids.append(
                    str(client_id_item)
                )
                continue

            selected_client = get_client(
                direct_client_id
            )

            if selected_client is None:
                invalid_client_ids.append(
                    str(client_id_item)
                )
                continue

            if selected_client["status"] != "online":
                offline_direct_clients.append(
                    selected_client["hostname"]
                )
                continue

            target_client_ids.add(
                direct_client_id
            )

        if invalid_client_ids:
            flash(
                "Geçersiz veya bulunamayan client seçildi.",
                "danger"
            )
            return render_form()

        if offline_direct_clients:
            flash(
                (
                    "Doğrudan seçilen şu clientlar çevrimdışı: "
                    + ", ".join(offline_direct_clients)
                ),
                "danger"
            )
            return render_form()

        if selected_group_ids:
            try:
                group_clients = list_clients_for_groups(
                    selected_group_ids
                )

            except (TypeError, ValueError):
                flash(
                    "Geçersiz grup seçildi.",
                    "danger"
                )
                return render_form()

            for group_client in group_clients:
                if group_client["status"] == "online":
                    target_client_ids.add(
                        group_client["id"]
                    )

        if select_all_online:
            for current_client in clients:
                if current_client["status"] == "online":
                    target_client_ids.add(
                        current_client["id"]
                    )

        if not target_client_ids:
            flash(
                (
                    "En az bir online client, grup "
                    "veya tüm online clientlar seçilmelidir."
                ),
                "danger"
            )
            return render_form()

        execution_ids = []

        try:
            use_batch = (
                bool(selected_group_ids)
                or select_all_online
                or len(target_client_ids) > 1
            )

            batch_id = None

            if use_batch:
                batch_id = create_script_batch(
                    requested_by=session["user_id"]
                )

            for target_client_id in sorted(
                target_client_ids
            ):
                execution_id = queue_script(
                    client_id=target_client_id,
                    script_content=script_content,
                    requested_by=session["user_id"],
                    timeout_seconds=timeout_seconds,
                    batch_id=batch_id
                )

                execution_ids.append(
                    execution_id
                )

            if batch_id is not None:
                flash(
                    (
                        f"Script {len(execution_ids)} farklı client "
                        "için çalıştırma kuyruğuna eklendi."
                    ),
                    "success"
                )

                return redirect(
                    url_for(
                        "script_execution.batch_detail",
                        batch_id=batch_id
                    )
                )

            flash(
                "Script çalıştırma kuyruğuna eklendi.",
                "success"
            )

            return redirect(
                url_for(
                    "script_execution.execution_detail",
                    execution_id=execution_ids[0]
                )
            )

        except ValueError as error:
            flash(
                str(error),
                "danger"
            )
            return render_form()

        except Exception as error:
            flash(
                f"Scriptler kuyruğa eklenemedi: {error}",
                "danger"
            )
            return render_form()

    return render_template(
        "scripts_execute.html",
        clients=clients,
        groups=groups,
        script_content="",
        timeout_seconds=300,
        selected_client_id=selected_client_id,
        selected_group_ids=[],
        select_all_online=False
    )


@operator_required
def execute_script(client_id):
    client = get_client(client_id)

    if client is None:
        return "Client bulunamadı.", 404

    if client["status"] != "online":
        flash(
            "Client çevrimdışı olduğu için script gönderilemez.",
            "danger"
        )

        return redirect(
            url_for(
                "client.client_detail",
                client_id=client_id
            )
        )

    if request.method == "POST":
        script_content = request.form.get(
            "script_content",
            ""
        )

        timeout_seconds = request.form.get(
            "timeout_seconds",
            default=300,
            type=int
        )

        try:
            execution_id = queue_script(
                client_id=client_id,
                script_content=script_content,
                requested_by=session["user_id"],
                timeout_seconds=timeout_seconds
            )

            flash(
                "Script çalıştırma kuyruğuna eklendi.",
                "success"
            )

            return redirect(
                url_for(
                    "script_execution.execution_detail",
                    execution_id=execution_id
                )
            )

        except ValueError as error:
            flash(str(error), "danger")

        except Exception as error:
            flash(
                f"Script kuyruğa eklenemedi: {error}",
                "danger"
            )

    return render_template(
        "script_run.html",
        client=client
    )


@script_execution_bp.route(
    "/execution-batches/<int:batch_id>"
)
@operator_required
def batch_detail(batch_id):
    batch = get_script_batch(
        batch_id
    )

    if batch is None:
        return "Toplu çalıştırma kaydı bulunamadı.", 404

    executions = list_batch_executions(
        batch_id
    )

    active_statuses = {
        "pending",
        "assigned",
        "running"
    }

    active_count = sum(
        1
        for execution in executions
        if execution["status"] in active_statuses
    )

    completed_count = sum(
        1
        for execution in executions
        if execution["status"] == "completed"
    )

    failed_count = sum(
        1
        for execution in executions
        if execution["status"] == "failed"
    )

    if active_count > 0:
        overall_status = "running"

    elif failed_count > 0:
        overall_status = "failed"

    else:
        overall_status = "completed"

    script_content = ""

    if executions:
        script_content = (
            executions[0].get(
                "script_content"
            )
            or ""
        )

    return render_template(
        "script_execution_batch_detail.html",
        batch=batch,
        executions=executions,
        script_content=script_content,
        active_count=active_count,
        completed_count=completed_count,
        failed_count=failed_count,
        overall_status=overall_status
    )


@script_execution_bp.route(
    "/executions/<int:execution_id>"
)
@operator_required
def execution_detail(execution_id):
    execution = get_execution(execution_id)

    if execution is None:
        return "Çalıştırma kaydı bulunamadı.", 404

    return render_template(
        "script_execution_detail.html",
        execution=execution
    )


@script_execution_bp.route(
    "/executions/<int:execution_id>/rollback",
    methods=["GET", "POST"]
)
@operator_required
def rollback_execution(execution_id):
    execution = get_execution(
        execution_id
    )

    if execution is None:
        flash(
            "Script bulunamadı.",
            "danger"
        )

        return redirect(
            url_for(
                "dashboard.dashboard"
            )
        )

    if request.method == "GET":
        try:
            rollback_script = (
                generate_rollback_powershell(
                    execution[
                        "script_content"
                    ]
                )
            )

        except Exception as error:
            flash(
                f"Rollback üretilemedi: {error}",
                "danger"
            )

            return redirect(
                url_for(
                    "script_execution.execution_detail",
                    execution_id=execution_id
                )
            )

        return render_template(
            "rollback_preview.html",
            execution=execution,
            rollback_script=rollback_script
        )

    rollback_script = request.form.get(
        "rollback_script",
        ""
    ).strip()

    if not rollback_script:
        flash(
            "Rollback scripti boş olamaz.",
            "danger"
        )

        return redirect(
            url_for(
                "script_execution.rollback_execution",
                execution_id=execution_id
            )
        )

    if execution["status"] != "completed":
        flash(
            "Yalnızca tamamlanmış scriptler geri alınabilir.",
            "danger"
        )

        return redirect(
            url_for(
                "script_execution.execution_detail",
                execution_id=execution_id
            )
        )

    if execution["rolled_back"]:
        flash(
            "Bu script daha önce geri alınmış.",
            "warning"
        )

        return redirect(
            url_for(
                "script_execution.execution_detail",
                execution_id=execution_id
            )
        )

    if execution["rollback_execution_id"]:
        flash(
            "Bu script için rollback zaten kuyruğa eklenmiş.",
            "warning"
        )

        return redirect(
            url_for(
                "script_execution.execution_detail",
                execution_id=execution_id
            )
        )

    try:
        rollback_execution_id = queue_script(
            client_id=execution["client_id"],
            script_content=rollback_script,
            requested_by=session["user_id"],
            timeout_seconds=(
                execution["timeout_seconds"] or 300
            ),
            rollback_of_execution_id=execution_id
        )

        set_rollback_execution(
            original_execution_id=execution_id,
            rollback_execution_id=rollback_execution_id
        )

        flash(
            "Rollback kuyruğa eklendi.",
            "success"
        )

        return redirect(
            url_for(
                "script_execution.execution_detail",
                execution_id=rollback_execution_id
            )
        )

    except ValueError as error:
        flash(
            str(error),
            "danger"
        )

    except Exception as error:
        flash(
            f"Rollback kuyruğa eklenemedi: {error}",
            "danger"
        )

    return redirect(
        url_for(
            "script_execution.execution_detail",
            execution_id=execution_id
        )
    )


@script_execution_bp.route(
    "/clients/<int:client_id>/executions"
)
@operator_required
def execution_history(client_id):
    client = get_client(client_id)

    if client is None:
        return "Client bulunamadı.", 404

    page = request.args.get(
        "page",
        default=1,
        type=int
    )

    per_page = request.args.get(
        "per_page",
        default=10,
        type=int
    )

    if per_page not in (10, 25, 50):
        per_page = 10

    search = request.args.get(
        "search",
        ""
    ).strip()

    status = request.args.get(
        "status",
        ""
    ).strip().lower()

    allowed_statuses = {
        "",
        "pending",
        "assigned",
        "running",
        "completed",
        "failed"
    }

    if status not in allowed_statuses:
        status = ""

    pagination = list_paginated_client_executions(
        client_id=client_id,
        page=page,
        per_page=per_page,
        search=search,
        status=status
    )

    start_page = max(
        1,
        pagination["page"] - 2
    )

    end_page = min(
        pagination["total_pages"],
        pagination["page"] + 2
    )

    filters = {
        "search": search,
        "status": status,
        "per_page": per_page
    }

    return render_template(
        "script_executions.html",
        client=client,
        executions=pagination["executions"],
        pagination=pagination,
        start_page=start_page,
        end_page=end_page,
        filters=filters
    )