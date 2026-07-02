from __future__ import annotations

import argparse
import ast
import csv
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "test" / "results"
BACKEND_API_DIR = ROOT / "backend" / "ppt_backend" / "api"
FRONTEND_SRC_DIR = ROOT / "slideon-frontend" / "src"
DOC_PARSER = ROOT / "backend" / "ppt_backend" / "services" / "rag" / "document_parser.py"
FRONTEND_API_CONFIG = FRONTEND_SRC_DIR / "config" / "api.js"
API_PREFIXES = (
    "/auth",
    "/dsl",
    "/eval",
    "/health",
    "/llm",
    "/outlines",
    "/presentations",
    "/rag",
    "/render-tree",
    "/themes",
)

BACKEND_FIELDS = ["method", "path", "source_file", "line", "frontend_referenced", "status"]
FRONTEND_FIELDS = ["path", "source_file", "line", "backend_defined", "status"]
UPLOAD_FIELDS = ["extension", "backend_supported", "frontend_allowed", "status"]


def normalize_path(path: str) -> str:
    path = path.strip().strip("'\"`")
    path = re.sub(r"\$\{[^}]+\}", "{param}", path)
    path = re.sub(r"\{[^}/]+\}", "{param}", path)
    return path.rstrip("/") or "/"


def extract_backend_routes() -> list[dict[str, object]]:
    routes: list[dict[str, object]] = []
    route_pattern = re.compile(r"@router\.(get|post|put|patch|delete)\(\s*['\"]([^'\"]+)['\"]")
    for path in [BACKEND_API_DIR / "routes.py", BACKEND_API_DIR / "auth_routes.py"]:
        prefix = ""
        text = path.read_text(encoding="utf-8", errors="replace")
        prefix_match = re.search(r"router\s*=\s*APIRouter\(\s*prefix\s*=\s*['\"]([^'\"]+)['\"]", text)
        if prefix_match:
            prefix = prefix_match.group(1).rstrip("/")
        for line_no, line in enumerate(text.splitlines(), start=1):
            match = route_pattern.search(line)
            if not match:
                continue
            method, route_path = match.groups()
            routes.append(
                {
                    "method": method.upper(),
                    "path": normalize_path(f"{prefix}{route_path}"),
                    "source_file": str(path.relative_to(ROOT)),
                    "line": line_no,
                }
            )
    return sorted(routes, key=lambda r: (str(r["path"]), str(r["method"])))


def should_keep_frontend_api_path(path: str) -> bool:
    return any(path == prefix or path.startswith(f"{prefix}/") for prefix in API_PREFIXES)


def add_frontend_entry(
    entries: list[dict[str, object]],
    *,
    raw_path: str,
    source_path: Path,
    line_no: int,
) -> None:
    rel = source_path.relative_to(ROOT)
    normalized = normalize_path(raw_path)
    if rel.as_posix() == "slideon-frontend/src/services/auth.js" and normalized in {
        "/register",
        "/login",
        "/refresh",
        "/me",
        "/logout",
    }:
        normalized = normalize_path(f"/auth{normalized}")
    if not should_keep_frontend_api_path(normalized):
        return
    entries.append(
        {
            "path": normalized,
            "source_file": str(rel),
            "line": line_no,
        }
    )


def extract_frontend_paths() -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    literal_pattern = re.compile(r"(['\"`])(/[^'\"`\s,)}]+)\1")
    template_pattern = re.compile(r"`(/[^`]+)`")
    for path in FRONTEND_SRC_DIR.rglob("*"):
        if path.suffix not in {".js", ".vue"}:
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel not in {
            "slideon-frontend/src/config/api.js",
            "slideon-frontend/src/services/auth.js",
            "slideon-frontend/src/views/ProfileView.vue",
        }:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for line_no, line in enumerate(text.splitlines(), start=1):
            for match in literal_pattern.finditer(line):
                raw_path = match.group(2)
                if raw_path.startswith("//"):
                    continue
                add_frontend_entry(entries, raw_path=raw_path, source_path=path, line_no=line_no)
            for match in template_pattern.finditer(line):
                raw_path = match.group(1)
                if raw_path.startswith("//"):
                    continue
                add_frontend_entry(entries, raw_path=raw_path, source_path=path, line_no=line_no)
    dedup: dict[tuple[str, str, int], dict[str, object]] = {}
    for entry in entries:
        dedup[(str(entry["path"]), str(entry["source_file"]), int(entry["line"]))] = entry
    return sorted(dedup.values(), key=lambda e: (str(e["path"]), str(e["source_file"]), int(e["line"])))


