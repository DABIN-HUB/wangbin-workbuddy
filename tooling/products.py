"""Per-product CLI, separate from the legacy tooling commands."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import product_factory as factory


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m tooling.products")
    parser.add_argument("command", choices=("list", "init", "validate", "test", "package", "verify", "record", "portfolio", "release-check", "register-version", "upload-list"))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--id")
    parser.add_argument("--kind", choices=("Skill", "Expert", "Connector"))
    parser.add_argument("--connector-mode", choices=("cli", "mcp"))
    parser.add_argument("--field", choices=sorted(factory.METRIC_FIELDS))
    parser.add_argument("--value")
    parser.add_argument("--evidence")
    parser.add_argument("--version")
    parser.add_argument("--source")
    parser.add_argument("--candidate", default="UNKNOWN")
    parser.add_argument("--sha256", default="UNKNOWN")
    parser.add_argument("--date", default="UNKNOWN")
    parser.add_argument("--published-at", default="UNKNOWN")
    parser.add_argument("--activate", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        if args.command == "list":
            result = factory.load_catalog(root)
        elif args.command == "portfolio":
            result = factory.portfolio_report(root)
        elif args.command == "upload-list":
            result = factory.upload_list(root)
        elif args.command == "validate" and not args.id:
            problems = factory.validate_catalog(root)
            result = {"status": "PASS" if not problems else "FAIL", "findings": problems}
        else:
            if not args.id:
                parser.error("--id is required for this command")
            if args.command == "init":
                result = {"source": str(factory.init_product(root, args.id, args.kind, args.connector_mode)), "status": "SCAFFOLDED_NOT_RELEASE_READY"}
            elif args.command == "record":
                if args.field is None or args.value is None or args.evidence is None:
                    parser.error("record requires --field, --value and --evidence")
                value = args.value if args.field == "review_result" else float(args.value)
                result = factory.record_metric(root, args.id, args.field, value, evidence=args.evidence)
            elif args.command == "register-version":
                if args.version is None:
                    parser.error("register-version requires --version")
                result = factory.register_version(root, args.id, args.version, source=args.source,
                                                  candidate=args.candidate, sha256=args.sha256, date=args.date,
                                                  published_at=args.published_at, activate=args.activate)
            else:
                result = {"validate": factory.validate_product, "test": factory.test_product,
                          "package": factory.package_product, "verify": factory.verify_package,
                          "release-check": factory.release_check}[args.command](root, args.id)
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(2, f"error: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status", "PASS") not in {"FAIL", "BLOCKED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
