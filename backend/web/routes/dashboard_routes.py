from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for
)

from backend.utils.decorators import (
    login_required,
    operator_required
)

from backend.services.client_service import (
    get_client_count,
    get_online_client_count,
    get_last_active_client
)

from backend.services.script_execution_service import (
    list_recent_executions
)



dashboard_bp = Blueprint(
    "dashboard",
    __name__,
    template_folder="../templates"
)


@dashboard_bp.route("/")
def index():
    return redirect(url_for("auth.login"))


@dashboard_bp.route("/dashboard")
@operator_required
def dashboard():
    total_clients = get_client_count()
    online_clients = get_online_client_count()
    offline_clients = total_clients - online_clients
    recent_executions = list_recent_executions(10)
    last_active_client = get_last_active_client()
    offline_clients = total_clients - online_clients

    return render_template(
        "dashboard.html",
        total_clients=total_clients,
        online_clients=online_clients,
        offline_clients=offline_clients,
        last_active_client=last_active_client,
        recent_executions=recent_executions
    )