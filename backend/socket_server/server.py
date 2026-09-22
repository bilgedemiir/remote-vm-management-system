import json
import socket
import threading
import time
import traceback

from backend.database.repositories.client_repository import (
    create_client,
    get_client_by_uuid,
    update_client,
    update_client_status,
    update_client_system_info,
    mark_all_clients_offline,
    mark_stale_clients_offline
)

from backend.database.repositories.script_execution_repository import (
    get_pending_executions_by_client,
    claim_pending_execution
)

from backend.database.repositories.installed_app_repository import (
    replace_client_installed_apps
)

from backend.database.repositories.port_inventory_repository import (
    replace_client_port_inventory
)

from backend.database.repositories.software_update_repository import (
    replace_client_software_updates
)

from backend.database.repositories.running_app_repository import (
    replace_client_running_apps
)

from backend.services.script_execution_service import (
    execution_started,
    execution_completed,
    execution_failed,
    set_agent_message
)

from backend.services.log_service import (
    log_info
)

from backend.database.repositories.cve_scan_job_repository import (
    create_cve_scan_job
)

from backend.services.nmap_service import (
    queue_automatic_nmap_scan
)

from backend.workers.cve_scan_worker import (
    run_cve_scan_worker
)

from backend.workers.nmap_scan_worker import (
    run_nmap_scan_worker
)

HOST = "0.0.0.0"
PORT = 9000

HEARTBEAT_TIMEOUT = 40
CLIENT_STATUS_CHECK_INTERVAL = 5
SCRIPT_CHECK_INTERVAL = 2


def send_json(client_socket, data, send_lock):
    message = json.dumps(data) + "\n"

    with send_lock:
        client_socket.sendall(
            message.encode("utf-8")
        )


def prepare_database_value(value):
    if isinstance(value, (dict, list)):
        return json.dumps(
            value,
            ensure_ascii=False
        )

    return value


