import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.append(BASE_DIR)

from backend.services.command_service import add_command

add_command(
    client_id=1,
    command_text="hostname"
)

print("Komut başarıyla eklendi.")