import ipaddress
import shutil
import subprocess
from defusedxml import (
    ElementTree as ET
)

from backend.database.repositories.port_inventory_repository import (
    get_client_port_inventory
)

from backend.database.repositories.nmap_scan_repository import (
    create_nmap_scan,
    create_nmap_scan_batch,
    delete_empty_nmap_scan_batch,
    get_latest_nmap_scan,
    get_nmap_results_by_scan,
    get_nmap_scan_batch_by_uuid,
    get_nmap_scans_by_batch
)

from backend.database.repositories.client_repository import (
    get_all_clients
)


NMAP_PROCESS_TIMEOUT_SECONDS = 180
NMAP_HOST_TIMEOUT = "120s"


def find_nmap_executable():
    nmap_path = shutil.which(
        "nmap"
    )

    if not nmap_path:
        raise FileNotFoundError(
            "Nmap bulunamadı. Nmap'in kurulu "
            "ve PATH içinde olduğundan emin olun."
        )

    return nmap_path


def validate_nmap_target(
    target_ip
):
    target_ip = str(
        target_ip or ""
    ).strip()

    try:
        ip_object = ipaddress.ip_address(
            target_ip
        )

    except ValueError as error:
        raise ValueError(
            "Geçersiz Nmap hedef IP adresi."
        ) from error

    allowed_target = (
        ip_object.is_private
        or ip_object.is_loopback
        or ip_object.is_link_local
    )

    if not allowed_target:
        raise ValueError(
            "Nmap taraması yalnızca yerel veya "
            "özel ağ adreslerinde yapılabilir."
        )

    if (
        ip_object.is_multicast
        or ip_object.is_unspecified
    ):
        raise ValueError(
            "Bu IP adresi Nmap hedefi olarak "
            "kullanılamaz."
        )

    return str(
        ip_object
    )


def get_agent_tcp_ports(
    client_id
):
    inventory = get_client_port_inventory(
        client_id
    )

    ports = {
        int(port["local_port"])
        for port in inventory
        if (
            str(
                port.get("protocol")
                or ""
            ).upper()
            == "TCP"
            and 1
            <= int(port["local_port"])
            <= 65535
        )
    }

    return sorted(
        ports
    )


def build_nmap_command(
    target_ip,
    ports
):
    nmap_path = find_nmap_executable()

    command = [
        nmap_path,
        "-Pn",
        "-sT",
        "-sV",
        "--version-light",
        "--reason",
        "--host-timeout",
        NMAP_HOST_TIMEOUT,
        "-p",
        ",".join(
            str(port)
            for port in ports
        ),
        "-oX",
        "-"
    ]

    ip_object = ipaddress.ip_address(
        target_ip
    )

    if ip_object.version == 6:
        command.append(
            "-6"
        )

    command.append(
        target_ip
    )

    return command


