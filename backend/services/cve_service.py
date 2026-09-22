import hashlib
import json
import os
import time

import requests
from packaging.version import Version, InvalidVersion

from backend.database.repositories.installed_app_repository import (
    get_installed_apps_by_client
)
from backend.database.repositories.cve_repository import (
    replace_client_cve_findings,
    get_cve_findings_by_client,
    count_cve_findings
)
from backend.database.repositories.cve_product_cache_repository import (
    get_valid_cve_product_cache,
    save_cve_product_cache,
    save_cve_product_cache_error
)

NVD_CPE_API_URL = "https://services.nvd.nist.gov/rest/json/cpes/2.0"
NVD_CVE_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

CPE_SEARCH_ALIASES = {
    "microsoft edge": "Microsoft Edge Chromium",
    "google chrome": "Google Chrome",
    "mozilla firefox": "Mozilla Firefox"
}


def get_cpe_search_name(app_name):
    normalized_name = str(app_name or "").strip().lower()
    return CPE_SEARCH_ALIASES.get(normalized_name, app_name)


def get_nvd_headers():
    api_key = os.getenv("NVD_API_KEY", "").strip()
    headers = {"User-Agent": "Remote-VM-Management-System/1.0"}

    if api_key:
        headers["apiKey"] = api_key

    return headers


def search_cpe(app_name, app_version):
    app_name = str(app_name or "").strip()
    app_version = str(app_version or "").strip()

    if not app_name:
        return []

    search_text = app_name
    if app_version:
        search_text = f"{app_name} {app_version}"

    response = requests.get(
        NVD_CPE_API_URL,
        params={"keywordSearch": search_text, "resultsPerPage": 20},
        headers=get_nvd_headers(),
        timeout=30
    )
    response.raise_for_status()

    data = response.json()
    results = []

    for product in data.get("products", []):
        cpe = product.get("cpe", {})
        cpe_name = cpe.get("cpeName")

        if not cpe_name:
            continue

        titles = [
            t.get("title", "") 
            for t in cpe.get("titles", []) 
            if t.get("lang") == "en"
        ]

        results.append({"cpe_name": cpe_name, "titles": titles})

    return results


def select_application_cpe(cpe_results, app_name):
    normalized_app_name = app_name.strip().lower()

    for result in cpe_results:
        cpe_name = result["cpe_name"]
        parts = cpe_name.split(":")

        if len(parts) != 13:
            continue

        product_type = parts[2]
        target_software = parts[10]

        if product_type != "a":
            continue

        if target_software not in ("*", "-", "windows", "windows_10", "windows_11"):
            continue

        titles = result.get("titles", [])
        for title in titles:
            normalized_title = title.strip().lower()
            if normalized_app_name == normalized_title or normalized_app_name in normalized_title:
                return cpe_name

    return None


def build_virtual_match_string(cpe_name):
    parts = cpe_name.split(":")
    if len(parts) != 13:
        raise ValueError("Geçersiz CPE formatı.")

    # cpe:2.3:a:vendor:product formatına indirger
    return ":".join(parts[:5])


def compare_versions(first_version, second_version):
    try:
        first = Version(str(first_version).strip())
        second = Version(str(second_version).strip())

        if first < second:
            return -1
        if first > second:
            return 1
        return 0

    except InvalidVersion:
        first = str(first_version).strip().lower()
        second = str(second_version).strip().lower()

        if first == second:
            return 0
        return -1 if first < second else 1


def version_matches_cpe(installed_version, cpe_match):
    criteria = cpe_match.get("criteria", "")
    parts = criteria.split(":")

    if len(parts) != 13:
        return False

    criteria_version = parts[5]

    if criteria_version not in ("*", "-", ""):
        return compare_versions(installed_version, criteria_version) == 0

    version_start_including = cpe_match.get("versionStartIncluding")
    if version_start_including:
        if compare_versions(installed_version, version_start_including) < 0:
            return False

    version_start_excluding = cpe_match.get("versionStartExcluding")
    if version_start_excluding:
        if compare_versions(installed_version, version_start_excluding) <= 0:
            return False

    version_end_including = cpe_match.get("versionEndIncluding")
    if version_end_including:
        if compare_versions(installed_version, version_end_including) > 0:
            return False

    version_end_excluding = cpe_match.get("versionEndExcluding")
    if version_end_excluding:
        if compare_versions(installed_version, version_end_excluding) >= 0:
            return False

    return True


