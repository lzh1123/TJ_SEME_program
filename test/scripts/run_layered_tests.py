from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "test" / "results"
FIELDS = [
    "timestamp",
    "layer",
    "command",
    "tests",
    "failures",
    "errors",
    "skipped",
    "duration_seconds",
    "success",
    "artifact",
]
FRONTEND_STATIC_SUMMARY = RESULT_DIR / "frontend_static_test_summary.json"


PYTEST_LAYERS = [
    {
        "layer": "unit",
        "target": "backend/test/unit",
        "requirements": ["1.0", "2.5", "4.0", "5.0", "6.0", "7.0"],
    },
    {
        "layer": "integration",
        "target": "backend/test/integration",
        "requirements": ["2.0", "5.0", "6.0", "8.0"],
    },
    {
        "layer": "api_runtime",
        "target": "backend/test/integration/test_api_runtime_smoke.py",
        "requirements": ["2.0", "2.2", "2.3", "4.0", "7.0"],
    },
    {
        "layer": "regression",
        "target": "backend/test/test_dsl_repair.py",
        "requirements": ["4.0", "5.0", "6.0"],
    },
]


def parse_junit(path: Path) -> dict[str, int | float | bool]:
    root = ET.parse(path).getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    if suite is None:
        raise ValueError(f"No testsuite element found in {path}")
    tests = int(suite.attrib.get("tests", 0))
    failures = int(suite.attrib.get("failures", 0))
    errors = int(suite.attrib.get("errors", 0))
    skipped = int(suite.attrib.get("skipped", 0))
    duration = float(suite.attrib.get("time", 0.0))
    return {
        "tests": tests,
        "failures": failures,
        "errors": errors,
        "skipped": skipped,
        "duration_seconds": round(duration, 3),
        "success": failures == 0 and errors == 0,
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def run_pytest_layer(layer: dict[str, object], timestamp: str) -> tuple[dict[str, object], int]:
    layer_name = str(layer["layer"])
    junit_rel = Path("test") / "results" / f"{layer_name}_test_{timestamp}.xml"
    junit_path = ROOT / junit_rel
    command = [
        sys.executable,
        "-m",
        "pytest",
        str(layer["target"]),
        f"--junitxml={junit_rel}",
        "-q",
    ]
    started = time.perf_counter()
    completed = subprocess.run(command, cwd=ROOT)
    elapsed = round(time.perf_counter() - started, 3)
    parsed = parse_junit(junit_path)
    parsed["duration_seconds"] = elapsed
    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "layer": layer_name,
        "command": " ".join(command),
        "artifact": str(junit_rel),
        **parsed,
    }
    return row, completed.returncode


def run_frontend_build(timestamp: str) -> tuple[dict[str, object], int]:
    npm_executable = shutil.which("npm.cmd") or shutil.which("npm")
    if npm_executable is None:
        return (
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "layer": "frontend_build",
                "command": "npm run build",
                "tests": 0,
                "failures": 0,
                "errors": 1,
                "skipped": 0,
                "duration_seconds": 0,
                "success": False,
                "artifact": "slideon-frontend/dist",
            },
            1,
        )

    command = [npm_executable, "run", "build"]
    started = time.perf_counter()
    completed = subprocess.run(command, cwd=ROOT / "slideon-frontend")
    elapsed = round(time.perf_counter() - started, 3)
    return (
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "layer": "frontend_build",
            "command": " ".join(command),
            "tests": 1,
            "failures": 0 if completed.returncode == 0 else 1,
            "errors": 0,
            "skipped": 0,
            "duration_seconds": elapsed,
            "success": completed.returncode == 0,
            "artifact": "slideon-frontend/dist",
        },
        completed.returncode,
    )


def run_frontend_static_tests() -> tuple[dict[str, object], int]:
    command = [sys.executable, "test/scripts/run_frontend_static_tests.py"]
    started = time.perf_counter()
    completed = subprocess.run(command, cwd=ROOT)
    elapsed = round(time.perf_counter() - started, 3)
    summary = json.loads(FRONTEND_STATIC_SUMMARY.read_text(encoding="utf-8"))
    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "layer": "frontend_static",
        "command": " ".join(command),
        "tests": summary["tests"],
        "failures": summary["failures"],
        "errors": 0,
        "skipped": 0,
        "duration_seconds": elapsed,
        "success": summary["success"],
        "artifact": str(FRONTEND_STATIC_SUMMARY.relative_to(ROOT)),
    }
    return row, completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Run layered tests.")
    parser.add_argument("--result-name", default="layered_test_results.csv")
    parser.add_argument("--json-name", default="layered_test_summary.json")
    parser.add_argument("--skip-frontend-build", action="store_true")
    args = parser.parse_args()

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    rows: list[dict[str, object]] = []
    return_code = 0
    for layer in PYTEST_LAYERS:
        row, code = run_pytest_layer(layer, timestamp)
        rows.append(row)
        return_code = return_code or code

    row, code = run_frontend_static_tests()
    rows.append(row)
    return_code = return_code or code

    frontend_row = None
    if not args.skip_frontend_build:
        frontend_row, code = run_frontend_build(timestamp)
        rows.append(frontend_row)
        return_code = return_code or code

    result_path = RESULT_DIR / args.result_name
    summary_path = RESULT_DIR / args.json_name
    write_csv(result_path, rows)

    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "success": return_code == 0,
        "layers": rows,
        "outputs": {
            "layered_results_csv": str(result_path.relative_to(ROOT)),
        },
        "requirements_traceability": {
            layer["layer"]: layer["requirements"] for layer in PYTEST_LAYERS
        } | {
            "frontend_static": ["3.0", "3.3", "4.2"],
        } | ({"frontend_build": ["3.0", "3.1", "3.2", "3.3", "3.4"]} if frontend_row else {}),
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "success": summary["success"],
        "layers": [row["layer"] for row in rows],
        "summary": str(summary_path.relative_to(ROOT)),
    }, ensure_ascii=False, indent=2))
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
