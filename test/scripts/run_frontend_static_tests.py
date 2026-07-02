from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "test" / "results"
FRONTEND_SRC = ROOT / "slideon-frontend" / "src"
API_CONFIG = FRONTEND_SRC / "config" / "api.js"
APP_VUE = FRONTEND_SRC / "App.vue"
ROUTER = FRONTEND_SRC / "router" / "index.js"
API_SERVICE = FRONTEND_SRC / "services" / "api.js"
APP_HEADER = FRONTEND_SRC / "components" / "common" / "AppHeader.vue"

FIELDS = ["case", "source_file", "status", "detail"]


def normalize_route(path: str) -> str:
    return re.sub(r":\w+", "{param}", path)


def strip_line_comments(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.strip().startswith("//"))


def extract_router_paths(text: str) -> set[str]:
    return set(re.findall(r"path\s*:\s*['\"]([^'\"]+)['\"]", text))


def extract_dynamic_imports(text: str) -> list[str]:
    return re.findall(r"import\(['\"]\.\./views/([^'\"]+\.vue)['\"]\)", text)


def extract_api_endpoint_groups(text: str) -> set[str]:
    cleaned = strip_line_comments(text)
    return set(re.findall(r"^ {2}([A-Za-z]\w*)\s*:", cleaned, flags=re.MULTILINE))


def extract_upload_types(text: str) -> set[str]:
    match = re.search(r"allowedTypes\s*:\s*\[([^\]]+)\]", text)
    if not match:
        return set()
    return set(re.findall(r"['\"](\.[A-Za-z0-9]+)['\"]", match.group(1)))


def extract_file_accept_types(text: str) -> set[str]:
    match = re.search(r'accept="([^"]+)"', text)
    if not match:
        return set()
    return {item.strip() for item in match.group(1).split(",") if item.strip()}


def row(case: str, source: Path, passed: bool, detail: str) -> dict[str, str]:
    return {
        "case": case,
        "source_file": str(source.relative_to(ROOT)),
        "status": "passed" if passed else "failed",
        "detail": detail,
    }


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run frontend static tests.")
    parser.add_argument("--result-prefix", default="frontend_static_test")
    args = parser.parse_args()

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    api_text = API_CONFIG.read_text(encoding="utf-8", errors="replace")
    app_text = APP_VUE.read_text(encoding="utf-8", errors="replace")
    router_text = ROUTER.read_text(encoding="utf-8", errors="replace")
    service_text = API_SERVICE.read_text(encoding="utf-8", errors="replace")
    header_text = APP_HEADER.read_text(encoding="utf-8", errors="replace")

    rows: list[dict[str, str]] = []

    router_paths = extract_router_paths(router_text)
    expected_routes = {
        "/",
        "/login",
        "/register",
        "/editor",
        "/editor/:id",
        "/outline-editor",
        "/dashboard",
        "/profile",
        "/knowledge-base",
        "/batch-eval",
    }
    missing_routes = sorted(expected_routes - router_paths)
    rows.append(row(
        "router_declares_required_pages",
        ROUTER,
        not missing_routes,
        "missing=" + ",".join(missing_routes) if missing_routes else f"routes={len(router_paths)}",
    ))

    missing_views = [
        view for view in extract_dynamic_imports(router_text)
        if not (FRONTEND_SRC / "views" / view).exists()
    ]
    rows.append(row(
        "router_dynamic_views_exist",
        ROUTER,
        not missing_views,
        "missing=" + ",".join(missing_views) if missing_views else "all dynamic views exist",
    ))

    groups = extract_api_endpoint_groups(api_text)
    required_groups = {"health", "themes", "dsl", "renderTree", "outlines", "auth", "presentations", "rag", "dslFromDocument", "eval"}
    missing_groups = sorted(required_groups - groups)
    rows.append(row(
        "api_endpoint_groups_declared",
        API_CONFIG,
        not missing_groups,
        "missing=" + ",".join(missing_groups) if missing_groups else f"groups={len(groups)}",
    ))

    service_groups = set(re.findall(r"API_ENDPOINTS\.([A-Za-z]\w*)", service_text))
    missing_service_groups = sorted(service_groups - groups)
    rows.append(row(
        "api_service_references_declared_groups",
        API_SERVICE,
        not missing_service_groups,
        "missing=" + ",".join(missing_service_groups) if missing_service_groups else f"referenced={len(service_groups)}",
    ))

    config_upload_types = extract_upload_types(api_text)
    file_accept_types = extract_file_accept_types(app_text)
    upload_mismatch = sorted(config_upload_types ^ file_accept_types)
    rows.append(row(
        "document_upload_accept_matches_config",
        APP_VUE,
        not upload_mismatch,
        "mismatch=" + ",".join(upload_mismatch) if upload_mismatch else ",".join(sorted(config_upload_types)),
    ))

    nav_paths = set(re.findall(r"path\s*:\s*['\"]([^'\"]+)['\"]", header_text))
    missing_nav_routes = sorted(nav_paths - router_paths)
    rows.append(row(
        "header_navigation_targets_router_paths",
        APP_HEADER,
        not missing_nav_routes,
        "missing=" + ",".join(missing_nav_routes) if missing_nav_routes else f"nav={len(nav_paths)}",
    ))

    csv_path = RESULT_DIR / f"{args.result_prefix}_results.csv"
    summary_path = RESULT_DIR / f"{args.result_prefix}_summary.json"
    write_csv(csv_path, rows)

    failed = [item for item in rows if item["status"] != "passed"]
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "success": not failed,
        "tests": len(rows),
        "failures": len(failed),
        "failed_cases": failed,
        "outputs": {
            "frontend_static_results_csv": str(csv_path.relative_to(ROOT)),
        },
        "requirements_traceability": {
            "3.0": "frontend routes and view modules are statically verified",
            "3.3": "frontend service references are checked against API endpoint configuration",
            "4.2": "document upload accept list is checked against frontend upload configuration",
        },
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "success": summary["success"],
        "tests": summary["tests"],
        "failures": summary["failures"],
        "summary": str(summary_path.relative_to(ROOT)),
    }, ensure_ascii=False, indent=2))
    return 0 if summary["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
