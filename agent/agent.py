import ctypes
import datetime
import getpass
import ipaddress
import json
import os
from pathlib import Path
import platform
import socket
import subprocess
import sys
import threading
import time
import traceback
import uuid
import psutil

MAX_SCRIPT_OUTPUT = 100_000


def is_running_as_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def get_application_directory():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent

    return Path(__file__).parent


def load_config():
    config_path = get_application_directory() / "config.json"

    if not config_path.exists():
        raise FileNotFoundError(f"config.json bulunamadı: {config_path}")

    with open(config_path, "r", encoding="utf-8") as file:
        return json.load(file)


CONFIG = load_config()

HOST = CONFIG["server_host"]
PORT = CONFIG["server_port"]

HEARTBEAT_INTERVAL = CONFIG.get("heartbeat_interval", 10)

RECONNECT_INTERVAL = CONFIG.get("reconnect_interval", 5)

AGENT_VERSION = CONFIG.get("agent_version", "1.1.0")

PORT_INVENTORY_INTERVAL = max(
    int(
        CONFIG.get(
            "port_inventory_interval",
            60
        )
    ),
    30
)

STATIC_SYSTEM_INFO = None


def send_json(client_socket, data, send_lock=None):
    message = json.dumps(data) + "\n"

    if send_lock:
        with send_lock:
            client_socket.sendall(message.encode("utf-8"))
    else:
        client_socket.sendall(message.encode("utf-8"))


def get_or_create_agent_id():
    agent_directory = Path.home() / ".remote_vm_agent"

    agent_id_file = agent_directory / "agent_id.txt"

    agent_directory.mkdir(parents=True, exist_ok=True)

    if agent_id_file.exists():
        return agent_id_file.read_text(encoding="utf-8").strip()

    agent_id = str(uuid.uuid4())

    agent_id_file.write_text(agent_id, encoding="utf-8")

    return agent_id


def bytes_to_gb(byte_value):
    return round(byte_value / (1024**3), 2)


def get_cpu_name():
    return platform.processor() or "Bilinmiyor"


def get_port_inventory():
    port_inventory = []
    seen_ports = set()
    process_name_cache = {}

    try:
        connections = psutil.net_connections(kind="inet")

        for connection in connections:
            protocol = "TCP" if connection.type == socket.SOCK_STREAM else "UDP"

            if protocol == "TCP" and connection.status != psutil.CONN_LISTEN:
                continue

            state = connection.status if protocol == "TCP" else "NONE"

            if not connection.laddr:
                continue

            local_address = connection.laddr.ip
            local_port = connection.laddr.port
            pid = connection.pid

            process_name = None
            if pid:
                if pid in process_name_cache:
                    process_name = process_name_cache[pid]
                else:
                    try:
                        process_name = psutil.Process(pid).name()
                    except (
                        psutil.NoSuchProcess,
                        psutil.AccessDenied,
                        psutil.ZombieProcess
                    ):
                        process_name = None

                    process_name_cache[pid] = process_name

            inventory_key = (
                protocol,
                str(local_address),
                local_port,
                pid
            )

            if inventory_key in seen_ports:
                continue

            seen_ports.add(inventory_key)

            port_inventory.append(
                {
                    "protocol": protocol,
                    "local_address": str(local_address),
                    "local_port": local_port,
                    "state": state,
                    "pid": pid,
                    "process_name": process_name
                }
            )

    except Exception as error:
        print(f"Port envanteri alınamadı: {error}")

    port_inventory.sort(
        key=lambda item: (
            0 if item["protocol"] == "TCP" else 1,
            item["local_port"],
            item["local_address"],
            item["pid"] or 0
        )
    )

    return port_inventory


def send_port_inventory(
    client_socket,
    send_lock
):
    ports = get_port_inventory()

    send_json(
        client_socket,
        {
            "type": "port_inventory",
            "ports": ports
        },
        send_lock
    )

    print(
        "Port envanteri gönderildi. "
        f"Toplam: {len(ports)}"
    )


def send_port_inventory_periodically(
    client_socket,
    send_lock
):
    while True:
        time.sleep(
            PORT_INVENTORY_INTERVAL
        )

        try:
            send_port_inventory(
                client_socket,
                send_lock
            )

        except (
            OSError,
            ConnectionError
        ):
            break

        except Exception as error:
            print(
                "Periyodik port envanteri "
                "gönderilemedi: "
                f"{error}"
            )


