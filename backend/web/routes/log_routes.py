from flask import (
    Blueprint,
    render_template,
    request
)

from backend.utils.decorators import (
    viewer_required
)

from backend.services.log_service import (
    list_paginated_logs,
    list_log_event_types
)

log_bp = Blueprint(
    "logs",
    __name__,
    template_folder="../templates"
)


@log_bp.route("/logs")
@viewer_required
def logs():
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

    event_type = request.args.get(
        "event_type",
        ""
    ).strip()

    level = request.args.get(
        "level",
        ""
    ).strip().lower()

    start_date = request.args.get(
        "start_date",
        ""
    ).strip()

    end_date = request.args.get(
        "end_date",
        ""
    ).strip()

    pagination = list_paginated_logs(
        page=page,
        per_page=per_page,
        search=search,
        event_type=event_type,
        level=level,
        start_date=start_date,
        end_date=end_date
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
        "event_type": event_type,
        "level": level,
        "start_date": start_date,
        "end_date": end_date,
        "per_page": per_page
    }

    return render_template(
        "logs.html",
        logs=pagination["logs"],
        pagination=pagination,
        start_page=start_page,
        end_page=end_page,
        event_types=list_log_event_types(),
        filters=filters
    )