def register_client(register_data):
    agent_id = register_data["agent_id"]
    hostname = register_data["hostname"]
    ip_address = register_data["ip_address"]

    agent_version = register_data.get(
        "agent_version",
        "1.0.0"
    )

    ipv6_address = register_data.get(
        "ipv6_address"
    )

    mac_address = register_data.get(
        "mac_address"
    )

    domain_name = register_data.get(
        "domain_name"
    )

    default_gateway = register_data.get(
        "default_gateway"
    )

    dns_servers = register_data.get(
        "dns_servers"
    )

    windows_version = register_data.get(
        "windows_version"
    )

    build_number = register_data.get(
        "build_number"
    )

    architecture = register_data.get(
        "architecture"
    )

    logged_in_user = register_data.get(
        "logged_in_user"
    )

    uptime = register_data.get(
        "uptime"
    )

    cpu_name = register_data.get(
        "cpu_name"
    )

    cpu_core_count = register_data.get(
        "cpu_core_count"
    )

    logical_processor_count = register_data.get(
        "logical_processor_count"
    )

    cpu_usage = register_data.get(
        "cpu_usage"
    )

    ram_usage_percent = register_data.get(
        "ram_usage_percent"
    )

    disk_usage_percent = register_data.get(
        "disk_usage_percent"
    )

    tcp_connection_count = register_data.get(
        "tcp_connection_count"
    )

    udp_endpoint_count = register_data.get(
        "udp_endpoint_count"
    )

    listening_port_count = register_data.get(
        "listening_port_count"
    )

    virtualization = register_data.get(
        "virtualization"
    )

    python_version = register_data.get(
        "python_version"
    )

    ipv6_address = prepare_database_value(
        ipv6_address
    )
    mac_address = prepare_database_value(
        mac_address
    )
    domain_name = prepare_database_value(
        domain_name
    )
    default_gateway = prepare_database_value(
        default_gateway
    )
    dns_servers = prepare_database_value(
        dns_servers
    )
    windows_version = prepare_database_value(
        windows_version
    )
    build_number = prepare_database_value(
        build_number
    )
    architecture = prepare_database_value(
        architecture
    )
    logged_in_user = prepare_database_value(
        logged_in_user
    )
    uptime = prepare_database_value(
        uptime
    )
    cpu_name = prepare_database_value(
        cpu_name
    )
    virtualization = prepare_database_value(
        virtualization
    )
    python_version = prepare_database_value(
        python_version
    )

    existing_client = get_client_by_uuid(
        agent_id
    )

    if existing_client:
        client_id = existing_client["id"]

        update_client(
            client_id=client_id,
            hostname=hostname,
            ip_address=ip_address,
            agent_version=agent_version,
            ipv6_address=ipv6_address,
            mac_address=mac_address,
            domain_name=domain_name,
            default_gateway=default_gateway,
            dns_servers=dns_servers,
            windows_version=windows_version,
            build_number=build_number,
            architecture=architecture,
            logged_in_user=logged_in_user,
            uptime=uptime,
            cpu_name=cpu_name,
            cpu_core_count=cpu_core_count,
            logical_processor_count=(
                logical_processor_count
            ),
            cpu_usage=cpu_usage,
            ram_usage_percent=ram_usage_percent,
            disk_usage_percent=disk_usage_percent,
            tcp_connection_count=(
                tcp_connection_count
            ),
            udp_endpoint_count=(
                udp_endpoint_count
            ),
            listening_port_count=(
                listening_port_count
            ),
            virtualization=virtualization,
            python_version=python_version
        )

        return client_id

    client_id = create_client(
        uuid=agent_id,
        hostname=hostname,
        ip_address=ip_address,
        agent_version=agent_version,
        ipv6_address=ipv6_address,
        mac_address=mac_address,
        domain_name=domain_name,
        default_gateway=default_gateway,
        dns_servers=dns_servers,
        windows_version=windows_version,
        build_number=build_number,
        architecture=architecture,
        logged_in_user=logged_in_user,
        uptime=uptime,
        cpu_name=cpu_name,
        cpu_core_count=cpu_core_count,
        logical_processor_count=(
            logical_processor_count
        ),
        cpu_usage=cpu_usage,
        ram_usage_percent=ram_usage_percent,
        disk_usage_percent=disk_usage_percent,
        tcp_connection_count=(
            tcp_connection_count
        ),
        udp_endpoint_count=(
            udp_endpoint_count
        ),
        listening_port_count=(
            listening_port_count
        ),
        virtualization=virtualization,
        python_version=python_version
    )

    return client_id


def process_script_result(received_data):
    execution_id = received_data.get(
        "execution_id"
    )

    if not execution_id:
        print(
            "Script sonucunda execution_id bulunamadı."
        )
        return

    status = received_data.get(
        "status",
        "failed"
    )

    exit_code = received_data.get(
        "exit_code"
    )

    stdout = received_data.get(
        "stdout",
        ""
    )

    stderr = received_data.get(
        "stderr",
        ""
    )

    duration_ms = received_data.get(
        "duration_ms"
    )

    executed_by = received_data.get(
        "executed_by"
    )

    if status == "completed":
        execution_completed(
            execution_id=execution_id,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_ms=duration_ms,
            executed_by=executed_by
        )

        print(
            f"Script tamamlandı. ID: {execution_id}"
        )

    else:
        execution_failed(
            execution_id=execution_id,
            error_message=(
                stderr
                or "Script çalıştırılamadı."
            ),
            stdout=stdout,
            exit_code=(
                exit_code
                if exit_code is not None
                else -1
            ),
            duration_ms=duration_ms,
            executed_by=executed_by
        )

        print(
            f"Script başarısız. ID: {execution_id}"
        )


