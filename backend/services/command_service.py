from database.repositories.command_repository import get_commands_by_client_id


def get_client_commands(client_id):
    return get_commands_by_client_id(client_id)