def run_powershell_json(script):
    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                script,
            ],
            capture_output=True,
            text=True,
            timeout=15,
            errors="replace",
        )

        if result.returncode != 0:
            return {}

        output = result.stdout.strip()

        if not output:
            return {}

        return json.loads(output)

    except Exception as error:
        print(f"Sistem bilgisi alınamadı: {error}")
        return {}


def get_static_system_info():
    global STATIC_SYSTEM_INFO

    if STATIC_SYSTEM_INFO is not None:
        return STATIC_SYSTEM_INFO

    powershell_script = r"""
        $computer = Get-CimInstance Win32_ComputerSystem

        $ipv6 = Get-NetIPAddress -AddressFamily IPv6 |
            Where-Object {
                $_.IPAddress -ne "::1" -and
                $_.IPAddress -notlike "fe80:*"
            } |
            Select-Object -First 1 -ExpandProperty IPAddress

        $adapter = Get-NetAdapter |
            Where-Object Status -eq "Up" |
            Select-Object -First 1

        $gateway = Get-NetRoute -DestinationPrefix "0.0.0.0/0" |
            Sort-Object RouteMetric |
            Select-Object -First 1 -ExpandProperty NextHop

        $dns = Get-DnsClientServerAddress -AddressFamily IPv4 |
            Where-Object {
                $_.ServerAddresses.Count -gt 0
            } |
            ForEach-Object {
                $_.ServerAddresses
            } |
            Select-Object -Unique

        $manufacturer = $computer.Manufacturer
        $model = $computer.Model

        $virtualization = "Fiziksel"

        if (
            $manufacturer -match "VMware" -or
            $model -match "VMware"
        ) {
            $virtualization = "VMware"
        }
        elseif (
            $manufacturer -match "VirtualBox" -or
            $model -match "VirtualBox"
        ) {
            $virtualization = "VirtualBox"
        }
        elseif (
            $manufacturer -match "Microsoft Corporation" -and
            $model -match "Virtual"
        ) {
            $virtualization = "Hyper-V"
        }

        [PSCustomObject]@{
            ipv6_address = $ipv6
            mac_address = $adapter.MacAddress
            domain_name = $computer.Domain
            default_gateway = $gateway
            dns_servers = ($dns -join ", ")
            virtualization = $virtualization
        } | ConvertTo-Json -Compress
    """

    powershell_info = run_powershell_json(powershell_script)

    STATIC_SYSTEM_INFO = {
        "ipv6_address": powershell_info.get("ipv6_address"),
        "mac_address": powershell_info.get("mac_address"),
        "domain_name": powershell_info.get("domain_name"),
        "default_gateway": powershell_info.get("default_gateway"),
        "dns_servers": powershell_info.get("dns_servers"),
        "virtualization": powershell_info.get("virtualization", "Bilinmiyor"),
    }

    return STATIC_SYSTEM_INFO


def get_installed_applications():
    powershell_script = r"""
        $registryPaths = @(
            "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*",
            "HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*",
            "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*"
        )

        $applications = foreach ($path in $registryPaths) {
            Get-ItemProperty $path -ErrorAction SilentlyContinue |
                Where-Object {
                    $_.DisplayName -and
                    $_.SystemComponent -ne 1
                } |
                Select-Object @{
                    Name = "app_name"
                    Expression = { $_.DisplayName }
                }, @{
                    Name = "app_version"
                    Expression = { $_.DisplayVersion }
                }, @{
                    Name = "publisher"
                    Expression = { $_.Publisher }
                }, @{
                    Name = "install_date"
                    Expression = { $_.InstallDate }
                }
        }

        $applications |
            Sort-Object app_name -Unique |
            ConvertTo-Json -Compress
    """

    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                powershell_script,
            ],
            capture_output=True,
            text=True,
            timeout=60,
            errors="replace",
        )

        if result.returncode != 0:
            print(f"Kurulu uygulamalar alınamadı: {result.stderr}")
            return []

        output = result.stdout.strip()

        if not output:
            return []

        installed_apps = json.loads(output)

        if isinstance(installed_apps, dict):
            installed_apps = [installed_apps]

        if not isinstance(installed_apps, list):
            return []

        return installed_apps

    except Exception as error:
        print(f"Kurulu uygulamalar alınamadı: {error}")
        return []


