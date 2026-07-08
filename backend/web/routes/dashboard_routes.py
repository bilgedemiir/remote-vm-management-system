from flask import Blueprint, render_template, redirect, url_for

from services.client_service import get_client_count
from utils.decorators import login_required

dashboard_bp = Blueprint(
    "dashboard",
    __name__,
    template_folder="../templates"
)


@dashboard_bp.route("/")
def index():
    return redirect(url_for("auth.login"))


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    total_clients = get_client_count()

    return render_template(
        "dashboard.html",
        total_clients=total_clients
    )