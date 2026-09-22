import time
import traceback

from backend.database.repositories.cve_scan_job_repository import (
    claim_next_cve_scan_job,
    complete_cve_scan_job,
    fail_cve_scan_job,
    requeue_interrupted_cve_scan_jobs
)
from backend.services.cve_service import (
    scan_client_cves
)


POLL_INTERVAL_SECONDS = 2


def process_cve_scan_job(
    job
):
    job_id = job["id"]
    client_id = job["client_id"]

    print(
        "CVE taraması başladı. "
        f"Job ID: {job_id}, "
        f"Client ID: {client_id}, "
        f"Tetikleme: {job['trigger_type']}"
    )

    try:
        result = scan_client_cves(
            client_id
        )

        complete_cve_scan_job(
            job_id=job_id,
            scanned_apps=result[
                "scanned_apps"
            ],
            matched_apps=result[
                "matched_apps"
            ],
            findings_count=result[
                "findings"
            ]
        )

        print(
            "CVE taraması tamamlandı. "
            f"Job ID: {job_id}, "
            f"Taranan: "
            f"{result['scanned_apps']}, "
            f"Eşleşen: "
            f"{result['matched_apps']}, "
            f"CVE: {result['findings']}, "
            f"Önbellek: "
            f"{result['cache_hits']}"
        )

    except Exception as error:
        traceback.print_exc()

        fail_cve_scan_job(
            job_id=job_id,
            error_message=str(error)
        )

        print(
            "CVE taraması başarısız oldu. "
            f"Job ID: {job_id}, "
            f"Hata: {error}"
        )


def run_cve_scan_worker():
    requeued_count = (
        requeue_interrupted_cve_scan_jobs()
    )

    if requeued_count:
        print(
            "Yarım kalan CVE işleri yeniden "
            "kuyruğa alındı. "
            f"Toplam: {requeued_count}"
        )

    print(
        "CVE tarama worker'ı başlatıldı."
    )

    while True:
        try:
            job = claim_next_cve_scan_job()

            if job is None:
                time.sleep(
                    POLL_INTERVAL_SECONDS
                )
                continue

            process_cve_scan_job(
                job
            )

        except KeyboardInterrupt:
            print(
                "CVE tarama worker'ı durduruldu."
            )
            break

        except Exception as error:
            traceback.print_exc()

            print(
                "CVE worker döngüsünde hata: "
                f"{error}"
            )

            time.sleep(
                POLL_INTERVAL_SECONDS
            )


if __name__ == "__main__":
    run_cve_scan_worker()