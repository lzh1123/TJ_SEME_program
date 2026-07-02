from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright


ROOT = Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "test" / "results"
DEFAULT_BASE_URL = "http://119.3.125.141"
FIELDS = ["timestamp", "case", "status", "detail"]


@dataclass
class FrontendE2ERunner:
    base_url: str
    headless: bool
    timeout_ms: int

    def __post_init__(self) -> None:
        self.rows: list[dict[str, Any]] = []
        suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        self.username = f"slideon_e2e_{suffix}"
        self.email = f"{self.username}@example.test"
        self.password = f"SlideonE2E{suffix}!"

    def record(self, case: str, ok: bool, detail: str) -> None:
        self.rows.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "case": case,
                "status": "passed" if ok else "failed",
                "detail": detail[:300],
            }
        )

    def step(self, case: str, fn) -> None:
        try:
            detail = fn()
            self.record(case, True, "ok" if detail is None else str(detail))
        except Exception as exc:
            self.record(case, False, f"{type(exc).__name__}: {exc}")

    def run(self) -> int:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            page = browser.new_page()
            page.set_default_timeout(self.timeout_ms)
            try:
                self.step("frontend_home_loads", lambda: self.expect_home(page))
                self.step("frontend_register_page_loads", lambda: self.expect_register_page(page))
                self.step("frontend_register_account", lambda: self.register(page))
                self.step("frontend_login_account", lambda: self.login(page))
                self.step("frontend_profile_page_loads", lambda: self.expect_route_ready(page, "/profile"))
                self.step("frontend_profile_update_display_name", lambda: self.update_profile_display_name(page))
                self.step("frontend_dashboard_route_loads", lambda: self.expect_route_ready(page, "/dashboard"))
                self.step("frontend_knowledge_base_route_loads", lambda: self.expect_route_ready(page, "/knowledge-base"))
                self.step("frontend_outline_editor_route_loads", lambda: self.expect_route_ready(page, "/outline-editor"))
            finally:
                browser.close()
        return 0 if all(row["status"] == "passed" for row in self.rows) else 1

    def goto(self, page: Page, path: str) -> None:
        page.goto(f"{self.base_url.rstrip('/')}{path}", wait_until="networkidle")

    def expect_home(self, page: Page) -> str:
        self.goto(page, "/")
        assert page.locator("#app").count() == 1
        assert "Slideon" in page.content()
        return page.title()

    def expect_route_ready(self, page: Page, path: str) -> str:
        self.goto(page, path)
        assert page.locator("#app").count() == 1
        body = page.locator("body").inner_text(timeout=self.timeout_ms)
        assert len(body.strip()) > 0
        return f"{path} text length={len(body)}"

    def expect_route_text(self, page: Page, path: str, text: str) -> str:
        self.goto(page, path)
        body = page.locator("body").inner_text(timeout=self.timeout_ms)
        assert text.lower() in body.lower()
        return f"{path} contains {text}"

    def expect_register_page(self, page: Page) -> str:
        self.goto(page, "/register")
        password_inputs = page.locator("input[type='password']").count()
        text_inputs = page.locator("input").count()
        assert password_inputs >= 1
        assert text_inputs >= 3
        return f"inputs={text_inputs}, password_inputs={password_inputs}"

    def register(self, page: Page) -> str:
        self.goto(page, "/register")
        fill_first(page, ["#username", "input[name='username']", "input[placeholder*='用户名']", "input[placeholder*='username']"], self.username)
        fill_first(page, ["#email", "input[name='email']", "input[type='email']", "input[placeholder*='邮箱']", "input[placeholder*='email']"], self.email)
        fill_first(page, ["#displayName"], "Slideon E2E Test")
        fill_first(page, ["#password", "input[name='password']", "input[type='password']"], self.password)
        fill_first(page, ["#confirmPassword"], self.password)
        submit_first(page, ["button[type='submit']", "button:has-text('注册')", "button:has-text('Register')"])
        page.wait_for_timeout(2500)
        body = page.locator("body").inner_text(timeout=self.timeout_ms)
        assert "/login" in page.url or "成功" in body or "success" in body.lower()
        return page.url

    def login(self, page: Page) -> str:
        self.goto(page, "/login")
        fill_first(page, ["#username", "input[name='username']", "input[name='account']", "input[placeholder*='用户名']", "input[placeholder*='username']"], self.username)
        fill_first(page, ["#password", "input[name='password']", "input[type='password']"], self.password)
        submit_first(page, ["button[type='submit']", "button:has-text('登录')", "button:has-text('Login')"])
        page.wait_for_timeout(2000)
        token = page.evaluate("() => localStorage.getItem('access_token')")
        assert token
        return "access token stored"

    def update_profile_display_name(self, page: Page) -> str:
        self.goto(page, "/profile")
        new_name = f"Updated {self.username}"
        fill_first(page, ["#displayName"], new_name)
        submit_first(page, ["button:has-text('保存修改')", "button.btn-primary"])
        page.wait_for_timeout(2000)
        body = page.locator("body").inner_text(timeout=self.timeout_ms)
        assert new_name in body
        return "updated display name visible"


def fill_first(page: Page, selectors: list[str], value: str) -> None:
    for selector in selectors:
        locator = page.locator(selector).first
        try:
            if locator.count() > 0:
                locator.fill(value)
                return
        except PlaywrightTimeoutError:
            pass
    raise AssertionError(f"No input matched {selectors}")


def submit_first(page: Page, selectors: list[str]) -> None:
    for selector in selectors:
        locator = page.locator(selector).first
        try:
            if locator.count() > 0:
                locator.click()
                return
        except PlaywrightTimeoutError:
            pass
    raise AssertionError(f"No submit matched {selectors}")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deployed frontend E2E tests.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--timeout-ms", type=int, default=30000)
    parser.add_argument("--result-prefix", default="frontend_e2e_test")
    args = parser.parse_args()

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    runner = FrontendE2ERunner(args.base_url, headless=not args.headed, timeout_ms=args.timeout_ms)
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
            "frontend_e2e_results_csv": str(result_csv.relative_to(ROOT)),
        },
        "requirements_traceability": {
            "3.0": "deployed frontend pages are opened in a real browser",
            "3.1": "registration and login UI flow is exercised",
            "3.2": "authenticated profile/dashboard navigation is exercised",
            "3.3": "frontend communicates with deployed authentication API",
            "7.0": "knowledge base route is opened in a real browser",
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
