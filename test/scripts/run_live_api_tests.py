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

import requests


ROOT = Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "test" / "results"
FIELDS = ["timestamp", "case", "method", "path", "status_code", "status", "detail"]
DEFAULT_BASE_URL = "http://119.3.125.141"


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def choose_llm_config() -> dict[str, str] | None:
    providers = [
        {
            "provider": "glm",
            "model": os.getenv("GLM_MODEL", "glm-4.7"),
            "apiBase": os.getenv("GLM_API_BASE", "https://open.bigmodel.cn/api/paas/v4"),
            "apiKey": os.getenv("GLM_API_KEY") or os.getenv("ZHIPU_API_KEY") or os.getenv("ZAI_API_KEY"),
        },
        {
            "provider": "deepseek",
            "model": os.getenv("DEEPSEEK_MODEL", os.getenv("LLM_MODEL", "Deepseek-V4-pro")),
            "apiBase": os.getenv("DEEPSEEK_API_BASE", os.getenv("LLM_API_BASE", "https://api.deepseek.com")),
            "apiKey": os.getenv("DEEPSEEK_API_KEY") or os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY"),
        },
        {
            "provider": "qwen",
            "model": os.getenv("QWEN_MODEL", "qwen-plus"),
            "apiBase": os.getenv("QWEN_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
            "apiKey": os.getenv("QWEN_API_KEY") or os.getenv("DASHSCOPE_API_KEY"),
        },
    ]
    for item in providers:
        if item.get("apiKey"):
            return item  # type: ignore[return-value]
    return None


@dataclass
class LiveApiRunner:
    base_url: str
    timeout: float
    include_llm_generation: bool

    def __post_init__(self) -> None:
        self.session = requests.Session()
        self.rows: list[dict[str, Any]] = []
        self.access_token: str | None = None
        suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        self.username = f"slideon_test_{suffix}"
        self.email = f"{self.username}@example.test"
        self.password = f"SlideonTest{suffix}!"

    def record(self, case: str, method: str, path: str, status_code: int | None, ok: bool, detail: str) -> None:
        self.rows.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "case": case,
                "method": method,
                "path": path,
                "status_code": "" if status_code is None else status_code,
                "status": "passed" if ok else "failed",
                "detail": detail,
            }
        )

    def request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        headers = kwargs.pop("headers", {})
        if self.access_token:
            headers = {"Authorization": f"Bearer {self.access_token}", **headers}
        return self.session.request(
            method,
            f"{self.base_url.rstrip('/')}{path}",
            timeout=self.timeout,
            headers=headers,
            **kwargs,
        )

    def check(self, case: str, method: str, path: str, expected: set[int], **kwargs: Any) -> requests.Response | None:
        try:
            response = self.request(method, path, **kwargs)
        except Exception as exc:
            self.record(case, method, path, None, False, type(exc).__name__)
            return None
        ok = response.status_code in expected
        detail = "ok" if ok else safe_error_detail(response)
        self.record(case, method, path, response.status_code, ok, detail)
        return response

    def run(self) -> int:
        health = self.check("public_health", "GET", "/health", {200})
        if health is not None and health.ok:
            try:
                self.record(
                    "public_health_body",
                    "GET",
                    "/health",
                    health.status_code,
                    health.json().get("ok") is True,
                    "ok field is true",
                )
            except Exception as exc:
                self.record("public_health_body", "GET", "/health", health.status_code, False, type(exc).__name__)

        self.check("public_themes", "GET", "/themes", {200})
        self.check("public_llm_providers", "GET", "/llm/providers", {200})

        register = self.check(
            "auth_register_test_account",
            "POST",
            "/auth/register",
            {201},
            json={
                "username": self.username,
                "email": self.email,
                "password": self.password,
                "display_name": "Slideon Live Test",
            },
        )
        if register is None or register.status_code != 201:
            return 1

        login = self.check(
            "auth_login_test_account",
            "POST",
            "/auth/login",
            {200},
            json={"username": self.username, "password": self.password},
        )
        if login is None or login.status_code != 200:
            return 1
        data = login.json()
        self.access_token = data.get("access_token") or data.get("accessToken")
        refresh_token = data.get("refresh_token") or data.get("refreshToken")
        if not self.access_token:
            self.record("auth_login_access_token", "POST", "/auth/login", login.status_code, False, "missing token")
            return 1
        self.record("auth_login_access_token", "POST", "/auth/login", login.status_code, True, "token received")

        me = self.check("auth_get_profile", "GET", "/auth/me", {200})
        if me is not None and me.status_code == 200:
            profile = me.json()
            self.record(
                "auth_profile_matches_test_account",
                "GET",
                "/auth/me",
                me.status_code,
                profile.get("username") == self.username,
                "username matches",
            )

        self.check("auth_update_profile", "PUT", "/auth/me", {200}, json={"displayName": "Slideon Live Test Updated"})

        if refresh_token:
            self.check("auth_refresh_token", "POST", "/auth/refresh", {200}, json={"refreshToken": refresh_token})

        llm_config = choose_llm_config()
        if llm_config:
            self.check("auth_update_llm_config", "PUT", "/auth/llm-config", {200}, json=llm_config)
            self.check("auth_get_llm_config", "GET", "/auth/llm-config", {200})
        else:
            self.record("auth_update_llm_config", "PUT", "/auth/llm-config", "", False, "no API key in .env")

        outline_id = f"live-outline-{int(time.time())}"
        outline_payload = {
            "id": outline_id,
            "title": "Live API Smoke Outline",
            "dsl": json.dumps({"title": "Live API Smoke Outline", "slides": []}, ensure_ascii=False),
            "slide_count": 0,
        }
        self.check("outline_create", "POST", "/outlines", {200}, json=outline_payload)
        self.check("outline_list", "GET", "/outlines", {200})
        self.check("outline_get", "GET", f"/outlines/{outline_id}", {200})
        self.check("outline_update", "PUT", f"/outlines/{outline_id}", {200}, json={"title": "Live API Smoke Outline Updated"})
        self.check("outline_delete", "DELETE", f"/outlines/{outline_id}", {200})

        self.check(
            "runtime_render_tree",
            "POST",
            "/render-tree",
            {200},
            json={
                "topic": "Live render tree",
                "theme": "paper_light",
                "outline": {
                    "title": "Live render tree",
                    "slides": [{"intent": "cover", "title": "Live", "subtitle": "Smoke"}],
                },
            },
        )

        self.check("rag_stats_read", "GET", "/rag/stats", {200})
        self.check("rag_sources_read_for_test_user", "GET", "/rag/sources", {200})

        if self.include_llm_generation and llm_config:
            self.check(
                "llm_generate_short_outline",
                "POST",
                "/dsl",
                {200},
                json={
                    "topic": "Software testing smoke test",
                    "theme": "paper_light",
                    "use_rag": False,
                    "modelProvider": llm_config["provider"],
                    "pageCountPreset": "short",
                },
            )

        self.check("auth_logout", "POST", "/auth/logout", {200})
        return 0 if all(row["status"] == "passed" for row in self.rows) else 1