def get_available_software_updates():
    try:
        result = subprocess.run(
            [
                "winget",
                "list",
                "--upgrade-available",
                "--source",
                "winget",
                "--accept-source-agreements",
                "--disable-interactivity",
            ],
            capture_output=True,
            text=True,
            timeout=120,
            errors="replace",
        )

        if result.returncode != 0:
            print(f"WinGet sürüm kontrolü başarısız: {result.stderr}")
            return []

        lines = result.stdout.splitlines()
        header_index = None

        for index, line in enumerate(lines):
            if (
                "Name" in line
                and "Id" in line
                and "Version" in line
                and "Available" in line
            ):
                header_index = index
                break

        if header_index is None:
            print("WinGet çıktısında tablo başlığı bulunamadı.")
            return []

        header = lines[header_index]

        id_position = header.index("Id")
        version_position = header.index("Version")
        available_position = header.index("Available")

        updates = []

        for line in lines[header_index + 1 :]:
            stripped_line = line.strip()

            if not stripped_line:
                continue

            if set(stripped_line) == {"-"}:
                continue

            if (
                "upgrade available" in stripped_line.lower()
                or "upgrades available" in stripped_line.lower()
            ):
                break

            package_name = line[:id_position].strip()
            package_id = line[id_position:version_position].strip()
            installed_version = line[version_position:available_position].strip()
            available_version = line[available_position:].strip()

            if (
                not package_name
                or not package_id
                or not installed_version
                or not available_version
            ):
                continue

            updates.append(
                {
                    "package_name": package_name,
                    "package_id": package_id,
                    "installed_version": installed_version,
                    "available_version": available_version,
                    "source": "winget",
                }
            )

        return updates

    except FileNotFoundError:
        print("WinGet bu bilgisayarda bulunamadı.")
        return []

    except subprocess.TimeoutExpired:
        print("WinGet sürüm kontrolü zaman aşımına uğradı.")
        return []

    except Exception as error:
        print(f"WinGet sürüm kontrolü sırasında hata: {error}")
        return []


def get_running_applications():
    powershell_script = r"""
        Get-Process |
            Where-Object {
                $_.MainWindowTitle -and
                $_.MainWindowTitle.Trim() -ne ""
            } |
            Select-Object @{
                Name = "process_id"
                Expression = { $_.Id }
            }, @{
                Name = "app_name"
                Expression = { $_.MainWindowTitle }
            } |
            ConvertTo-Json -Compress
    """

    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                powershell_script,
            ],
            capture_output=True,
            text=True,
            timeout=20,
            errors="replace",
        )

        if result.returncode != 0:
            print(f"Çalışan uygulamalar alınamadı: {result.stderr}")
            return []

        output = result.stdout.strip()

        if not output:
            return []

        window_apps = json.loads(output)

        if isinstance(window_apps, dict):
            window_apps = [window_apps]

        if not isinstance(window_apps, list):
            return []

        window_map = {}

        for app in window_apps:
            try:
                process_id = int(app.get("process_id"))
            except (TypeError, ValueError):
                continue

            app_name = str(app.get("app_name") or "").strip()

            if not app_name:
                continue

            window_map[process_id] = app_name

        running_apps = []

        for process in psutil.process_iter(
            ["pid", "name", "username", "memory_info"]
        ):
            try:
                process_info = process.info
                process_id = process_info.get("pid")

                if process_id not in window_map:
                    continue

                memory_info = process_info.get("memory_info")
                memory_mb = 0.0

                if memory_info:
                    memory_mb = round(memory_info.rss / (1024 * 1024), 2)

                running_apps.append(
                    {
                        "app_name": window_map[process_id],
                        "process_name": process_info.get("name"),
                        "process_id": process_id,
                        "username": process_info.get("username"),
                        "memory_mb": memory_mb,
                    }
                )

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
                psutil.ZombieProcess,
            ):
                continue

        running_apps.sort(
            key=lambda app: (app.get("memory_mb") or 0), reverse=True
        )

        return running_apps

    except subprocess.TimeoutExpired:
        print("Çalışan uygulamalar alınırken zaman aşımı oluştu.")
        return []

    except Exception as error:
        print(f"Çalışan uygulamalar alınamadı: {error}")
        return []


