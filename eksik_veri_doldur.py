#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple
from urllib.parse import urlparse

from manifest_downloader import download_with_resume, read_manifest, resolve_download_url


def load_rows(path: Path) -> List[Dict[str, str]]:
    return read_manifest(path)


def write_rows(path: Path, rows: List[Dict[str, str]]) -> None:
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def row_matches(row: Dict[str, str], category: str) -> bool:
    object_id = (row.get("object_id") or "").upper()
    if category == "all":
        return True
    if category == "telescope":
        return object_id.startswith("TELESKOP-")
    if category == "rover":
        return object_id.startswith("ROVER-")
    return False


def local_file_state(row: Dict[str, str]) -> Tuple[Path | None, bool, bool]:
    local_path = (row.get("local_path") or "").strip()
    if not local_path:
        return None, False, False
    path = Path(local_path)
    exists = path.exists()
    has_hash = bool((row.get("sha256") or "").strip())
    return path, exists, has_hash


def missing_rows(rows: Iterable[Dict[str, str]], category: str) -> List[Dict[str, str]]:
    selected: List[Dict[str, str]] = []
    for row in rows:
        if not row_matches(row, category):
            continue
        _, exists, has_hash = local_file_state(row)
        if not exists or not has_hash:
            selected.append(row)
    return selected


def next_rover_id(rows: List[Dict[str, str]]) -> str:
    numbers = []
    for row in rows:
        object_id = (row.get("object_id") or "").strip()
        if object_id.startswith("ROVER-"):
            try:
                numbers.append(int(object_id.split("-", 1)[1]))
            except ValueError:
                pass
    return f"ROVER-{(max(numbers) if numbers else 0) + 1:03d}"


def parse_rover_feed_line(line: str) -> Tuple[str, Dict[str, str], str] | None:
    if not line or line.startswith("#") or "|http" not in line:
        return None

    parts = line.split("|", 2)
    if len(parts) != 3:
        return None

    timestamp, raw_meta, url = (part.strip() for part in parts)
    metadata: Dict[str, str] = {}
    if raw_meta:
        try:
            parsed = ast.literal_eval(raw_meta)
            if isinstance(parsed, dict):
                metadata = {str(key): str(value) for key, value in parsed.items()}
        except (SyntaxError, ValueError):
            metadata = {"raw_meta": raw_meta}

    return timestamp, metadata, url


def normalize_rover_instrument(value: str) -> str:
    aliases = {
        "SHERLOC_WATSON": "SHERLOC_WATSON",
        "SHERLOC_CONTEXT": "SHERLOC_CONTEXT",
        "MASTCAM_Z": "MASTCAM_Z",
        "SUPERCAM_RMI": "SUPERCAM_RMI",
        "SUPERCAM": "SUPERCAM",
        "PIXL_MCC": "PIXL_MCC",
        "PIXL": "PIXL",
        "SRLC": "SHERLOC_CONTEXT",
        "SHRLC": "SHERLOC_WATSON",
        "ZCAM": "MASTCAM_Z",
        "SCAM": "SUPERCAM_RMI",
        "PIXL_CAM": "PIXL_MCC",
    }
    key = value.strip().upper()
    return aliases.get(key, key or "UNKNOWN")


def infer_instrument_from_url(url: str, metadata: Dict[str, str]) -> str:
    meta_instrument = normalize_rover_instrument(metadata.get("instrument", ""))
    if meta_instrument != "UNKNOWN":
        return meta_instrument

    folder = Path(urlparse(url).path).parent.name.lower()
    instrument_map = {
        "shrlc": "SHERLOC_WATSON",
        "srlc": "SHERLOC_CONTEXT",
        "zcam": "MASTCAM_Z",
        "scam": "SUPERCAM_RMI",
        "pixl": "PIXL_MCC",
    }
    return instrument_map.get(folder, folder.upper() or "UNKNOWN")


def infer_level_from_url(url: str) -> str:
    match = re.search(r"/ids/([^/]+)/", urlparse(url).path.lower())
    if match:
        return match.group(1).upper()
    return "EDR"


def source_timestamp_to_utc(timestamp: str) -> str:
    if re.match(r"^\d{4}-\d{2}-\d{2}t\d{2}:\d{2}:\d{2}", timestamp.lower()):
        return timestamp
    return ""


def build_rover_notes(feed_name: str, timestamp: str, metadata: Dict[str, str]) -> str:
    detail_parts = [f"source={feed_name}"]
    if timestamp:
        detail_parts.append(f"timestamp={timestamp}")
    filter_name = metadata.get("filter_name", "").strip()
    if filter_name:
        detail_parts.append(f"filter={filter_name}")
    camera_type = metadata.get("camera_model_type", "").strip()
    if camera_type:
        detail_parts.append(f"camera_model={camera_type}")
    return "Added from rover feed (" + ", ".join(detail_parts) + ")"