def safe_error_detail(response: requests.Response) -> str:
    try:
        data = response.json()
    except Exception:
        return response.text[:200]
    detail = data.get("detail") if isinstance(data, dict) else None
    if isinstance(detail, str):
        return detail[:200]
    return f"unexpected status {response.status_code}"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run live API tests against a deployed Slideon backend.")
    parser.add_argument("--base-url", default=os.getenv("LIVE_API_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--include-llm-generation", action="store_true")
    parser.add_argument("--result-prefix", default="live_api_test")
    args = parser.parse_args()

    load_env_file(ROOT / ".env")
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    runner = LiveApiRunner(
        base_url=args.base_url,
        timeout=args.timeout,
        include_llm_generation=args.include_llm_generation,
    )
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
            "live_api_results_csv": str(result_csv.relative_to(ROOT)),
        },
        "requirements_traceability": {
            "2.0": "deployed backend API runtime endpoints are exercised",
            "2.2": "authentication and profile endpoints are exercised on the deployed service",
            "2.3": "outline persistence endpoints are exercised on the deployed service",
            "3.3": "frontend-facing API paths are exercised through deployed HTTP endpoints",
            "4.2": "render-tree generation from structured outline is exercised",
            "7.0": "deployed RAG read endpoints are exercised without mutating the knowledge base",
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
