import uuid
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for
)

from backend.services.ai_service import (
    generate_powershell
)

from backend.services.client_service import (
    get_client,
    list_paginated_clients,
    list_paginated_installed_apps,
    list_paginated_running_apps,
    list_paginated_software_updates,
    list_paginated_client_ports,
    list_paginated_client_port_events
)

from backend.services.group_service import (
    list_groups,
    list_client_groups,
    update_client_groups,
    bulk_add_clients_to_groups
)

from backend.services.log_service import (
    list_client_logs
)

from backend.services.cve_service import (
    list_client_cve_findings,
    get_client_cve_count
)

from backend.services.nmap_service import (
    get_client_nmap_status,
    queue_bulk_nmap_scans,
    get_nmap_batch_results,
    merge_agent_ports_with_nmap
)

from backend.database.repositories.client_repository import (
    get_all_clients
)

from backend.database.repositories.cve_scan_job_repository import (
    create_cve_scan_job,
    get_cve_scan_jobs_by_batch
)

from backend.database.repositories.nmap_scan_repository import (
    create_nmap_scan
)

from backend.services.software_update_service import (
    get_software_update,
    build_winget_upgrade_script
)

from backend.services.script_execution_service import (
    queue_script
)

from backend.utils.decorators import (
    admin_required,
    login_required,
    operator_required
)


client_bp = Blueprint(
    "client",
    __name__,
    template_folder="../templates"
)


def get_installed_apps_context(client_id):
    apps_page = request.args.get(
        "apps_page",
        default=1,
        type=int
    )

    apps_per_page = request.args.get(
        "apps_per_page",
        default=10,
        type=int
    )

    if apps_per_page not in (10, 25, 50):
        apps_per_page = 10

    apps_search = request.args.get(
        "apps_search",
        ""
    ).strip()

    pagination = list_paginated_installed_apps(
        client_id=client_id,
        page=apps_page,
        per_page=apps_per_page,
        search=apps_search
    )

    start_page = max(
        1,
        pagination["page"] - 2
    )

    end_page = min(
        pagination["total_pages"],
        pagination["page"] + 2
    )

    return {
        "installed_apps": pagination["items"],
        "apps_pagination": pagination,
        "apps_start_page": start_page,
        "apps_end_page": end_page,
        "apps_filters": {
            "search": apps_search,
            "per_page": apps_per_page
        },
        "show_installed_apps": (
            bool(apps_search)
            or apps_page > 1
        )
    }


def get_running_apps_context(client_id):
    running_page = request.args.get(
        "running_page",
        default=1,
        type=int
    )

    running_per_page = request.args.get(
        "running_per_page",
        default=10,
        type=int
    )

    if running_per_page not in (10, 25, 50):
        running_per_page = 10

    running_search = request.args.get(
        "running_search",
        ""
    ).strip()

    pagination = list_paginated_running_apps(
        client_id=client_id,
        page=running_page,
        per_page=running_per_page,
        search=running_search
    )

    start_page = max(
        1,
        pagination["page"] - 2
    )

    end_page = min(
        pagination["total_pages"],
        pagination["page"] + 2
    )

    return {
        "running_apps": pagination["items"],
        "running_pagination": pagination,
        "running_start_page": start_page,
        "running_end_page": end_page,
        "running_filters": {
            "search": running_search,
            "per_page": running_per_page
        },
        "show_running_apps": (
            bool(running_search)
            or running_page > 1
        )
    }


