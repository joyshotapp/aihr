from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.cloud_provisioning import provision_cloud_resources


def main() -> int:
    create_missing = "--check-only" not in sys.argv
    report = provision_cloud_resources(create_missing=create_missing)
    print(json.dumps(report, ensure_ascii=False, indent=2))

    has_error = any(item["status"] == "error" for item in report)
    has_missing = any(item["status"] == "missing" for item in report)
    if has_error or has_missing:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
