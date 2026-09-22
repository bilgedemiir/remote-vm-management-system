import os

from flask import Blueprint, current_app, send_from_directory


download_bp = Blueprint(
    "download",
    __name__
)


@download_bp.route("/download/agent")
def download_agent():
    downloads_folder = os.path.join(
        current_app.root_path,
        "downloads"
    )

    return send_from_directory(
        downloads_folder,
        "RemoteVMAgentSetup.exe",
        as_attachment=True
    )