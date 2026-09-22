from backend.database.repositories.group_repository import (
    get_all_groups,
    get_group_by_id,
    create_group,
    update_group,
    delete_group,
    get_client_groups,
    set_client_groups,
    get_clients_by_group_ids,
    add_clients_to_groups,
    get_group_members,
    delete_group_member
)


def list_groups():
    return get_all_groups()


def get_group(group_id):
    return get_group_by_id(group_id)


def add_group(
    name,
    description,
    created_by=None
):
    name = name.strip()

    if not name:
        raise ValueError(
            "Grup adı boş olamaz."
        )

    create_group(
        name=name,
        description=description.strip(),
        created_by=created_by
    )


def edit_group(
    group_id,
    name,
    description
):
    name = name.strip()

    if not name:
        raise ValueError(
            "Grup adı boş olamaz."
        )

    update_group(
        group_id=group_id,
        name=name,
        description=description.strip()
    )


def remove_group(group_id):
    delete_group(group_id)


def list_client_groups(client_id):
    return get_client_groups(client_id)


def update_client_groups(
    client_id,
    group_ids,
    added_by=None
):
    group_ids = [
        int(group_id)
        for group_id in group_ids
    ]

    set_client_groups(
        client_id=client_id,
        group_ids=group_ids,
        added_by=added_by
    )


def list_clients_for_groups(group_ids):
    group_ids = [
        int(group_id)
        for group_id in group_ids
    ]

    return get_clients_by_group_ids(
        group_ids
    )


def bulk_add_clients_to_groups(
    client_ids,
    group_ids,
    added_by=None
):
    try:
        client_ids = list({
            int(client_id)
            for client_id in client_ids
        })

        group_ids = list({
            int(group_id)
            for group_id in group_ids
        })

    except (TypeError, ValueError):
        raise ValueError(
            "Geçersiz istemci veya grup bilgisi."
        )

    if not client_ids:
        raise ValueError(
            "En az bir istemci seçmelisiniz."
        )

    if not group_ids:
        raise ValueError(
            "En az bir grup seçmelisiniz."
        )

    return add_clients_to_groups(
        client_ids=client_ids,
        group_ids=group_ids,
        added_by=added_by
    )


def list_group_members(group_id):
    return get_group_members(group_id)


def remove_client_from_group(
    group_id,
    client_id
):
    deleted_count = delete_group_member(
        group_id=group_id,
        client_id=client_id
    )

    if deleted_count == 0:
        raise ValueError(
            "İstemci bu grubun üyesi değil."
        )