def is_ingestable_rover_url(url: str, metadata: Dict[str, str] | None = None) -> bool:
    lower_url = url.lower()
    parsed = urlparse(url)
    metadata = metadata or {}

    if metadata.get("entry_type", "").strip().upper() == "ARCHIVE_REF":
        return False
    if parsed.scheme not in {"http", "https"}:
        return False
    if parsed.netloc.lower() != "mars.nasa.gov":
        return False
    if "/mars2020-raw-images/" not in lower_url or "/browse/" not in lower_url:
        return False

    archive_markers = (
        "collection_",
        "bundle",
        "readme.txt",
        "context-pds4",
        "inventory.csv",
        ".lblx.xml",
        ".xml",
        ".csv",
        "/document/",
    )
    if any(marker in lower_url for marker in archive_markers):
        return False

    return lower_url.endswith((".png", ".jpg", ".jpeg"))


def ingest_rover_feed(rows: List[Dict[str, str]], feed_path: Path) -> int:
    if not feed_path.exists():
        return 0

    existing_urls = {(row.get("source_url") or "").strip() for row in rows}
    added = 0
    for line in feed_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        parsed = parse_rover_feed_line(line)
        if not parsed:
            continue
        timestamp, metadata, url = parsed
        if not url or url in existing_urls or not is_ingestable_rover_url(url, metadata):
            continue

        filename = Path(url).name
        folder = Path(url).parent.name.lower()
        instrument = infer_instrument_from_url(url, metadata)
        local_path = f"raw/mars/perseverance/{folder}/{filename}"
        rows.append(
            {
                "object_id": next_rover_id(rows),
                "body": "Mars",
                "mission": "Mars 2020 Perseverance",
                "instrument": instrument,
                "product_id": filename,
                "level": infer_level_from_url(url),
                "acquired_utc": source_timestamp_to_utc(timestamp),
                "doi": "",
                "source_url": url,
                "sha256": "",
                "local_path": local_path,
                "notes": build_rover_notes(feed_path.name, timestamp, metadata),
            }
        )
        existing_urls.add(url)
        added += 1
    return added


def main() -> int:
    parser = argparse.ArgumentParser(description="Eksik rover ve teleskop verilerini doldur")
    parser.add_argument("--manifest", default="veri_manifest_sablonu.csv", help="Manifest CSV yolu")
    parser.add_argument("--category", choices=["all", "rover", "telescope"], default="all")
    parser.add_argument("--download", action="store_true", help="Eksik dosyalari indir")
    parser.add_argument("--update-checksums", action="store_true", help="Mevcut/indirilen dosyalar icin SHA256 yaz")
    parser.add_argument("--ingest-rover-feed", default="rover_latest_urls.txt", help="Yeni rover URL listesini manifest'e ekle")
    parser.add_argument("--timeout", type=int, default=60, help="HTTP timeout saniye")
    parser.add_argument("--limit", type=int, default=0, help="Islenecek maksimum satir sayisi")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    rows = load_rows(manifest_path)

    added = ingest_rover_feed(rows, Path(args.ingest_rover_feed)) if args.ingest_rover_feed else 0
    targets = missing_rows(rows, args.category)
    if args.limit > 0:
        targets = targets[: args.limit]

    print(f"Manifest girdisi eklendi: {added}")
    print(f"Eksik satir sayisi: {len(targets)}")

    downloaded = 0
    failed = 0
    updated = 0

    for row in targets:
        object_id = row.get("object_id") or "?"
        local_path, exists, has_hash = local_file_state(row)
        if local_path is None:
            print(f"[{object_id}] SKIP - local_path yok")
            continue

        if args.download and not exists:
            url, reason = resolve_download_url(row, timeout=args.timeout)
            if not url:
                print(f"[{object_id}] FAIL - {reason}")
                failed += 1
                continue
            success, message = download_with_resume(url, local_path, timeout=args.timeout)
            if not success:
                print(f"[{object_id}] FAIL - {message}")
                failed += 1
                continue
            print(f"[{object_id}] OK - indirildi")
            downloaded += 1
            exists = True

        if args.update_checksums and exists and (not has_hash or args.download):
            row["sha256"] = sha256_file(local_path)
            updated += 1
            print(f"[{object_id}] HASH - guncellendi")

    if added or updated:
        write_rows(manifest_path, rows)

    print("\nOzet")
    print(f"Eklendi     : {added}")
    print(f"Indirildi   : {downloaded}")
    print(f"Hash        : {updated}")
    print(f"Basarisiz   : {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())