from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _compose_cmd() -> list[str]:
    """Return the correct Docker Compose CLI for this environment.

    Prefer `docker compose` (plugin) when available; fall back to the
    standalone `docker-compose` binary otherwise.
    """
    try:
        subprocess.run(
            ["docker", "compose", "version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
            timeout=5,
        )
        return ["docker", "compose"]
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        if shutil.which("docker-compose"):
            return ["docker-compose"]
    raise RuntimeError(
        "No Docker Compose CLI found. Install Docker Desktop or the docker-compose standalone binary."
    )


@dataclass
class Check:
    name: str
    command: list[str]
    cwd: Path
    timeout: int = 600
    env_overrides: dict[str, str] | None = None
    stub_files: list[Path] | None = None  # created before run, deleted after if they didn't previously exist


def build_checks(include_audit: bool, include_db_tests: bool) -> list[Check]:
    checks = [
        Check("Backend Ruff", [sys.executable, "-m", "ruff", "check", "app/"], ROOT),
        Check("Frontend TypeScript", ["npm", "exec", "--", "tsc", "--noEmit"], ROOT / "frontend"),
        Check("Frontend Lint", ["npm", "run", "lint"], ROOT / "frontend"),
        Check("Frontend Build", ["npm", "run", "build"], ROOT / "frontend"),
        Check("Admin TypeScript", ["npm", "exec", "--", "tsc", "--noEmit"], ROOT / "admin-frontend"),
        Check("Admin Lint", ["npm", "run", "lint"], ROOT / "admin-frontend"),
        Check("Admin Build", ["npm", "run", "build"], ROOT / "admin-frontend"),
        Check(
            "Stable Pytest Subset",
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_feature_flags_logic.py",
                "tests/test_llm_security_guardrails.py",
                "-q",
                "-o",
                "addopts=",
            ],
            ROOT,
            timeout=300,
        ),
        Check("Compose Dev Config", [*_compose_cmd(), "-f", "docker-compose.yml", "config"], ROOT),
        Check(
            "Compose Prod Config",
            [*_compose_cmd(), "-f", "docker-compose.prod.yml", "config"],
            ROOT,
            env_overrides={
                "POSTGRES_PASSWORD": "preflight-placeholder",
                "REDIS_PASSWORD": "preflight-placeholder",
                "ADMIN_REDIS_PASSWORD": "preflight-placeholder",
                "ADMIN_SERVICE_TOKEN": "preflight-placeholder",
            },
            stub_files=[ROOT / ".env.production"],
        ),
    ]

    if include_audit:
        checks.extend(
            [
                Check("Frontend Audit", ["npm", "audit", "--audit-level=high"], ROOT / "frontend"),
                Check("Admin Audit", ["npm", "audit", "--audit-level=high"], ROOT / "admin-frontend"),
            ]
        )

    if include_db_tests:
        checks.append(
            Check(
                "Auth Security Tests",
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "tests/test_auth_security.py",
                    "-q",
                    "-o",
                    "addopts=",
                ],
                ROOT,
                timeout=300,
            )
        )

    return checks


def run_check(check: Check) -> bool:
    print(f"\n=== {check.name} ===")
    command = check.command
    if sys.platform == "win32" and command and command[0] == "npm":
        command = ["cmd", "/c", *command]
    env = os.environ.copy()
    if check.env_overrides:
        env.update(check.env_overrides)

    # Create stub files that are required by the command but should not persist
    stubs_created: list[Path] = []
    if check.stub_files:
        for stub in check.stub_files:
            if not stub.exists():
                stub.touch()
                stubs_created.append(stub)

    try:
        subprocess.run(
            command,
            cwd=check.cwd,
            check=True,
            timeout=check.timeout,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        print(f"[PASS] {check.name}")
        return True
    except subprocess.TimeoutExpired:
        print(f"[FAIL] {check.name} timed out after {check.timeout}s")
        return False
    except subprocess.CalledProcessError as exc:
        print(f"[FAIL] {check.name} exited with code {exc.returncode}")
        return False
    finally:
        for stub in stubs_created:
            stub.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a stable UniHR release preflight suite.")
    parser.add_argument("--include-audit", action="store_true", help="Include npm audit checks.")
    parser.add_argument("--include-db-tests", action="store_true", help="Include DB-dependent auth tests.")
    args = parser.parse_args()

    checks = build_checks(include_audit=args.include_audit, include_db_tests=args.include_db_tests)
    results = [run_check(check) for check in checks]
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