def parse_nmap_xml(
    xml_output,
    requested_ports
):
    try:
        root = ET.fromstring(
            xml_output
        )

    except ET.ParseError as error:
        raise ValueError(
            "Nmap XML çıktısı ayrıştırılamadı."
        ) from error

    host = root.find("host")

    if host is None:
        raise RuntimeError(
            "Nmap çıktısında hedef bilgisi bulunamadı."
        )

    host_status = host.find(
        "status"
    )

    if (
        host_status is not None
        and host_status.get("state")
        != "up"
    ):
        raise RuntimeError(
            "Nmap hedef istemciye ulaşamadı."
        )

    ports_element = host.find(
        "ports"
    )

    parsed_results = []
    parsed_port_numbers = set()

    if ports_element is not None:
        for port_element in ports_element.findall(
            "port"
        ):
            protocol = str(
                port_element.get(
                    "protocol"
                )
                or "tcp"
            ).upper()

            try:
                port_number = int(
                    port_element.get(
                        "portid"
                    )
                )

            except (
                TypeError,
                ValueError
            ):
                continue

            state_element = port_element.find(
                "state"
            )

            state = "unknown"
            reason = None

            if state_element is not None:
                state = str(
                    state_element.get(
                        "state"
                    )
                    or "unknown"
                ).lower()

                reason = state_element.get(
                    "reason"
                )

            service_element = port_element.find(
                "service"
            )

            service_name = None
            product = None
            service_version = None
            extra_info = None

            if service_element is not None:
                service_name = (
                    service_element.get(
                        "name"
                    )
                )

                product = (
                    service_element.get(
                        "product"
                    )
                )

                service_version = (
                    service_element.get(
                        "version"
                    )
                )

                extra_info = (
                    service_element.get(
                        "extrainfo"
                    )
                )

            parsed_results.append(
                {
                    "protocol": protocol,
                    "port_number": port_number,
                    "state": state,
                    "service_name": service_name,
                    "product": product,
                    "service_version": (
                        service_version
                    ),
                    "extra_info": extra_info,
                    "reason": reason
                }
            )

            parsed_port_numbers.add(
                port_number
            )

    missing_port_state = "unknown"

    if ports_element is not None:
        extra_port_states = {
            str(
                extra_ports.get(
                    "state"
                )
                or "unknown"
            ).lower()
            for extra_ports
            in ports_element.findall(
                "extraports"
            )
        }

        if len(extra_port_states) == 1:
            missing_port_state = (
                next(
                    iter(
                        extra_port_states
                    )
                )
            )

    for port_number in requested_ports:
        if port_number in parsed_port_numbers:
            continue

        parsed_results.append(
            {
                "protocol": "TCP",
                "port_number": port_number,
                "state": missing_port_state,
                "service_name": None,
                "product": None,
                "service_version": None,
                "extra_info": None,
                "reason": None
            }
        )

    parsed_results.sort(
        key=lambda result: (
            result["protocol"],
            result["port_number"]
        )
    )

    return parsed_results


def run_agent_port_nmap_scan(
    client_id,
    target_ip
):
    validated_target = validate_nmap_target(
        target_ip
    )

    ports = get_agent_tcp_ports(
        client_id
    )

    if not ports:
        raise ValueError(
            "İstemciye ait taranabilecek TCP "
            "port envanteri bulunamadı."
        )

    command = build_nmap_command(
        target_ip=validated_target,
        ports=ports
    )

    completed_process = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=NMAP_PROCESS_TIMEOUT_SECONDS,
        shell=False,
        creationflags=getattr(
            subprocess,
            "CREATE_NO_WINDOW",
            0
        ),
        check=False
    )

    if completed_process.returncode != 0:
        error_message = (
            completed_process.stderr.strip()
            or completed_process.stdout.strip()
            or "Nmap bilinmeyen bir hata döndürdü."
        )

        raise RuntimeError(
            error_message
        )

    results = parse_nmap_xml(
        xml_output=completed_process.stdout,
        requested_ports=ports
    )

    return {
        "target_ip": validated_target,
        "requested_ports": ports,
        "results": results
    }


def get_client_nmap_status(
    client_id
):
    latest_scan = get_latest_nmap_scan(
        client_id
    )

    results = []

    if (
        latest_scan
        and latest_scan["status"]
        == "completed"
    ):
        results = get_nmap_results_by_scan(
            latest_scan["id"]
        )

    return {
        "latest_scan": latest_scan,
        "results": results,
        "has_active_scan": (
            latest_scan is not None
            and latest_scan["status"]
            in {
                "pending",
                "running"
            }
        )
    }


def queue_automatic_nmap_scan(
    client_id,
    target_ip
):
    try:
        validated_target = validate_nmap_target(
            target_ip
        )

    except ValueError:
        return {
            "scan_id": None,
            "created": False,
            "reason": "invalid_target"
        }

    ports = get_agent_tcp_ports(
        client_id
    )

    if not ports:
        return {
            "scan_id": None,
            "created": False,
            "reason": "no_tcp_ports"
        }

    return create_nmap_scan(
        client_id=client_id,
        target_ip=validated_target,
        scan_type="agent_ports",
        trigger_type="automatic"
    )