def node_has_vulnerable_product(node, virtual_match_string, app_version):
    for cpe_match in node.get("cpeMatch", []):
        criteria = cpe_match.get("criteria", "")

        if cpe_match.get("vulnerable") is not True:
            continue

        if not criteria.startswith(virtual_match_string + ":"):
            continue

        if version_matches_cpe(installed_version=app_version, cpe_match=cpe_match):
            return True

    for child in node.get("children", []):
        if node_has_vulnerable_product(child, virtual_match_string, app_version):
            return True

    return False


def cve_has_vulnerable_product(cve_data, virtual_match_string, app_version):
    configurations = cve_data.get("configurations", [])

    for configuration in configurations:
        for node in configuration.get("nodes", []):
            if node_has_vulnerable_product(node, virtual_match_string, app_version):
                return True

    return False


def search_cves_by_product_version(cpe_name, app_version):
    virtual_match_string = build_virtual_match_string(cpe_name)

    response = requests.get(
        NVD_CVE_API_URL,
        params={
            "virtualMatchString": virtual_match_string,
            "versionStart": app_version,
            "versionStartType": "including",
            "versionEnd": app_version,
            "versionEndType": "including"
        },
        headers=get_nvd_headers(),
        timeout=30
    )
    response.raise_for_status()

    data = response.json()
    vulnerabilities = data.get("vulnerabilities", [])

    filtered_vulnerabilities = []
    for item in vulnerabilities:
        cve_data = item.get("cve", {})
        if cve_has_vulnerable_product(cve_data, virtual_match_string, app_version):
            filtered_vulnerabilities.append(item)

    return filtered_vulnerabilities


def parse_cve_results(vulnerabilities, app_name, app_version):
    parsed_findings = []

    for item in vulnerabilities:
        cve_data = item.get("cve", {})
        cve_id = cve_data.get("id")

        if not cve_id:
            continue

        descriptions = cve_data.get("descriptions", [])
        description = next(
            (d.get("value") for d in descriptions if d.get("lang") == "en"),
            "Açıklama bulunamadı."
        )

        metrics = cve_data.get("metrics", {})
        cvss_score = 0.0
        severity = "UNKNOWN"

        cvss_v3_list = metrics.get("cvssMetricV31", []) or metrics.get("cvssMetricV30", [])
        if cvss_v3_list:
            cvss_data = cvss_v3_list[0].get("cvssData", {})
            cvss_score = cvss_data.get("baseScore", 0.0)
            severity = cvss_data.get("baseSeverity", "UNKNOWN")
        elif metrics.get("cvssMetricV2"):
            cvss_v2 = metrics.get("cvssMetricV2", [])[0]
            cvss_data = cvss_v2.get("cvssData", {})
            cvss_score = cvss_data.get("baseScore", 0.0)
            severity = cvss_v2.get("baseSeverity", "UNKNOWN")

        references = cve_data.get("references", [])
        ref_url = (
            references[0].get("url")
            if references
            else f"https://nvd.nist.gov/vuln/detail/{cve_id}"
        )

        parsed_findings.append({
            "app_name": app_name,
            "app_version": app_version,
            "cve_id": cve_id,
            "severity": severity.upper(),
            "cvss_score": float(cvss_score),
            "description": description,
            "reference_url": ref_url
        })

    return parsed_findings


def normalize_cache_product_name(
    app_name
):
    return str(
        app_name or ""
    ).strip().lower()


def generate_cve_cache_key(
    app_name,
    app_version
):
    normalized_name = (
        normalize_cache_product_name(
            app_name
        )
    )

    normalized_version = (
        str(
            app_version or ""
        ).strip().lower()
    )

    raw_key = (
        f"{normalized_name}::{normalized_version}"
    )

    return hashlib.sha256(
        raw_key.encode(
            "utf-8"
        )
    ).hexdigest()


