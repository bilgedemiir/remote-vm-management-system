import re

from backend.database.repositories.software_update_repository import (
    get_software_update_by_id
)


PACKAGE_VALUE_PATTERN = re.compile(
    r"^[A-Za-z0-9._+\-]+$"
)


def get_software_update(
    update_id,
    client_id
):
    return get_software_update_by_id(
        update_id=update_id,
        client_id=client_id
    )


def validate_package_value(
    value,
    field_name
):
    value = str(
        value or ""
    ).strip()

    if not value:
        raise ValueError(
            f"{field_name} bulunamadı."
        )

    if not PACKAGE_VALUE_PATTERN.fullmatch(
        value
    ):
        raise ValueError(
            f"Geçersiz {field_name}."
        )

    return value


def build_winget_upgrade_script(
    software_update
):
    if software_update is None:
        raise ValueError(
            "Yazılım güncelleme kaydı bulunamadı."
        )

    source = str(
        software_update.get("source") or ""
    ).strip().lower()

    if source != "winget":
        raise ValueError(
            "Bu yazılım WinGet üzerinden güncellenemez."
        )

    package_id = validate_package_value(
        software_update.get("package_id"),
        "paket kimliği"
    )

    target_version = validate_package_value(
        software_update.get(
            "available_version"
        ),
        "hedef sürüm"
    )

    script = f"""
$ErrorActionPreference = "Stop"

$packageId = '{package_id}'
$targetVersion = '{target_version}'

winget upgrade `
    --id $packageId `
    --version $targetVersion `
    --exact `
    --source winget `
    --silent `
    --accept-package-agreements `
    --accept-source-agreements `
    --disable-interactivity

$wingetExitCode = $LASTEXITCODE

if ($wingetExitCode -ne 0) {{
    Write-Error (
        "WinGet güncellemesi başarısız oldu. " +
        "Exit Code: $wingetExitCode"
    )

    exit $wingetExitCode
}}

Write-Output (
    "Yazılım başarıyla güncellendi: " +
    "$packageId -> $targetVersion"
)
""".strip()

    return script