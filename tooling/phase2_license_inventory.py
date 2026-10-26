"""Print conservative license metadata from the active installed environment.

Designed to execute with the independently installed clean Python interpreter.
"""
from __future__ import annotations

import json
from importlib import metadata


def main() -> None:
    entries = []
    for package in metadata.distributions():
        meta = package.metadata
        license_value = meta.get("License-Expression") or meta.get("License") or ""
        if len(license_value) > 120:
            license_value = "long license text in installed metadata (inspect wheel)"
        classifiers = [value for value in meta.get_all("Classifier", []) if value.startswith("License ::")]
        entries.append({
            "name": meta.get("Name", "unknown"),
            "version": package.version,
            "declared_license": license_value,
            "license_classifiers": classifiers[:5],
            "metadata_missing": not license_value and not classifiers,
        })
    print(json.dumps(sorted(entries, key=lambda entry: entry["name"].lower()), ensure_ascii=False))


if __name__ == "__main__":
    main()