def get_port_inventory_context(
    client_id
):
    ports_page = request.args.get(
        "ports_page",
        default=1,
        type=int
    )

    ports_per_page = request.args.get(
        "ports_per_page",
        default=10,
        type=int
    )

    if ports_per_page not in (
        10,
        25,
        50
    ):
        ports_per_page = 10

    ports_search = request.args.get(
        "ports_search",
        ""
    ).strip()

    ports_protocol = request.args.get(
        "ports_protocol",
        ""
    ).strip().upper()

    if ports_protocol not in (
        "",
        "TCP",
        "UDP"
    ):
        ports_protocol = ""

    show_ports = (
        request.args.get(
            "show_ports",
            default=0,
            type=int
        )
        == 1
    )

    pagination = (
        list_paginated_client_ports(
            client_id=client_id,
            page=ports_page,
            per_page=ports_per_page,
            search=ports_search,
            protocol=ports_protocol
        )
    )

    start_page = max(
        1,
        pagination["page"] - 2
    )

    end_page = min(
        pagination["total_pages"],
        pagination["page"] + 2
    )

    return {
        "client_ports": pagination["items"],
        "ports_pagination": pagination,
        "ports_start_page": start_page,
        "ports_end_page": end_page,
        "ports_summary": pagination[
            "summary"
        ],
        "ports_filters": {
            "search": ports_search,
            "protocol": ports_protocol,
            "per_page": ports_per_page
        },
        "show_port_inventory": (
            show_ports
            or bool(ports_search)
            or bool(ports_protocol)
            or ports_page > 1
            or ports_per_page != 10
        )
    }


def get_port_event_context(
    client_id
):
    events_page = request.args.get(
        "events_page",
        default=1,
        type=int
    )

    events_per_page = request.args.get(
        "events_per_page",
        default=10,
        type=int
    )

    if events_per_page not in (
        10,
        25,
        50
    ):
        events_per_page = 10

    events_search = request.args.get(
        "events_search",
        ""
    ).strip()

    events_protocol = request.args.get(
        "events_protocol",
        ""
    ).strip().upper()

    if events_protocol not in (
        "",
        "TCP",
        "UDP"
    ):
        events_protocol = ""

    events_type = request.args.get(
        "events_type",
        ""
    ).strip().upper()

    if events_type not in (
        "",
        "OPENED",
        "CLOSED"
    ):
        events_type = ""

    show_port_events = (
        request.args.get(
            "show_port_events",
            default=0,
            type=int
        )
        == 1
    )

    pagination = (
        list_paginated_client_port_events(
            client_id=client_id,
            page=events_page,
            per_page=events_per_page,
            search=events_search,
            protocol=events_protocol,
            event_type=events_type
        )
    )

    start_page = max(
        1,
        pagination["page"] - 2
    )

    end_page = min(
        pagination["total_pages"],
        pagination["page"] + 2
    )

    return {
        "port_events": pagination["items"],
        "port_events_pagination": pagination,
        "port_events_start_page": start_page,
        "port_events_end_page": end_page,
        "port_events_summary": pagination[
            "summary"
        ],
        "port_events_filters": {
            "search": events_search,
            "protocol": events_protocol,
            "event_type": events_type,
            "per_page": events_per_page
        },
        "show_port_events": (
            show_port_events
            or bool(events_search)
            or bool(events_protocol)
            or bool(events_type)
            or events_page > 1
            or events_per_page != 10
        )
    }


def get_nmap_context(
    client_id,
    client_ports
):
    nmap_data = get_client_nmap_status(
        client_id
    )

    merge_agent_ports_with_nmap(
        ports=client_ports,
        latest_scan=nmap_data["latest_scan"],
        nmap_results=nmap_data["results"]
    )

    return {
        "latest_nmap_scan": nmap_data[
            "latest_scan"
        ],
        "nmap_results": nmap_data[
            "results"
        ],
        "nmap_scan_active": nmap_data[
            "has_active_scan"
        ]
    }


def get_software_updates_context(client_id):
    updates_page = request.args.get(
        "updates_page",
        default=1,
        type=int
    )

    updates_per_page = request.args.get(
        "updates_per_page",
        default=10,
        type=int
    )

    if updates_per_page not in (10, 25, 50):
        updates_per_page = 10

    updates_search = request.args.get(
        "updates_search",
        ""
    ).strip()

    pagination = list_paginated_software_updates(
        client_id=client_id,
        page=updates_page,
        per_page=updates_per_page,
        search=updates_search
    )

    start_page = max(
        1,
        pagination["page"] - 2
    )

    end_page = min(
        pagination["total_pages"],
        pagination["page"] + 2
    )

    return {
        "software_updates": pagination["items"],
        "updates_pagination": pagination,
        "updates_start_page": start_page,
        "updates_end_page": end_page,
        "updates_filters": {
            "search": updates_search,
            "per_page": updates_per_page
        },
        "show_software_updates": (
            bool(updates_search)
            or updates_page > 1
        )
    }