def scan_or_get_cached_application(
    app_name,
    app_version,
    request_delay
):
    normalized_app_name = (
        normalize_cache_product_name(
            app_name
        )
    )

    cache_key = (
        generate_cve_cache_key(
            app_name=app_name,
            app_version=app_version
        )
    )

    cached_entry = (
        get_valid_cve_product_cache(
            cache_key
        )
    )

    if cached_entry:
        findings = []

        if cached_entry.get(
            "findings_json"
        ):
            try:
                findings = (
                    json.loads(
                        cached_entry[
                            "findings_json"
                        ]
                    )
                )
            except Exception:
                findings = []

        return {
            "matched": bool(
                cached_entry.get(
                    "product_matched"
                )
            ),
            "findings": findings,
            "from_cache": True
        }

    try:
        cpe_search_name = (
            get_cpe_search_name(
                app_name
            )
        )

        cpe_results = (
            search_cpe(
                cpe_search_name,
                ""
            )
        )

        time.sleep(
            request_delay
        )

        selected_cpe = (
            select_application_cpe(
                cpe_results,
                cpe_search_name
            )
        )

        if selected_cpe is None:
            save_cve_product_cache(
                cache_key=cache_key,
                app_name=app_name,
                normalized_app_name=(
                    normalized_app_name
                ),
                app_version=app_version,
                cpe_name=None,
                product_matched=False,
                findings_json="[]"
            )

            return {
                "matched": False,
                "findings": [],
                "from_cache": False
            }

        if not app_version:
            save_cve_product_cache(
                cache_key=cache_key,
                app_name=app_name,
                normalized_app_name=(
                    normalized_app_name
                ),
                app_version=app_version,
                cpe_name=selected_cpe,
                product_matched=True,
                findings_json="[]"
            )

            return {
                "matched": True,
                "findings": [],
                "from_cache": False
            }

        vulnerabilities = (
            search_cves_by_product_version(
                cpe_name=selected_cpe,
                app_version=app_version
            )
        )

        time.sleep(
            request_delay
        )

        findings = parse_cve_results(
            vulnerabilities=vulnerabilities,
            app_name=app_name,
            app_version=app_version
        )

        save_cve_product_cache(
            cache_key=cache_key,
            app_name=app_name,
            normalized_app_name=(
                normalized_app_name
            ),
            app_version=app_version,
            cpe_name=selected_cpe,
            product_matched=True,
            findings_json=json.dumps(
                findings,
                ensure_ascii=False
            )
        )

        return {
            "matched": True,
            "findings": findings,
            "from_cache": False
        }

    except Exception as error:
        save_cve_product_cache_error(
            cache_key=cache_key,
            app_name=app_name,
            normalized_app_name=(
                normalized_app_name
            ),
            app_version=app_version,
            error_message=str(error)
        )

        raise


def scan_client_cves(
    client_id
):
    installed_apps = (
        get_installed_apps_by_client(
            client_id
        )
    )

    all_findings = []

    scanned_count = 0
    matched_count = 0
    cache_hit_count = 0

    api_key = os.getenv(
        "NVD_API_KEY",
        ""
    ).strip()

    request_delay = (
        1.0
        if api_key
        else 6.5
    )

    for app in installed_apps:
        app_name = str(
            app.get(
                "app_name"
            )
            or ""
        ).strip()

        app_version = str(
            app.get(
                "app_version"
            )
            or ""
        ).strip()

        if not app_name:
            continue

        scanned_count += 1

        result = (
            scan_or_get_cached_application(
                app_name=app_name,
                app_version=app_version,
                request_delay=request_delay
            )
        )

        if result["matched"]:
            matched_count += 1

        if result["from_cache"]:
            cache_hit_count += 1

        all_findings.extend(
            result["findings"]
        )

    saved_count = (
        replace_client_cve_findings(
            client_id=client_id,
            findings=all_findings
        )
    )

    return {
        "scanned_apps": scanned_count,
        "matched_apps": matched_count,
        "findings": saved_count,
        "cache_hits": cache_hit_count
    }


def list_client_cve_findings(client_id):
    return get_cve_findings_by_client(client_id)


def get_client_cve_count(client_id):
    return count_cve_findings(client_id)