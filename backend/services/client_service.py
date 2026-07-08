from database.repositories.client_repository import (
    get_all_clients,
    get_total_client_count,
    get_client_by_id
)


def get_clients():
    return get_all_clients()


def get_client_count():
    return get_total_client_count()


def get_client_detail(client_id):
    return get_client_by_id(client_id)