from __future__ import annotations

import argparse
import csv
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests

from run_live_api_tests import choose_llm_config, load_env_file, safe_error_detail


ROOT = Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "test" / "results"
DEFAULT_BASE_URL = "http://119.3.125.141"
FIELDS = ["timestamp", "case", "method", "path", "status_code", "status", "detail"]


@dataclass
class RemainingLiveRunner:
    base_url: str
    timeout: float
    slow_timeout: float
    poll_timeout: float

    def __post_init__(self) -> None:
        self.session = requests.Session()
        self.rows: list[dict[str, Any]] = []
        self.access_token: str | None = None
        suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        self.username = f"slideon_remaining_{suffix}"
        self.email = f"{self.username}@example.test"
        self.password = f"SlideonRemaining{suffix}!"
        self.unique_phrase = f"slideon-rag-live-phrase-{suffix}"
        self.uploaded_source = f"{self.unique_phrase}.txt"

    def record(self, case: str, method: str, path: str, status_code: int | None, ok: bool, detail: str) -> None:
        self.rows.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "case": case,
                "method": method,
                "path": path,
                "status_code": "" if status_code is None else status_code,
                "status": "passed" if ok else "failed",
                "detail": detail[:300],
            }
        )

    def request(self, method: str, path: str, *, timeout: float | None = None, **kwargs: Any) -> requests.Response:
        headers = kwargs.pop("headers", {})
        if self.access_token:
            headers = {"Authorization": f"Bearer {self.access_token}", **headers}
        return self.session.request(
            method,
            f"{self.base_url.rstrip('/')}{path}",
            timeout=self.timeout if timeout is None else timeout,
            headers=headers,
            **kwargs,
        )

    def check(self, case: str, method: str, path: str, expected: set[int], **kwargs: Any) -> requests.Response | None:
        timeout = kwargs.pop("timeout", None)
        try:
            response = self.request(method, path, timeout=timeout, **kwargs)
        except Exception as exc:
            self.record(case, method, path, None, False, type(exc).__name__)
            return None
        ok = response.status_code in expected
        self.record(case, method, path, response.status_code, ok, "ok" if ok else safe_error_detail(response))
        return response

    def register_and_login(self) -> bool:
        register = self.check(
            "remaining_auth_register",
            "POST",
            "/auth/register",
            {201},
            json={
                "username": self.username,
                "email": self.email,
                "password": self.password,
                "display_name": "Slideon Remaining Test",
            },
        )
        if register is None or register.status_code != 201:
            return False
        login = self.check(
            "remaining_auth_login",
            "POST",
            "/auth/login",
            {200},
            json={"username": self.username, "password": self.password},
        )
        if login is None or login.status_code != 200:
            return False
        data = login.json()
        self.access_token = data.get("access_token") or data.get("accessToken")
        ok = bool(self.access_token)
        self.record("remaining_auth_token_received", "POST", "/auth/login", login.status_code, ok, "token received")
        return ok

    def configure_llm(self) -> dict[str, str] | None:
        llm_config = choose_llm_config()
        if not llm_config:
            self.record("remaining_llm_config_available", "LOCAL", ".env", None, False, "no API key in .env")
            return None
        response = self.check("remaining_llm_config_update", "PUT", "/auth/llm-config", {200}, json=llm_config)
        return llm_config if response is not None and response.status_code == 200 else None

    def run_frontend_http_smoke(self) -> None:
        home = self.check("frontend_home_html", "GET", "/", {200})
        if home is not None and home.status_code == 200:
            text = home.text
            ok = "<div id=\"app\">" in text and "assets/" in text
            self.record("frontend_home_contains_app_mount", "GET", "/", home.status_code, ok, "app mount and assets referenced")
        self.check("frontend_login_route_fallback", "GET", "/login", {200})
        self.check("frontend_knowledge_base_route_fallback", "GET", "/knowledge-base", {200})

    def run_rag_write_read_cleanup(self) -> None:
        content = (
            f"{self.unique_phrase}\n"
            "This file is generated by the Slideon live RAG test. "
            "It should be deleted after the test completes."
        ).encode("utf-8")
        files = {"file": (self.uploaded_source, content, "text/plain")}
        upload = self.check("rag_upload_single_document", "POST", "/rag/documents", {200}, files=files)
        if upload is None or upload.status_code != 200:
            return

        self.check("rag_sources_after_upload", "GET", "/rag/sources", {200})
        documents = self.check("rag_documents_after_upload", "GET", "/rag/documents", {200})
        source = self.uploaded_source
        if documents is not None and documents.status_code == 200:
            try:
                payload = documents.json()
                for doc in payload.get("documents", []):
                    if (
                        doc.get("source") == self.uploaded_source
                        or doc.get("filename") == self.uploaded_source
                        or self.unique_phrase in str(doc.get("source", ""))
                        or self.unique_phrase in str(doc.get("filename", ""))
                    ):
                        source = doc.get("source") or self.uploaded_source
                        break
                self.record("rag_preview_source_resolved_from_documents", "GET", "/rag/documents", 200, bool(source), "source resolved")
            except Exception as exc:
                self.record("rag_preview_source_resolved_from_documents", "GET", "/rag/documents", documents.status_code, False, type(exc).__name__)

        encoded_source = quote(source, safe="")
        preview_path = f"/rag/documents/{encoded_source}/preview"
        preview = self.check("rag_preview_uploaded_document", "GET", preview_path, {200})
        if preview is not None and preview.status_code == 200:
            try:
                data = preview.json()
                ok = self.unique_phrase in json.dumps(data, ensure_ascii=False)
                self.record("rag_preview_contains_unique_phrase", "GET", preview_path, preview.status_code, ok, "unique phrase present")
            except Exception as exc:
                self.record("rag_preview_contains_unique_phrase", "GET", preview_path, preview.status_code, False, type(exc).__name__)

        search = self.check(
            "rag_search_uploaded_phrase",
            "POST",
            "/rag/search",
            {200},
            json={"query": self.unique_phrase, "top_k": 5, "enable_web": False, "enable_local": True, "deep_fetch": False},
            timeout=self.slow_timeout,
        )
        if search is not None and search.status_code == 200:
            ok = self.unique_phrase in json.dumps(search.json(), ensure_ascii=False)
            self.record("rag_search_contains_unique_phrase", "POST", "/rag/search", search.status_code, ok, "unique phrase present")

        self.check("rag_delete_uploaded_document", "DELETE", f"/rag/documents/{encoded_source}", {200})

    def run_llm_and_export_attempts(self, llm_config: dict[str, str] | None) -> None:
        if not llm_config:
            return
        dsl = self.check(
            "llm_generate_short_outline_long_timeout",
            "POST",
            "/dsl",
            {200},
            json={
                "topic": "Software testing remaining live validation",
                "theme": "paper_light",
                "use_rag": False,
                "modelProvider": llm_config["provider"],
                "pageCountPreset": "short",
            },
            timeout=self.slow_timeout,
        )
        if dsl is not None and dsl.status_code == 200:
            try:
                data = dsl.json()
                ok = isinstance(data.get("slides"), list) and len(data["slides"]) > 0
                self.record("llm_generated_outline_has_slides", "POST", "/dsl", dsl.status_code, ok, "slides present")
            except Exception as exc:
                self.record("llm_generated_outline_has_slides", "POST", "/dsl", dsl.status_code, False, type(exc).__name__)

        created = self.check(
            "presentation_create_live_generation",
            "POST",
            "/presentations",
            {200},
            json={"topic": "Software testing export validation", "theme": "paper_light", "use_rag": False},
            timeout=self.slow_timeout,
        )
        if created is None or created.status_code != 200:
            return
        try:
            presentation_id = created.json().get("id")
        except Exception:
            presentation_id = None
        ok = bool(presentation_id)
        self.record("presentation_create_returns_id", "POST", "/presentations", created.status_code, ok, "id present")
        if not presentation_id:
            return

        self.check("presentation_get_created", "GET", f"/presentations/{presentation_id}", {200})
        export = self.check(
            "presentation_export_pptx",
            "POST",
            f"/presentations/{presentation_id}/export/pptx",
            {200},
            timeout=self.slow_timeout,
        )
        if export is not None and export.status_code == 200:
            content_type = export.headers.get("content-type", "")
            ok = (
                "presentation" in content_type
                or export.content.startswith(b"PK")
            ) and len(export.content) > 1024
            self.record("presentation_export_pptx_openxml_payload", "POST", f"/presentations/{presentation_id}/export/pptx", export.status_code, ok, "pptx-like payload")

    def run(self) -> int:
        self.run_frontend_http_smoke()
        if not self.register_and_login():
            return 1
        llm_config = self.configure_llm()
        self.run_rag_write_read_cleanup()
        self.run_llm_and_export_attempts(llm_config)
        self.check("remaining_auth_logout", "POST", "/auth/logout", {200})
        return 0 if all(row["status"] == "passed" for row in self.rows) else 1


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run remaining live validation tests.")
    parser.add_argument("--base-url", default=os.getenv("LIVE_API_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--slow-timeout", type=float, default=420.0)
    parser.add_argument("--poll-timeout", type=float, default=180.0)
    parser.add_argument("--result-prefix", default="live_remaining_test")
    args = parser.parse_args()

    load_env_file(ROOT / ".env")
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    runner = RemainingLiveRunner(args.base_url, args.timeout, args.slow_timeout, args.poll_timeout)
    code = runner.run()

    result_csv = RESULT_DIR / f"{args.result_prefix}_results.csv"
    summary_json = RESULT_DIR / f"{args.result_prefix}_summary.json"
    write_csv(result_csv, runner.rows)
    failed = [row for row in runner.rows if row["status"] != "passed"]
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "base_url": args.base_url,
        "success": not failed,
        "tests": len(runner.rows),
        "failures": len(failed),
        "failed_cases": failed,
        "outputs": {
            "live_remaining_results_csv": str(result_csv.relative_to(ROOT)),
        },
        "requirements_traceability": {
            "2.0": "deployed frontend and backend runtime workflows are exercised",
            "2.3": "deployed presentation creation and export are attempted",
            "3.0": "deployed SPA routes are reachable over HTTP",
            "4.0": "live LLM outline generation is attempted with a long timeout",
            "7.0": "RAG upload, preview, search, and cleanup workflow is exercised",
            "8.0": "deployed PPTX export payload is validated when presentation creation succeeds",
        },
    }
    summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "success": summary["success"],
        "tests": summary["tests"],
        "failures": summary["failures"],
        "summary": str(summary_json.relative_to(ROOT)),
    }, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
