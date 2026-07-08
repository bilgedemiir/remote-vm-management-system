from flask import Blueprint, render_template

from services.client_service import get_clients, get_client_detail
from services.command_service import get_client_commands
from utils.decorators import login_required


client_bp = Blueprint(
    "client",
    __name__,
    template_folder="../templates"
)


@client_bp.route("/clients")
@login_required
def clients():
    client_list = get_clients()

    return render_template(
        "clients.html",
        clients=client_list
    )


@client_bp.route("/clients/<int:client_id>")
@login_required
def client_detail(client_id):
    client = get_client_detail(client_id)

    if not client:
        return "Client bulunamadı.", 404

    commands = get_client_commands(client_id)

    return render_template(
        "client_detail.html",
        client=client,
        commands=commands
    )