def get_cve_context(client_id):
    findings = list_client_cve_findings(
        client_id
    )

    total = get_client_cve_count(
        client_id
    )

    show_cves = (
        request.args.get(
            "show_cves",
            ""
        )
        == "1"
    )

    return {
        "cve_findings": findings,
        "cve_count": total,
        "show_cve_findings": show_cves
    }


@client_bp.route("/clients")
@operator_required
def clients():
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

    if status not in (
        "",
        "online",
        "offline"
    ):
        status = ""

    pagination = list_paginated_clients(
        page=page,
        per_page=per_page,
        search=search,
        status=status
    )

    groups = list_groups()

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
        "clients.html",
        clients=pagination["clients"],
        pagination=pagination,
        start_page=start_page,
        end_page=end_page,
        filters=filters,
        groups=groups
    )


@client_bp.route("/clients/<int:client_id>")
@operator_required
def client_detail(client_id):
    client = get_client(client_id)

    if client is None:
        return "Client bulunamadı.", 404

    logs = list_client_logs(client_id)

    groups = list_groups()

    client_groups = list_client_groups(
        client_id
    )

    selected_group_ids = {
        group["id"]
        for group in client_groups
    }

    apps_context = get_installed_apps_context(
        client_id
    )

    running_context = get_running_apps_context(
        client_id
    )

    updates_context = get_software_updates_context(
        client_id
    )

    cve_context = get_cve_context(
        client_id
    )

    ports_context = get_port_inventory_context(
        client_id
    )

    port_events_context = get_port_event_context(
        client_id
    )

    nmap_context = get_nmap_context(
        client_id=client_id,
        client_ports=ports_context[
            "client_ports"
        ]
    )

    return render_template(
        "client_detail.html",
        client=client,
        logs=logs,
        ai_request="",
        generated_command="",
        ai_error=None,
        groups=groups,
        selected_group_ids=selected_group_ids,
        **apps_context,
        **running_context,
        **updates_context,
        **cve_context,
        **ports_context,
        **port_events_context,
        **nmap_context
    )


@client_bp.route(
    "/clients/<int:client_id>/generate-ai-command",
    methods=["POST"]
)
@operator_required
def generate_ai_command(client_id):
    client = get_client(client_id)

    if client is None:
        return "Client bulunamadı.", 404

    logs = list_client_logs(client_id)

    groups = list_groups()

    client_groups = list_client_groups(
        client_id
    )

    selected_group_ids = {
        group["id"]
        for group in client_groups
    }

    apps_context = get_installed_apps_context(
        client_id
    )

    running_context = get_running_apps_context(
        client_id
    )

    updates_context = get_software_updates_context(
        client_id
    )

    cve_context = get_cve_context(
        client_id
    )

    ports_context = get_port_inventory_context(
        client_id
    )

    port_events_context = get_port_event_context(
        client_id
    )

    nmap_context = get_nmap_context(
        client_id=client_id,
        client_ports=ports_context[
            "client_ports"
        ]
    )

    if client["status"] != "online":
        return render_template(
            "client_detail.html",
            client=client,
            logs=logs,
            ai_request="",
            generated_command="",
            ai_error=(
                "Client çevrimdışı olduğu için "
                "AI komutu oluşturulamaz."
            ),
            groups=groups,
            selected_group_ids=(
                selected_group_ids
            ),
            **apps_context,
            **running_context,
            **updates_context,
            **cve_context,
            **ports_context,
            **port_events_context,
            **nmap_context
        )

    ai_request = request.form.get(
        "ai_request",
        ""
    ).strip()

    generated_command = ""
    ai_error = None

    if not ai_request:
        ai_error = (
            "Lütfen yapmak istediğiniz işlemi yazın."
        )

    else:
        try:
            generated_command = (
                generate_powershell(
                    ai_request
                )
            )

        except Exception as error:
            ai_error = (
                "PowerShell komutu oluşturulamadı: "
                f"{error}"
            )

    return render_template(
        "client_detail.html",
        client=client,
        logs=logs,
        ai_request=ai_request,
        generated_command=generated_command,
        ai_error=ai_error,
        groups=groups,
        selected_group_ids=(
            selected_group_ids
        ),
        **apps_context,
        **running_context,
        **updates_context,
        **cve_context,
        **ports_context,
        **port_events_context,
        **nmap_context
    )