def queue_bulk_nmap_scans():
    clients = get_all_clients()

    if not clients:
        return {
            "batch_id": None,
            "batch_uuid": None,
            "queued_count": 0,
            "active_count": 0,
            "skipped_count": 0
        }

    batch = create_nmap_scan_batch()

    queued_count = 0
    active_count = 0
    skipped_count = 0

    for client in clients:
        if client.get("status") != "online":
            skipped_count += 1
            continue

        target_ip = str(
            client.get("ip_address") or ""
        ).strip()

        if not target_ip:
            skipped_count += 1
            continue

        try:
            validated_target = validate_nmap_target(
                target_ip
            )

            ports = get_agent_tcp_ports(
                client["id"]
            )

            if not ports:
                skipped_count += 1
                continue

            result = create_nmap_scan(
                client_id=client["id"],
                target_ip=validated_target,
                scan_type="agent_ports",
                trigger_type="bulk",
                batch_id=batch["batch_id"]
            )

            if result["created"]:
                queued_count += 1

            elif result["reason"] == "active_scan":
                active_count += 1

            else:
                skipped_count += 1

        except (
            TypeError,
            ValueError
        ):
            skipped_count += 1

    if queued_count == 0:
        delete_empty_nmap_scan_batch(
            batch["batch_id"]
        )

        return {
            "batch_id": None,
            "batch_uuid": None,
            "queued_count": 0,
            "active_count": active_count,
            "skipped_count": skipped_count
        }

    return {
        "batch_id": batch["batch_id"],
        "batch_uuid": batch["batch_uuid"],
        "queued_count": queued_count,
        "active_count": active_count,
        "skipped_count": skipped_count
    }


def get_nmap_batch_results(
    batch_uuid
):
    batch = get_nmap_scan_batch_by_uuid(
        batch_uuid
    )

    if batch is None:
        return None

    scans = get_nmap_scans_by_batch(
        batch["id"]
    )

    active_count = (
        int(batch["pending_count"])
        + int(batch["running_count"])
    )

    return {
        "batch": batch,
        "scans": scans,
        "active_count": active_count,
        "is_active": active_count > 0
    }
def merge_agent_ports_with_nmap(
    ports,
    latest_scan,
    nmap_results
):
    result_map = {}

    if (
        latest_scan
        and latest_scan["status"] == "completed"
    ):
        for result in nmap_results:
            key = (
                str(
                    result.get("protocol")
                    or ""
                ).upper(),
                int(
                    result["port_number"]
                )
            )

            result_map[key] = result

    for port in ports:
        protocol = str(
            port.get("protocol")
            or ""
        ).upper()

        port_number = int(
            port["local_port"]
        )

        port["nmap_state"] = None
        port["nmap_service_name"] = None
        port["network_status"] = "not_scanned"

        if protocol != "TCP":
            port["network_status"] = "udp_not_scanned"
            continue

        if (
            latest_scan is None
            or latest_scan["status"] != "completed"
        ):
            continue

        nmap_result = result_map.get(
            (
                protocol,
                port_number
            )
        )

        if nmap_result is None:
            port["network_status"] = "not_in_scan"
            continue

        nmap_state = str(
            nmap_result.get("state")
            or "unknown"
        ).strip().lower()

        port["nmap_state"] = nmap_state
        port["nmap_service_name"] = (
            nmap_result.get("service_name")
        )

        if nmap_state == "open":
            port["network_status"] = "accessible"

        elif nmap_state == "filtered":
            port["network_status"] = "filtered"

        elif nmap_state == "closed":
            port["network_status"] = "mismatch"

        else:
            port["network_status"] = "unknown"

    return ports