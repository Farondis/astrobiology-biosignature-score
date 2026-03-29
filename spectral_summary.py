#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from statistics import fmean
from typing import Dict, Iterable, List, Sequence
import zipfile


def read_manifest(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="USGS spectral zip paketlerinden ozet CSV uretir")
    parser.add_argument("--manifest", default="veri_manifest_sablonu.csv", help="Manifest CSV yolu")
    parser.add_argument(
        "--object-ids",
        default="EARTH-010,EARTH-011,EARTH-012",
        help="Virgulle ayrilmis object_id listesi",
    )
    parser.add_argument(
        "--output",
        default="raw/earth/usgs_splib07/usgs_spectral_summary.csv",
        help="Uretilecek CSV dosyasi",
    )
    parser.add_argument(
        "--first-n",
        type=int,
        default=9,
        help="Erken kanal ozetinde kac deger kullanilacagi",
    )
    parser.add_argument(
        "--chapter-contains",
        default="",
        help="Sadece chapter adinda gecen parcaya gore filtrele",
    )
    parser.add_argument(
        "--limit-per-archive",
        type=int,
        default=0,
        help="Her zip icin islenecek maksimum spektrum sayisi (0 = sinirsiz)",
    )
    return parser.parse_args()


def selected_rows(rows: Iterable[Dict[str, str]], object_ids: Sequence[str]) -> List[Dict[str, str]]:
    wanted = {item.strip().upper() for item in object_ids if item.strip()}
    selected: List[Dict[str, str]] = []
    for row in rows:
        object_id = (row.get("object_id") or "").strip().upper()
        local_path = (row.get("local_path") or "").strip()
        if object_id in wanted and local_path.lower().endswith(".zip"):
            selected.append(row)
    return selected


def parse_spectrum_text(text: str) -> tuple[str, List[float]]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "", []

    header = lines[0]
    values: List[float] = []
    for line in lines[1:]:
        try:
            value = float(line)
        except ValueError:
            continue
        if not math.isfinite(value):
            continue
        if abs(value) > 1e20:
            continue
        values.append(value)
    return header, values


def sparkline(values: Sequence[float]) -> str:
    if not values:
        return ""

    scale = ".-:=+*#%@"
    minimum = min(values)
    maximum = max(values)
    span = maximum - minimum
    if span == 0:
        return scale[0] * len(values)

    chars = []
    top = len(scale) - 1
    for value in values:
        index = int((value - minimum) / span * top)
        if index < 0:
            index = 0
        elif index > top:
            index = top
        chars.append(scale[index])
    return " ".join(chars)


def summarize_values(values: Sequence[float], first_n: int) -> Dict[str, str]:
    first_slice = list(values[:first_n])
    first_count = len(first_slice)
    first_value = first_slice[0] if first_slice else ""
    nth_value = first_slice[-1] if first_slice else ""
    first_delta = (first_slice[-1] - first_slice[0]) if len(first_slice) >= 2 else ""

    return {
        "sample_count": str(len(values)),
        "first_n_count": str(first_count),
        "first_value": format_float(values[0]) if values else "",
        "n_value": format_float(nth_value) if nth_value != "" else "",
        "last_value": format_float(values[-1]) if values else "",
        "global_min": format_float(min(values)) if values else "",
        "global_max": format_float(max(values)) if values else "",
        "global_mean": format_float(fmean(values)) if values else "",
        "first_n_min": format_float(min(first_slice)) if first_slice else "",
        "first_n_max": format_float(max(first_slice)) if first_slice else "",
        "first_n_delta": format_float(first_delta) if first_delta != "" else "",
        "first_n_trace": sparkline(first_slice),
        "first_n_values": ", ".join(format_float(value) for value in first_slice),
    }


def format_float(value: float) -> str:
    return f"{value:.6f}"


def iter_zip_rows(row: Dict[str, str], first_n: int, chapter_contains: str, limit_per_archive: int) -> List[Dict[str, str]]:
    zip_path = Path((row.get("local_path") or "").strip())
    if not zip_path.exists():
        raise FileNotFoundError(f"Zip bulunamadi: {zip_path}")

    lowered_chapter_filter = chapter_contains.strip().lower()
    produced: List[Dict[str, str]] = []
    with zipfile.ZipFile(zip_path) as archive:
        txt_names = [name for name in archive.namelist() if name.lower().endswith(".txt")]
        for name in txt_names:
            parts = Path(name).parts
            chapter = parts[1] if len(parts) >= 3 else ""
            if lowered_chapter_filter and lowered_chapter_filter not in chapter.lower():
                continue

            header, values = parse_spectrum_text(archive.read(name).decode("utf-8", errors="replace"))
            if not values:
                continue

            summary = summarize_values(values, first_n)
            produced.append(
                {
                    "object_id": row.get("object_id") or "",
                    "mission": row.get("mission") or "",
                    "instrument": row.get("instrument") or "",
                    "product_id": row.get("product_id") or "",
                    "zip_path": str(zip_path).replace("\\", "/"),
                    "chapter": chapter,
                    "member_path": name,
                    "sample_file": Path(name).name,
                    "header": header,
                    **summary,
                }
            )

            if limit_per_archive > 0 and len(produced) >= limit_per_archive:
                break

    return produced


def write_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    if not rows:
        raise ValueError("Yazilacak ozet satiri yok")

    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    manifest_rows = read_manifest(Path(args.manifest))
    object_ids = [item.strip() for item in args.object_ids.split(",") if item.strip()]
    targets = selected_rows(manifest_rows, object_ids)
    if not targets:
        print("Hedef spektral zip satiri bulunamadi")
        return 2

    all_rows: List[Dict[str, str]] = []
    for row in targets:
        archive_rows = iter_zip_rows(
            row,
            first_n=args.first_n,
            chapter_contains=args.chapter_contains,
            limit_per_archive=args.limit_per_archive,
        )
        all_rows.extend(archive_rows)
        print(f"[{row.get('object_id', '?')}] ozet satiri: {len(archive_rows)}")

    if not all_rows:
        print("Filtrelerden sonra ozetlenecek spektrum kalmadi")
        return 3

    output_path = Path(args.output)
    write_csv(output_path, all_rows)
    print(f"CSV yazildi: {output_path}")
    print(f"Toplam ozet satiri: {len(all_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())