@client_bp.route(
    "/clients/<int:client_id>/scan-cves",
    methods=["POST"]
)
@operator_required
def scan_cves(client_id):
    client = get_client(
        client_id
    )

    if client is None:
        return "Client bulunamadı.", 404

    try:
        job_result = create_cve_scan_job(
            client_id=client_id,
            trigger_type="manual"
        )

        if job_result["created"]:
            flash(
                (
                    "CVE taraması kuyruğa alındı. "
                    "Tarama arka planda gerçekleştirilecek."
                ),
                "success"
            )

        else:
            current_status = (
                "çalışıyor"
                if job_result["status"] == "running"
                else "bekliyor"
            )

            flash(
                (
                    "Bu istemci için CVE taraması "
                    f"zaten {current_status}."
                ),
                "warning"
            )

    except Exception:
        flash(
            (
                "CVE taraması kuyruğa "
                "eklenirken bir hata oluştu."
            ),
            "danger"
        )

    return redirect(
        url_for(
            "client.client_detail",
            client_id=client_id,
            show_cves=1
        )
    )


@client_bp.route(
    "/clients/scan-cves",
    methods=["POST"]
)
@operator_required
def scan_all_client_cves():
    clients = get_all_clients()

    if not clients:
        flash(
            "CVE taraması yapılabilecek istemci bulunamadı.",
            "warning"
        )

        return redirect(
            url_for(
                "client.clients"
            )
        )

    batch_id = str(
        uuid.uuid4()
    )

    created_count = 0
    skipped_count = 0

    try:
        for client in clients:
            result = create_cve_scan_job(
                client_id=client["id"],
                trigger_type="bulk",
                batch_id=batch_id
            )

            if result["created"]:
                created_count += 1

            else:
                skipped_count += 1

        if created_count:
            message = (
                f"{created_count} istemci için CVE "
                "taraması kuyruğa alındı."
            )

            if skipped_count:
                message += (
                    f" {skipped_count} istemcide zaten "
                    "bekleyen veya çalışan tarama vardı."
                )

            flash(
                message,
                "success"
            )

        else:
            flash(
                (
                    "Bütün istemciler için zaten bekleyen "
                    "veya çalışan CVE taraması bulunuyor."
                ),
                "warning"
            )

    except Exception:
        flash(
            (
                "Toplu CVE taraması kuyruğa "
                "eklenirken bir hata oluştu."
            ),
            "danger"
        )

    if created_count:
        return redirect(
            url_for(
                "client.cve_scan_batch_detail",
                batch_id=batch_id
            )
        )

    return redirect(
        url_for(
            "client.clients"
        )
    )


