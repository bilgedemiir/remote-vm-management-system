from backend.database.repositories.script_repository import (
    create_script,
    delete_script,
    get_all_scripts,
    get_script_by_id,
    get_script_by_name,
    set_script_active,
    update_current_version,
)

from backend.database.repositories.script_version_repository import (
    create_script_version,
    get_next_version_number,
    get_versions,
)

from backend.services.script_analyzer import (
    validate_script_or_raise,
)


def list_scripts():
    return get_all_scripts()


def get_script(script_id):
    return get_script_by_id(script_id)


def list_versions(script_id):
    return get_versions(script_id)


def create_new_script(
    name,
    description,
    category,
    script_content,
    created_by
):
    name = name.strip()
    description = description.strip()
    category = category.strip()
    script_content = script_content.strip()

    if not name:
        raise ValueError("Script adı boş bırakılamaz.")

    if not script_content:
        raise ValueError("Script içeriği boş bırakılamaz.")

    existing_script = get_script_by_name(name)

    if existing_script is not None:
        raise ValueError(
            "Bu isimde bir script zaten bulunmaktadır."
        )

    # Script veritabanına kaydedilmeden önce analiz edilir.
    validate_script_or_raise(script_content)

    script_id = None

    try:
        script_id = create_script(
            name=name,
            description=description,
            category=category,
            created_by=created_by,
        )

        version_number = 1

        create_script_version(
            script_id=script_id,
            version_number=version_number,
            title=f"{name} v{version_number}",
            script_content=script_content,
            created_by=created_by,
            change_log="İlk script versiyonu oluşturuldu.",
        )

        update_current_version(
            script_id=script_id,
            current_version=version_number,
        )

        return script_id

    except Exception:
        # Script kaydı oluşturulup versiyon kaydı başarısız
        # olursa boş script kaydını temizler.
        if script_id is not None:
            try:
                delete_script(script_id)
            except Exception:
                pass

        raise


def create_new_version(
    script_id,
    script_content,
    created_by,
    change_log
):
    script_content = script_content.strip()
    change_log = change_log.strip()

    script = get_script_by_id(script_id)

    if script is None:
        raise ValueError("Script bulunamadı.")

    if not script_content:
        raise ValueError(
            "Yeni versiyonun script içeriği boş bırakılamaz."
        )

    # Yeni versiyon da kaydedilmeden önce analiz edilir.
    validate_script_or_raise(script_content)

    version_number = get_next_version_number(script_id)

    version_id = create_script_version(
        script_id=script_id,
        version_number=version_number,
        title=f"{script['name']} v{version_number}",
        script_content=script_content,
        created_by=created_by,
        change_log=(
            change_log
            if change_log
            else f"Versiyon {version_number} oluşturuldu."
        ),
    )

    update_current_version(
        script_id=script_id,
        current_version=version_number,
    )

    return version_id


def change_script_status(
    script_id,
    is_active
):
    script = get_script_by_id(script_id)

    if script is None:
        raise ValueError("Script bulunamadı.")

    set_script_active(
        script_id=script_id,
        is_active=bool(is_active),
    )