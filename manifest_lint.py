#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List

from manifest_downloader import is_reference_only_url


REQUIRED_FIELDS = [
    "object_id",
    "body",
    "mission",
    "instrument",
    "product_id",
    "level",
    "source_url",
    "local_path",
]


def read_manifest(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def expected_prefix(body: str) -> str:
    mapping = {
        "earth": "raw/earth/",
        "mars": "raw/mars/",
        "moon": "raw/moon/",
        "deepspace": "raw/telescope/",
    }
    return mapping.get(body.strip().lower(), "")


def find_duplicates(rows: Iterable[Dict[str, str]], field: str) -> Dict[str, List[str]]:
    values: Dict[str, List[str]] = defaultdict(list)
    for row in rows:
        value = (row.get(field) or "").strip()
        object_id = (row.get("object_id") or "?").strip()
        if value:
            values[value].append(object_id)
    return {value: object_ids for value, object_ids in values.items() if len(object_ids) > 1}


def find_source_product_duplicates(rows: Iterable[Dict[str, str]]) -> Dict[str, List[str]]:
    values: Dict[str, List[str]] = defaultdict(list)
    for row in rows:
        source_url = (row.get("source_url") or "").strip()
        product_id = (row.get("product_id") or "").strip()
        object_id = (row.get("object_id") or "?").strip()
        if source_url and product_id:
            values[f"{source_url} || {product_id}"].append(object_id)
    return {value: object_ids for value, object_ids in values.items() if len(object_ids) > 1}


def should_have_hash(row: Dict[str, str]) -> bool:
    source_url = (row.get("source_url") or "").strip()
    if not source_url:
        return False
    if is_reference_only_url(source_url):
        return False
    return True


def lint_rows(rows: List[Dict[str, str]], check_files: bool) -> Dict[str, List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    for row in rows:
        object_id = (row.get("object_id") or "?").strip()

        for field in REQUIRED_FIELDS:
            if not (row.get(field) or "").strip():
                errors.append(f"{object_id}: zorunlu alan bos -> {field}")

        local_path = (row.get("local_path") or "").strip().replace("\\", "/")
        prefix = expected_prefix(row.get("body") or "")
        if prefix and local_path and not local_path.lower().startswith(prefix):
            errors.append(f"{object_id}: local_path body ile uyumsuz -> {local_path}")

        if should_have_hash(row) and not (row.get("sha256") or "").strip():
            warnings.append(f"{object_id}: indirilebilir kayitta sha256 eksik")

        doi = (row.get("doi") or "").strip()
        source_url = (row.get("source_url") or "").strip()
        if "publications" in source_url.lower() and not doi:
            warnings.append(f"{object_id}: publication kaydinda doi bos")

        acquired_utc = (row.get("acquired_utc") or "").strip()
        if not acquired_utc:
            warnings.append(f"{object_id}: acquired_utc bos")

        if check_files and local_path:
            path = Path(local_path)
            if not path.exists() and should_have_hash(row):
                warnings.append(f"{object_id}: local_path diskte yok -> {local_path}")

    for field in ("object_id", "local_path"):
        duplicates = find_duplicates(rows, field)
        for value, object_ids in duplicates.items():
            errors.append(f"yinelenen {field}: {value} -> {', '.join(object_ids)}")

    source_product_duplicates = find_source_product_duplicates(rows)
    for value, object_ids in source_product_duplicates.items():
        errors.append(f"yinelenen source_url+product_id: {value} -> {', '.join(object_ids)}")

    return {"errors": errors, "warnings": warnings}


def print_report(report: Dict[str, List[str]]) -> int:
    errors = report["errors"]
    warnings = report["warnings"]

    print("Manifest Lint Raporu")
    print(f"ERROR   : {len(errors)}")
    print(f"WARNING : {len(warnings)}")

    if errors:
        print("\nErrors")
        for item in errors:
            print(f"- {item}")

    if warnings:
        print("\nWarnings")
        for item in warnings:
            print(f"- {item}")

    return 1 if errors else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manifest kalite kontrol raporu uretir")
    parser.add_argument("--manifest", default="veri_manifest_sablonu.csv", help="Manifest CSV yolu")
    parser.add_argument("--check-files", action="store_true", help="local_path alanlarini diskte kontrol et")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = read_manifest(Path(args.manifest))
    report = lint_rows(rows, check_files=args.check_files)
    return print_report(report)


if __name__ == "__main__":
    raise SystemExit(main())