def dispatch_pending_scripts(
    client_socket,
    client_id,
    send_lock
):
    pending_executions = (
        get_pending_executions_by_client(
            client_id
        )
    )

    for execution in pending_executions:
        execution_id = execution["id"]

        claimed = claim_pending_execution(
            execution_id
        )

        if not claimed:
            continue

        try:
            script_data = {
                "type": "script_execute",
                "execution_id": execution_id,
                "script_content": execution[
                    "script_content"
                ],
                "timeout_seconds": execution.get(
                    "timeout_seconds",
                    300
                ),
                "execution_type": execution.get(
                    "execution_type",
                    "script"
                )
            }

            send_json(
                client_socket,
                script_data,
                send_lock
            )

            set_agent_message(
                execution_id,
                "Script Agent'a gönderildi."
            )

            print(
                "Script Agent'a gönderildi. "
                f"Execution ID: {execution_id}"
            )

        except Exception as error:
            execution_failed(
                execution_id=execution_id,
                error_message=(
                    "Script Agent'a gönderilemedi: "
                    f"{error}"
                )
            )

            print(
                "Script gönderme hatası: "
                f"{error}"
            )


def handle_client(
    client_socket,
    client_address
):
    client_id = None
    hostname = None

    buffer = ""
    send_lock = threading.Lock()

    last_message_time = time.time()
    last_script_check = 0

    try:
        print(
            f"Agent bağlandı: {client_address}"
        )

        # İlk kayıt mesajı için daha uzun süre bekle
        client_socket.settimeout(30)

        while "\n" not in buffer:
            data = client_socket.recv(4096)

            if not data:
                raise ConnectionError(
                    "Agent kayıt mesajı gelmeden "
                    "bağlantıyı kapattı."
                )

            buffer += data.decode(
                "utf-8",
                errors="replace"
            )

        message, buffer = buffer.split(
            "\n",
            1
        )

        register_data = json.loads(
            message
        )

        if register_data.get("type") != "register":
            raise ValueError(
                "İlk mesajın türü register olmalıdır."
            )

        hostname = register_data["hostname"]

        client_id = register_client(
            register_data
        )

        # Normal mesaj döngüsünde kısa timeout kullanılabilir
        client_socket.settimeout(2)

        print(
            f"Agent kaydedildi: {hostname}"
        )

        log_info(
            event_type="CLIENT_CONNECTED",
            message=f"{hostname} bağlandı.",
            client_id=client_id,
            ip_address=client_address[0]
        )

        print(
            f"Client ID: {client_id}"
        )

        while True:
            try:
                data = client_socket.recv(4096)

                if not data:
                    print(
                        "Agent bağlantıyı kapattı."
                    )
                    break

                buffer += data.decode(
                    "utf-8",
                    errors="replace"
                )

                while "\n" in buffer:
                    message, buffer = buffer.split(
                        "\n",
                        1
                    )

                    if not message.strip():
                        continue

                    received_data = json.loads(
                        message
                    )

                    message_type = received_data.get(
                        "type"
                    )

                    last_message_time = time.time()

                    if message_type == "heartbeat":
                        update_client_system_info(
                            client_id=client_id,
                            system_info=received_data
                        )

                    elif message_type == "installed_apps":
                        applications = received_data.get(
                            "applications",
                            []
                        )

                        if not isinstance(
                            applications,
                            list
                        ):
                            applications = []

                        saved_count = (
                            replace_client_installed_apps(
                                client_id=client_id,
                                installed_apps=applications
                            )
                        )

                        cve_job_result = (
                            create_cve_scan_job(
                                client_id=client_id,
                                trigger_type="automatic"
                            )
                        )

                        log_info(
                            event_type="INSTALLED_APPS_UPDATED",
                            message=(
                                "Kurulu uygulama listesi "
                                f"güncellendi. Toplam: {saved_count}"
                            ),
                            client_id=client_id,
                            ip_address=client_address[0]
                        )

                        print(
                            "Kurulu uygulamalar kaydedildi. "
                            f"Client ID: {client_id}, "
                            f"Toplam: {saved_count}"
                        )

                        if cve_job_result["created"]:
                            print(
                                "Otomatik CVE taraması "
                                "kuyruğa eklendi. "
                                f"Job ID: "
                                f"{cve_job_result['job_id']}, "
                                f"Client ID: {client_id}"
                            )

                        else:
                            print(
                                "İstemci için zaten bekleyen "
                                "veya çalışan bir CVE taraması var. "
                                f"Job ID: "
                                f"{cve_job_result['job_id']}"
                            )

                    elif message_type == "port_inventory":
                        ports = received_data.get(
                            "ports",
                            []
                        )

                        if not isinstance(
                            ports,
                            list
                        ):
                            ports = []

                        saved_count = (
                            replace_client_port_inventory(
                                client_id=client_id,
                                ports=ports
                            )
                        )

                        log_info(
                            event_type=(
                                "PORT_INVENTORY_UPDATED"
                            ),
                            message=(
                                "Port envanteri güncellendi. "
                                f"Toplam: {saved_count}"
                            ),
                            client_id=client_id,
                            ip_address=(
                                client_address[0]
                            )
                        )

                        print(
                            "Port envanteri kaydedildi. "
                            f"Client ID: {client_id}, "
                            f"Toplam: {saved_count}"
                        )

                        try:
                            nmap_scan_result = (
                                queue_automatic_nmap_scan(
                                    client_id=client_id,
                                    target_ip=(
                                        client_address[0]
                                    )
                                )
                            )

                            if nmap_scan_result["created"]:
                                print(
                                    "Otomatik Nmap taraması "
                                    "kuyruğa eklendi. "
                                    f"Scan ID: "
                                    f"{nmap_scan_result['scan_id']}, "
                                    f"Client ID: {client_id}"
                                )

                        except Exception as error:
                            print(
                                "Otomatik Nmap taraması "
                                "kuyruğa eklenemedi. "
                                f"Client ID: {client_id}, "
                                f"Hata: {error}"
                            )

                    elif message_type == "software_updates":
                        updates = received_data.get(
                            "updates",
                            []
                        )

                        if not isinstance(
                            updates,
                            list
                        ):
                            updates = []

                        saved_count = (
                            replace_client_software_updates(
                                client_id=client_id,
                                updates=updates
                            )
                        )

                        log_info(
                            event_type="SOFTWARE_UPDATES_UPDATED",
                            message=(
                                "Yazılım güncelleme bilgileri "
                                f"güncellendi. Toplam: {saved_count}"
                            ),
                            client_id=client_id,
                            ip_address=client_address[0]
                        )

                        print(
                            "Yazılım güncelleme bilgileri kaydedildi. "
                            f"Client ID: {client_id}, "
                            f"Toplam: {saved_count}"
                        )

                    elif message_type == "running_apps":
                        applications = received_data.get(
                            "applications",
                            []
                        )

                        if not isinstance(
                            applications,
                            list
                        ):
                            applications = []

                        saved_count = (
                            replace_client_running_apps(
                                client_id=client_id,
                                running_apps=applications
                            )
                        )

                        log_info(
                            event_type="RUNNING_APPS_UPDATED",
                            message=(
                                "Çalışan uygulama listesi "
                                f"güncellendi. Toplam: {saved_count}"
                            ),
                            client_id=client_id,
                            ip_address=client_address[0]
                        )

                        print(
                            "Çalışan uygulamalar kaydedildi. "
                            f"Client ID: {client_id}, "
                            f"Toplam: {saved_count}"
                        )

                    elif message_type == "script_started":
                        execution_id = (
                            received_data.get(
                                "execution_id"
                            )
                        )

                        if execution_id:
                            execution_started(
                                execution_id
                            )

                            set_agent_message(
                                execution_id,
                                (
                                    "Script Agent "
                                    "tarafından çalıştırılıyor."
                                )
                            )

                            print(
                                "Script başladı. "
                                f"Execution ID: "
                                f"{execution_id}"
                            )

                    elif message_type == "script_result":
                        process_script_result(
                            received_data
                        )

                    else:
                        print(
                            "Bilinmeyen mesaj türü: "
                            f"{message_type}"
                        )

            except socket.timeout:
                pass

            current_time = time.time()

            if (
                current_time - last_message_time
                > HEARTBEAT_TIMEOUT
            ):
                print(
                    "Heartbeat zaman aşımı: "
                    f"{hostname}"
                )
                break

            if (
                current_time - last_script_check
                >= SCRIPT_CHECK_INTERVAL
            ):
                dispatch_pending_scripts(
                    client_socket=client_socket,
                    client_id=client_id,
                    send_lock=send_lock
                )

                last_script_check = current_time

    except json.JSONDecodeError as error:
        print(
            "Geçersiz JSON mesajı: "
            f"{error}"
        )

    except Exception as error:
        traceback.print_exc()

        print(
            "Agent bağlantı hatası: "
            f"{error}"
        )

    finally:
        if client_id:
            try:
                update_client_status(
                    client_id,
                    "offline"
                )

                log_info(
                    event_type="CLIENT_DISCONNECTED",
                    message=f"{hostname} bağlantıyı kapattı.",
                    client_id=client_id,
                    ip_address=client_address[0]
                )

            except Exception as error:
                print(
                    "Client offline yapılamadı: "
                    f"{error}"
                )

        try:
            client_socket.close()

        except Exception:
            pass

        print(
            "Agent bağlantısı kapandı: "
            f"{hostname or client_address}"
        )


