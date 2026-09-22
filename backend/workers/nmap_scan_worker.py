import time
import traceback

from backend.database.repositories.nmap_scan_repository import (
    claim_next_nmap_scan,
    complete_nmap_scan,
    fail_nmap_scan,
    requeue_interrupted_nmap_scans
)
from backend.services.nmap_service import (
    run_agent_port_nmap_scan
)


NMAP_POLL_INTERVAL_SECONDS = 2


def process_nmap_scan(
    scan
):
    scan_id = scan["id"]
    client_id = scan["client_id"]
    target_ip = scan["target_ip"]
    scan_type = scan["scan_type"]

    print(
        "Nmap taraması başladı. "
        f"Scan ID: {scan_id}, "
        f"Client ID: {client_id}, "
        f"Hedef: {target_ip}, "
        f"Tür: {scan_type}"
    )

    try:
        if scan_type == "agent_ports":
            scan_result = (
                run_agent_port_nmap_scan(
                    client_id=client_id,
                    target_ip=target_ip
                )
            )

        else:
            raise ValueError(
                "Desteklenmeyen Nmap "
                f"tarama türü: {scan_type}"
            )

        summary = complete_nmap_scan(
            scan_id=scan_id,
            client_id=client_id,
            results=scan_result[
                "results"
            ]
        )

        print(
            "Nmap taraması tamamlandı. "
            f"Scan ID: {scan_id}, "
            f"Taranan: "
            f"{summary['scanned_port_count']}, "
            f"Açık: "
            f"{summary['open_port_count']}, "
            f"Filtrelenmiş: "
            f"{summary['filtered_port_count']}, "
            f"Kapalı: "
            f"{summary['closed_port_count']}"
        )

    except Exception as error:
        traceback.print_exc()

        fail_nmap_scan(
            scan_id=scan_id,
            error_message=str(error)
        )

        print(
            "Nmap taraması başarısız oldu. "
            f"Scan ID: {scan_id}, "
            f"Hata: {error}"
        )


def run_nmap_scan_worker():
    requeued_count = (
        requeue_interrupted_nmap_scans()
    )

    if requeued_count:
        print(
            "Yarım kalan Nmap taramaları "
            "yeniden kuyruğa alındı. "
            f"Toplam: {requeued_count}"
        )

    print(
        "Nmap tarama worker'ı başlatıldı."
    )

    while True:
        try:
            scan = claim_next_nmap_scan()

            if scan is None:
                time.sleep(
                    NMAP_POLL_INTERVAL_SECONDS
                )
                continue

            process_nmap_scan(
                scan
            )

        except KeyboardInterrupt:
            print(
                "Nmap tarama worker'ı durduruldu."
            )
            break

        except Exception as error:
            traceback.print_exc()

            print(
                "Nmap worker döngüsünde hata: "
                f"{error}"
            )

            time.sleep(
                NMAP_POLL_INTERVAL_SECONDS
            )


if __name__ == "__main__":
    run_nmap_scan_worker()