@client_bp.route(
    "/clients/<int:client_id>/nmap-scan",
    methods=["POST"]
)
@operator_required
def start_nmap_scan(client_id):
    client = get_client(
        client_id
    )

    if client is None:
        return "Client bulunamadı.", 404

    if client["status"] != "online":
        flash(
            (
                "İstemci çevrimdışı olduğu için "
                "Nmap taraması başlatılamaz."
            ),
            "warning"
        )

        return redirect(
            url_for(
                "client.client_detail",
                client_id=client_id,
                show_ports=1,
                _anchor="portInventorySection"
            )
        )

    target_ip = str(
        client.get("ip_address")
        or ""
    ).strip()

    if not target_ip:
        flash(
            "İstemcinin IP adresi bulunmuyor.",
            "warning"
        )

        return redirect(
            url_for(
                "client.client_detail",
                client_id=client_id,
                show_ports=1,
                _anchor="portInventorySection"
            )
        )

    try:
        result = create_nmap_scan(
            client_id=client_id,
            target_ip=target_ip,
            scan_type="agent_ports",
            trigger_type="manual"
        )

        if result["created"]:
            flash(
                (
                    "Nmap taraması kuyruğa alındı. "
                    "Agent tarafından bildirilen TCP "
                    "portları ağ üzerinden kontrol edilecek."
                ),
                "success"
            )

        else:
            current_status = (
                "çalışıyor"
                if result["status"] == "running"
                else "bekliyor"
            )

            flash(
                (
                    "Bu istemci için Nmap taraması "
                    f"zaten {current_status}."
                ),
                "warning"
            )

    except Exception:
        flash(
            (
                "Nmap taraması kuyruğa "
                "eklenirken bir hata oluştu."
            ),
            "danger"
        )

    return redirect(
        url_for(
            "client.client_detail",
            client_id=client_id,
            show_ports=1,
            _anchor="portInventorySection"
        )
    )


@client_bp.route(
    "/clients/nmap-scans",
    methods=["POST"]
)
@operator_required
def start_all_nmap_scans():
    try:
        result = queue_bulk_nmap_scans()

        queued_count = result[
            "queued_count"
        ]

        active_count = result[
            "active_count"
        ]

        skipped_count = result[
            "skipped_count"
        ]

        if queued_count > 0:
            message = (
                f"{queued_count} istemci için Nmap "
                "taraması kuyruğa alındı."
            )

            if active_count:
                message += (
                    f" {active_count} istemcide zaten "
                    "bekleyen veya çalışan tarama vardı."
                )

            if skipped_count:
                message += (
                    f" {skipped_count} istemci çevrimdışı, "
                    "geçersiz IP'ye sahip veya taranabilecek "
                    "TCP portu bulunmadığı için atlandı."
                )

            flash(
                message,
                "success"
            )

            return redirect(
                url_for(
                    "client.nmap_scan_batch_detail",
                    batch_uuid=result[
                        "batch_uuid"
                    ]
                )
            )

        if active_count:
            flash(
                (
                    "Uygun istemcilerin tamamında zaten "
                    "bekleyen veya çalışan Nmap taraması "
                    "bulunuyor."
                ),
                "warning"
            )

        else:
            flash(
                (
                    "Nmap taraması yapılabilecek çevrimiçi, "
                    "geçerli IP adresine ve TCP port "
                    "envanterine sahip istemci bulunamadı."
                ),
                "warning"
            )

    except Exception:
        flash(
            (
                "Toplu Nmap taraması kuyruğa "
                "eklenirken bir hata oluştu."
            ),
            "danger"
        )

    return redirect(
        url_for(
            "client.clients"
        )
    )


@client_bp.route(
    "/nmap-scans/batches/<string:batch_uuid>",
    methods=["GET"]
)
@operator_required
def nmap_scan_batch_detail(
    batch_uuid
):
    batch_results = get_nmap_batch_results(
        batch_uuid
    )

    if batch_results is None:
        return (
            "Nmap toplu tarama kaydı bulunamadı.",
            404
        )

    return render_template(
        "nmap_scan_batch_detail.html",
        batch=batch_results["batch"],
        scans=batch_results["scans"],
        active_count=batch_results[
            "active_count"
        ],
        has_active_scans=batch_results[
            "is_active"
        ]
    )