def extract_backend_upload_suffixes() -> set[str]:
    text = DOC_PARSER.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"SUPPORTED_DOCUMENT_SUFFIXES\s*=\s*(\{[^}]+\})", text)
    if not match:
        return set()
    value = ast.literal_eval(match.group(1))
    return {str(item) for item in value}


def extract_frontend_upload_suffixes() -> set[str]:
    text = FRONTEND_API_CONFIG.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"allowedTypes\s*:\s*(\[[^\]]+\])", text)
    if not match:
        return set()
    value = ast.literal_eval(match.group(1))
    return {str(item) for item in value}


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run API contract coverage tests.")
    parser.add_argument("--result-prefix", default="api_contract_test")
    args = parser.parse_args()

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()

    backend_routes = extract_backend_routes()
    frontend_paths = extract_frontend_paths()
    backend_paths = {str(route["path"]) for route in backend_routes}
    frontend_path_set = {str(entry["path"]) for entry in frontend_paths}

    backend_rows = []
    for route in backend_routes:
        referenced = str(route["path"]) in frontend_path_set
        backend_rows.append(
            {
                **route,
                "frontend_referenced": referenced,
                "status": "covered" if referenced else "backend_only",
            }
        )

    frontend_rows = []
    frontend_sources: dict[str, list[str]] = defaultdict(list)
    for entry in frontend_paths:
        frontend_sources[str(entry["path"])].append(f"{entry['source_file']}:{entry['line']}")
        defined = str(entry["path"]) in backend_paths
        frontend_rows.append(
            {
                **entry,
                "backend_defined": defined,
                "status": "matched" if defined else "frontend_only",
            }
        )

    backend_suffixes = extract_backend_upload_suffixes()
    frontend_suffixes = extract_frontend_upload_suffixes()
    upload_rows = []
    for ext in sorted(backend_suffixes | frontend_suffixes):
        backend_supported = ext in backend_suffixes
        frontend_allowed = ext in frontend_suffixes
        status = "matched" if backend_supported and frontend_allowed else "mismatch"
        upload_rows.append(
            {
                "extension": ext,
                "backend_supported": backend_supported,
                "frontend_allowed": frontend_allowed,
                "status": status,
            }
        )

    backend_csv = RESULT_DIR / f"{args.result_prefix}_backend_routes.csv"
    frontend_csv = RESULT_DIR / f"{args.result_prefix}_frontend_paths.csv"
    upload_csv = RESULT_DIR / f"{args.result_prefix}_upload_types.csv"
    summary_json = RESULT_DIR / f"{args.result_prefix}_summary.json"
    write_csv(backend_csv, backend_rows, BACKEND_FIELDS)
    write_csv(frontend_csv, frontend_rows, FRONTEND_FIELDS)
    write_csv(upload_csv, upload_rows, UPLOAD_FIELDS)

    backend_only = [row for row in backend_rows if row["status"] == "backend_only"]
    frontend_only = [row for row in frontend_rows if row["status"] == "frontend_only"]
    upload_mismatches = [row for row in upload_rows if row["status"] == "mismatch"]

    summary = {
        "timestamp": timestamp,
        "success": not frontend_only and not upload_mismatches,
        "backend_route_count": len(backend_rows),
        "frontend_path_reference_count": len(frontend_rows),
        "backend_routes_referenced_by_frontend": len(backend_rows) - len(backend_only),
        "backend_only_route_count": len(backend_only),
        "frontend_only_path_count": len(frontend_only),
        "upload_type_mismatch_count": len(upload_mismatches),
        "backend_only_routes": backend_only,
        "frontend_only_paths": frontend_only,
        "upload_type_mismatches": upload_mismatches,
        "outputs": {
            "backend_routes_csv": str(backend_csv.relative_to(ROOT)),
            "frontend_paths_csv": str(frontend_csv.relative_to(ROOT)),
            "upload_types_csv": str(upload_csv.relative_to(ROOT)),
        },
        "requirements_traceability": {
            "2.2": "REST route definitions are discoverable from backend decorators",
            "2.3": "frontend-referenced API paths are checked against backend-defined paths",
            "3.3": "frontend API integration paths are checked against backend contract",
            "4.2": "document upload file type preprocessing contract is compared",
            "7.0": "RAG document/search endpoints are included in the contract",
        },
    }
    summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "success": summary["success"],
        "backend_route_count": summary["backend_route_count"],
        "frontend_only_path_count": summary["frontend_only_path_count"],
        "upload_type_mismatch_count": summary["upload_type_mismatch_count"],
        "summary": str(summary_json.relative_to(ROOT)),
    }, ensure_ascii=False, indent=2))
    return 0 if summary["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