def get_system_info():
    memory_info = psutil.virtual_memory()
    system_drive = Path.home().anchor or "/"
    disk_info = psutil.disk_usage(system_drive)
    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
    uptime = str(datetime.datetime.now() - boot_time).split(".")[0]

    tcp_count = 0
    udp_count = 0
    listening_port_count = 0

    try:
        connections = psutil.net_connections(kind="inet")

        for connection in connections:
            if connection.type == socket.SOCK_STREAM:
                tcp_count += 1

                if connection.status == psutil.CONN_LISTEN:
                    listening_port_count += 1

            elif connection.type == socket.SOCK_DGRAM:
                udp_count += 1

    except Exception as error:
        print(f"Ağ bağlantıları alınamadı: {error}")

    static_info = get_static_system_info()

    return {
        **static_info,
        "cpu_name": get_cpu_name(),
        "cpu_usage": psutil.cpu_percent(interval=1),
        "cpu_core_count": psutil.cpu_count(logical=False),
        "logical_processor_count": psutil.cpu_count(logical=True),
        "ram_total": bytes_to_gb(memory_info.total),
        "ram_used": bytes_to_gb(memory_info.used),
        "ram_usage_percent": memory_info.percent,
        "disk_total": bytes_to_gb(disk_info.total),
        "disk_used": bytes_to_gb(disk_info.used),
        "disk_usage_percent": disk_info.percent,
        "windows_version": platform.platform(),
        "build_number": platform.version(),
        "architecture": platform.machine(),
        "logged_in_user": getpass.getuser(),
        "python_version": platform.python_version(),
        "uptime": uptime,
        "tcp_connection_count": tcp_count,
        "udp_endpoint_count": udp_count,
        "listening_port_count": listening_port_count,
        "agent_version": AGENT_VERSION,
    }


def send_heartbeat(client_socket, send_lock=None):
    try:
        while True:
            system_info = get_system_info()
            heartbeat_data = {"type": "heartbeat", **system_info}
            send_json(client_socket, heartbeat_data, send_lock)
            time.sleep(10)

    except Exception:
        print("Heartbeat Hatası:")
        traceback.print_exc()


def execute_powershell_script(execution_id, script_content, timeout_seconds):
    started_time = time.time()

    if not is_running_as_admin():
        return {
            "type": "script_result",
            "execution_id": execution_id,
            "status": "failed",
            "exit_code": -1,
            "stdout": "",
            "stderr": "Agent yönetici yetkisiyle çalışmadığı için script reddedildi.",
            "duration_ms": 0,
            "executed_by": getpass.getuser(),
        }

    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script_content,
            ],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            errors="replace",
        )

        duration_ms = int((time.time() - started_time) * 1000)
        stdout = result.stdout[:MAX_SCRIPT_OUTPUT]
        stderr = result.stderr[:MAX_SCRIPT_OUTPUT]
        status = "completed" if result.returncode == 0 else "failed"

        return {
            "type": "script_result",
            "execution_id": execution_id,
            "status": status,
            "exit_code": result.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "duration_ms": duration_ms,
            "executed_by": getpass.getuser(),
        }

    except subprocess.TimeoutExpired as error:
        duration_ms = int((time.time() - started_time) * 1000)

        stdout = error.stdout or ""
        stderr = error.stderr or ""

        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")

        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")

        return {
            "type": "script_result",
            "execution_id": execution_id,
            "status": "failed",
            "exit_code": -1,
            "stdout": stdout[:MAX_SCRIPT_OUTPUT],
            "stderr": (stderr or "Script zaman aşımına uğradı.")[
                :MAX_SCRIPT_OUTPUT
            ],
            "duration_ms": duration_ms,
            "executed_by": getpass.getuser(),
        }

    except Exception as error:
        duration_ms = int((time.time() - started_time) * 1000)

        return {
            "type": "script_result",
            "execution_id": execution_id,
            "status": "failed",
            "exit_code": -1,
            "stdout": "",
            "stderr": str(error),
            "duration_ms": duration_ms,
            "executed_by": getpass.getuser(),
        }