@client_bp.route(
    "/cve-scans/batches/<string:batch_id>",
    methods=["GET"]
)
@operator_required
def cve_scan_batch_detail(
    batch_id
):
    jobs = get_cve_scan_jobs_by_batch(
        batch_id
    )

    if not jobs:
        return "CVE toplu tarama kaydı bulunamadı.", 404

    summary = {
        "total": len(jobs),
        "pending": 0,
        "running": 0,
        "completed": 0,
        "failed": 0,
        "total_findings": 0
    }

    for job in jobs:
        status = job["status"]

        if status in summary:
            summary[status] += 1

        summary["total_findings"] += (
            job["findings_count"] or 0
        )

    has_active_jobs = (
        summary["pending"] > 0
        or summary["running"] > 0
    )

    return render_template(
        "cve_scan_batch_detail.html",
        batch_id=batch_id,
        jobs=jobs,
        summary=summary,
        has_active_jobs=has_active_jobs
    )


@client_bp.route(
    (
        "/clients/<int:client_id>/"
        "software-updates/<int:update_id>/upgrade"
    ),
    methods=["POST"]
)
@admin_required
def upgrade_software(
    client_id,
    update_id
):
    client = get_client(
        client_id
    )

    if client is None:
        return "Client bulunamadı.", 404

    if client["status"] != "online":
        flash(
            (
                "Client çevrimdışı olduğu için "
                "yazılım güncellenemez."
            ),
            "warning"
        )

        return redirect(
            url_for(
                "client.client_detail",
                client_id=client_id
            )
        )

    software_update = get_software_update(
        update_id=update_id,
        client_id=client_id
    )

    if software_update is None:
        flash(
            "Yazılım güncelleme kaydı bulunamadı.",
            "danger"
        )

        return redirect(
            url_for(
                "client.client_detail",
                client_id=client_id
            )
        )

    try:
        script_content = (
            build_winget_upgrade_script(
                software_update
            )
        )

        execution_id = queue_script(
            client_id=client_id,
            script_content=script_content,
            requested_by=session["user_id"],
            timeout_seconds=1800,
            execution_type="software_update"
        )

    except ValueError as error:
        flash(
            str(error),
            "warning"
        )

        return redirect(
            url_for(
                "client.client_detail",
                client_id=client_id
            )
        )

    except Exception:
        flash(
            (
                "Yazılım güncellemesi "
                "başlatılamadı."
            ),
            "danger"
        )

        return redirect(
            url_for(
                "client.client_detail",
                client_id=client_id
            )
        )

    return redirect(
        url_for(
            "script_execution.execution_detail",
            execution_id=execution_id
        )
    )


@client_bp.route(
    "/clients/<int:client_id>/groups",
    methods=["POST"]
)
@admin_required
def update_groups(client_id):

    client = get_client(client_id)

    if client is None:
        return "Client bulunamadı.", 404

    group_ids = request.form.getlist(
        "group_ids"
    )

    update_client_groups(
        client_id=client_id,
        group_ids=group_ids,
        added_by=session["user_id"]
    )

    flash(
        "Gruplar güncellendi.",
        "success"
    )

    return redirect(
        url_for(
            "client.client_detail",
            client_id=client_id
        )
    )


@client_bp.route(
    "/clients/groups/bulk-add",
    methods=["POST"]
)
@admin_required
def bulk_add_groups():
    client_ids = request.form.getlist(
        "client_ids"
    )

    group_ids = request.form.getlist(
        "group_ids"
    )

    try:
        added_count = bulk_add_clients_to_groups(
            client_ids=client_ids,
            group_ids=group_ids,
            added_by=session["user_id"]
        )

        if added_count > 0:
            flash(
                f"{added_count} yeni grup üyeliği eklendi.",
                "success"
            )
        else:
            flash(
                "Seçilen istemciler zaten seçilen gruplara üye.",
                "info"
            )

    except ValueError as error:
        flash(
            str(error),
            "warning"
        )

    except Exception:
        flash(
            "Toplu grup atama sırasında bir hata oluştu.",
            "danger"
        )

    return redirect(
        url_for("client.clients")
    )