def monitor_stale_clients():
    print(
        "İstemci durum denetleyicisi "
        "başlatıldı."
    )

    while True:
        try:
            offline_count = (
                mark_stale_clients_offline(
                    timeout_seconds=(
                        HEARTBEAT_TIMEOUT
                    )
                )
            )

            if offline_count:
                print(
                    f"{offline_count} istemci "
                    "heartbeat zaman aşımı nedeniyle "
                    "çevrimdışı yapıldı."
                )

        except Exception as error:
            traceback.print_exc()

            print(
                "İstemci durum kontrolünde hata: "
                f"{error}"
            )

        time.sleep(
            CLIENT_STATUS_CHECK_INTERVAL
        )


def start_background_workers():
    offline_count = (
        mark_all_clients_offline()
    )

    print(
        "Socket Server başlangıcında eski "
        "istemci durumları temizlendi. "
        f"Çevrimdışı yapılan: {offline_count}"
    )

    status_monitor_thread = threading.Thread(
        target=monitor_stale_clients,
        name="client-status-monitor",
        daemon=True
    )

    status_monitor_thread.start()

    cve_worker_thread = threading.Thread(
        target=run_cve_scan_worker,
        name="cve-scan-worker",
        daemon=True
    )

    cve_worker_thread.start()

    nmap_worker_thread = threading.Thread(
        target=run_nmap_scan_worker,
        name="nmap-scan-worker",
        daemon=True
    )

    nmap_worker_thread.start()

    print(
        "Arka plan servisleri başlatıldı."
    )


def start_server():
    server_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    server_socket.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    server_socket.bind(
        (
            HOST,
            PORT
        )
    )

    server_socket.listen()

    print(
        f"Socket Server çalışıyor: "
        f"{HOST}:{PORT}"
    )

    try:
        while True:
            client_socket, client_address = (
                server_socket.accept()
            )

            client_thread = threading.Thread(
                target=handle_client,
                args=(
                    client_socket,
                    client_address
                ),
                daemon=True
            )

            client_thread.start()

    except KeyboardInterrupt:
        print(
            "\nSocket Server kapatılıyor."
        )

    finally:
        server_socket.close()


if __name__ == "__main__":
    start_background_workers()
    start_server()