def send_refreshed_inventory(client_socket, send_lock):
    installed_apps = get_installed_applications()
    send_json(
        client_socket,
        {"type": "installed_apps", "applications": installed_apps},
        send_lock,
    )
    print(
        f"Kurulu uygulama listesi yenilendi. Toplam: {len(installed_apps)}"
    )

    software_updates = get_available_software_updates()
    send_json(
        client_socket,
        {"type": "software_updates", "updates": software_updates},
        send_lock,
    )
    print(
        f"Yazılım güncelleme bilgileri yenilendi. Toplam: {len(software_updates)}"
    )

    running_apps = get_running_applications()
    send_json(
        client_socket,
        {"type": "running_apps", "applications": running_apps},
        send_lock,
    )
    print(
        f"Çalışan uygulama listesi yenilendi. Toplam: {len(running_apps)}"
    )

    send_port_inventory(
        client_socket,
        send_lock
    )


def start_agent():
    if not is_running_as_admin():
        raise PermissionError("Agent yönetici yetkisiyle çalıştırılmalıdır.")

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    send_lock = threading.Lock()

    print(f"Socket Server'a bağlanılıyor ({HOST}:{PORT})...")
    client_socket.connect((HOST, PORT))
    print("Bağlantı başarılı.")

    agent_id = get_or_create_agent_id()
    system_info = get_system_info()

    register_data = {
        "type": "register",
        "agent_id": agent_id,
        "hostname": socket.gethostname(),
        "ip_address": socket.gethostbyname(socket.gethostname()),
        **system_info,
    }

    send_json(client_socket, register_data, send_lock)

    heartbeat_thread = threading.Thread(
        target=send_heartbeat, args=(client_socket, send_lock), daemon=True
    )
    heartbeat_thread.start()

    port_inventory_thread = (
        threading.Thread(
            target=(
                send_port_inventory_periodically
            ),
            args=(
                client_socket,
                send_lock
            ),
            daemon=True
        )
    )

    port_inventory_thread.start()

    installed_apps = get_installed_applications()
    send_json(
        client_socket,
        {"type": "installed_apps", "applications": installed_apps},
        send_lock,
    )
    print(f"Kurulu uygulama listesi gönderildi. Toplam: {len(installed_apps)}")

    software_updates = get_available_software_updates()
    send_json(
        client_socket,
        {"type": "software_updates", "updates": software_updates},
        send_lock,
    )
    print(
        f"Yazılım güncelleme bilgileri gönderildi. Toplam: {len(software_updates)}"
    )

    running_apps = get_running_applications()
    send_json(
        client_socket,
        {"type": "running_apps", "applications": running_apps},
        send_lock,
    )
    print(f"Çalışan uygulama listesi gönderildi. Toplam: {len(running_apps)}")

    send_port_inventory(
        client_socket,
        send_lock
    )

    buffer = ""

    try:
        while True:
            data = client_socket.recv(4096)

            if not data:
                break

            buffer += data.decode("utf-8")

            while "\n" in buffer:
                message, buffer = buffer.split("\n", 1)

                if not message.strip():
                    continue

                received_data = json.loads(message)
                message_type = received_data.get("type")

                if message_type == "script_execute":
                    execution_id = received_data["execution_id"]
                    script_content = received_data["script_content"]
                    timeout_seconds = received_data.get("timeout_seconds", 300)
                    execution_type = received_data.get(
                        "execution_type", "script"
                    )

                    send_json(
                        client_socket,
                        {
                            "type": "script_started",
                            "execution_id": execution_id,
                        },
                        send_lock,
                    )

                    print(f"Script çalıştırılıyor: {execution_id}")

                    result_data = execute_powershell_script(
                        execution_id, script_content, timeout_seconds
                    )

                    send_json(client_socket, result_data, send_lock)
                    print(f"Script sonucu gönderildi: {execution_id}")

                    if execution_type == "software_update":
                        print(
                            "Yazılım güncellemesi tamamlandı. Envanter yeniden toplanıyor..."
                        )
                        send_refreshed_inventory(client_socket, send_lock)

                else:
                    print(f"Bilinmeyen mesaj: {message_type}")

    except Exception as error:
        print(f"Agent hatası: {error}")

    finally:
        client_socket.close()
        print("Bağlantı kapatıldı.")


def run_agent():
    while True:
        try:
            print("Sunucuya bağlanmayı deniyorum...")
            start_agent()

        except Exception as error:
            print(f"Bağlantı hatası: {error}")
            traceback.print_exc()

        print(f"{RECONNECT_INTERVAL} saniye sonra tekrar denenecek...")
        time.sleep(RECONNECT_INTERVAL)


if __name__ == "__main__":
    run_agent()