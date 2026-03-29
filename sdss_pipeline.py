#!/usr/bin/env python3
"""SDSS DR17 lite FITS spektrum okuyucu ve S_remote pipeline entegrasyonu.

Stdlib-only minimal FITS binary-table parser ile SDSS spektrumlarini okur,
feature_extractor fonksiyonlariyla ozellik cikarir ve pipeline uyumlu CSV uretir.

Kullanim:
    python sdss_pipeline.py                           # varsayilan: raw/telescope/sdss/
    python sdss_pipeline.py --fits-dir raw/telescope/sdss/ --output sdss_features.csv
    python sdss_pipeline.py --json                    # JSON cikti
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import struct
import sys
from pathlib import Path
from statistics import fmean, stdev
from typing import Dict, List, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# Minimal FITS Reader (stdlib only)
# ---------------------------------------------------------------------------

FITS_BLOCK = 2880
FITS_CARD = 80


def _read_header(fobj) -> Tuple[Dict[str, str], int]:
    """FITS header bloklarini oku, keyword-value dict dondur."""
    cards: Dict[str, str] = {}
    n_blocks = 0
    while True:
        block = fobj.read(FITS_BLOCK)
        if len(block) < FITS_BLOCK:
            break
        n_blocks += 1
        for i in range(0, FITS_BLOCK, FITS_CARD):
            card = block[i : i + FITS_CARD].decode("ascii", "replace")
            key = card[:8].strip()
            if key == "END":
                return cards, n_blocks * FITS_BLOCK
            if "=" in card[8:10]:
                raw = card[10:].split("/")[0].strip()
                if raw.startswith("'"):
                    raw = raw.strip("'").strip()
                cards[key] = raw
    return cards, n_blocks * FITS_BLOCK


def _parse_int(v: str) -> int:
    return int(v.strip())


def _parse_tform(tform: str) -> Tuple[int, str, int]:
    """FITS TFORMn -> (count, type_char, byte_size)."""
    tform = tform.strip()
    # Parse repeat count
    i = 0
    while i < len(tform) and tform[i].isdigit():
        i += 1
    count = int(tform[:i]) if i > 0 else 1
    tc = tform[i] if i < len(tform) else "B"
    sizes = {"L": 1, "B": 1, "I": 2, "J": 4, "K": 8, "E": 4, "D": 8, "A": 1}
    return count, tc, sizes.get(tc, 1) * count


def read_fits_bintable(path: str, hdu_index: int = 1) -> Tuple[Dict[str, str], Dict[str, List]]:
    """FITS dosyasindan belirtilen HDU'deki binary table'i oku.

    Returns: (header_dict, column_dict)
    """
    with open(path, "rb") as f:
        # Skip HDUs until target
        for _ in range(hdu_index):
            hdr, hdr_bytes = _read_header(f)
            naxis = _parse_int(hdr.get("NAXIS", "0"))
            if naxis == 0:
                continue
            data_bytes = 1
            for ax in range(1, naxis + 1):
                data_bytes *= _parse_int(hdr.get(f"NAXIS{ax}", "1"))
            data_bytes = abs(_parse_int(hdr.get("BITPIX", "8"))) // 8 * (data_bytes if naxis > 0 else 0)
            # Actually for extensions, BITPIX*GCOUNT*NAXIS1*NAXIS2...
            # But simpler: total = product of NAXISn * |BITPIX|/8
            if "GCOUNT" in hdr:
                data_bytes *= _parse_int(hdr.get("GCOUNT", "1"))
            # Pad to 2880-byte boundary
            pad = (FITS_BLOCK - data_bytes % FITS_BLOCK) % FITS_BLOCK
            f.seek(data_bytes + pad, 1)

        # Read target HDU header
        hdr, _ = _read_header(f)
        naxis1 = _parse_int(hdr.get("NAXIS1", "0"))  # row width bytes
        naxis2 = _parse_int(hdr.get("NAXIS2", "0"))  # n rows
        tfields = _parse_int(hdr.get("TFIELDS", "0"))

        # Parse columns
        col_info = []  # (name, count, type_char, byte_size)
        for i in range(1, tfields + 1):
            name = hdr.get(f"TTYPE{i}", f"col{i}").strip()
            tform = hdr.get(f"TFORM{i}", "E")
            count, tc, bsz = _parse_tform(tform)
            col_info.append((name, count, tc, bsz))

        # Initialize columns
        columns: Dict[str, List] = {ci[0]: [] for ci in col_info}

        # Read rows
        data = f.read(naxis1 * naxis2)
        for row_idx in range(naxis2):
            offset = row_idx * naxis1
            for name, count, tc, bsz in col_info:
                chunk = data[offset : offset + bsz]
                offset += bsz
                if tc == "E":  # 32-bit float big-endian
                    vals = struct.unpack(f">{count}f", chunk)
                    columns[name].append(vals[0] if count == 1 else list(vals))
                elif tc == "D":  # 64-bit float
                    vals = struct.unpack(f">{count}d", chunk)
                    columns[name].append(vals[0] if count == 1 else list(vals))
                elif tc == "J":  # 32-bit int
                    vals = struct.unpack(f">{count}i", chunk)
                    columns[name].append(vals[0] if count == 1 else list(vals))
                elif tc == "K":  # 64-bit int
                    vals = struct.unpack(f">{count}q", chunk)
                    columns[name].append(vals[0] if count == 1 else list(vals))
                elif tc == "I":  # 16-bit int
                    vals = struct.unpack(f">{count}h", chunk)
                    columns[name].append(vals[0] if count == 1 else list(vals))
                elif tc == "A":  # ASCII string
                    columns[name].append(chunk.decode("ascii", "replace").strip())
                else:
                    columns[name].append(None)

    return hdr, columns


# ---------------------------------------------------------------------------
# Spectral feature computation (adapted from feature_extractor.py)
# ---------------------------------------------------------------------------

def spectral_slope(values: Sequence[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    x_mean = (n - 1) / 2.0
    y_mean = fmean(values)
    num = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
    den = sum((i - x_mean) ** 2 for i in range(n))
    return num / den if den != 0 else 0.0


def band_depth(values: Sequence[float]) -> float:
    if len(values) < 3:
        return 0.0
    continuum = [values[0] + (values[-1] - values[0]) * i / (len(values) - 1)
                 for i in range(len(values))]
    depths = [c - v for c, v in zip(continuum, values) if c != 0]
    return max(depths) / max(abs(values[0]), abs(values[-1]), 1e-30) if depths else 0.0


def spectral_variability(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = fmean(values)
    return stdev(values) / abs(m) if abs(m) > 1e-30 else 0.0


def curvature_metric(values: Sequence[float]) -> float:
    if len(values) < 3:
        return 0.0
    d2 = [values[i + 1] - 2 * values[i] + values[i - 1] for i in range(1, len(values) - 1)]
    return fmean([abs(x) for x in d2])


def compute_s_remote(flux: List[float]) -> Dict[str, float]:
    """SDSS flux dizisinden S_remote ozelliklerini hesapla."""
    clean = [v for v in flux if math.isfinite(v) and abs(v) < 1e10]
    if len(clean) < 10:
        return {"slope": 0.0, "band_depth": 0.0, "variability": 0.0,
                "curvature": 0.0, "s_remote_hint": 0.0}

    sl = spectral_slope(clean)
    bd = band_depth(clean)
    var = spectral_variability(clean)
    curv = curvature_metric(clean)

    # S_remote hint: yukaridaki ozelliklerin normalize edilmis bilesimi
    hint = min(1.0, bd * 1.5 + var * 0.3 + min(abs(sl), 1.0) * 0.2)
    return {
        "slope": sl,
        "band_depth": bd,
        "variability": var,
        "curvature": curv,
        "s_remote_hint": hint,
    }


# ---------------------------------------------------------------------------
# SDSS metadata extraction
# ---------------------------------------------------------------------------

def extract_sdss_metadata(hdr: Dict[str, str]) -> Dict[str, str]:
    """FITS headerindan SDSS metadatasi cikar."""
    return {
        "plate": hdr.get("PLATEID", hdr.get("PLATE", "")),
        "mjd": hdr.get("MJD", ""),
        "fiberid": hdr.get("FIBERID", ""),
        "ra": hdr.get("PLUG_RA", hdr.get("RA", "")),
        "dec": hdr.get("PLUG_DEC", hdr.get("DEC", "")),
        "z": hdr.get("Z", ""),
        "class": hdr.get("CLASS", hdr.get("OBJTYPE", "")),
        "subclass": hdr.get("SUBCLASS", ""),
    }


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def process_fits_file(fits_path: str) -> Optional[Dict]:
    """Tek bir SDSS FITS dosyasini isle."""
    fname = os.path.basename(fits_path)
    try:
        hdr, cols = read_fits_bintable(fits_path, hdu_index=1)
    except Exception as e:
        print(f"  HATA: {fname}: {e}", file=sys.stderr)
        return None

    flux = cols.get("flux", cols.get("FLUX", []))
    loglam = cols.get("loglam", cols.get("LOGLAM", []))

    if not flux:
        print(f"  UYARI: {fname}: flux kolonu bulunamadi", file=sys.stderr)
        return None

    # Dalga boyu hesapla
    wavelengths = [10 ** ll for ll in loglam] if loglam else []

    # Ozellik cikar
    features = compute_s_remote(flux)

    # Metadata
    meta = extract_sdss_metadata(hdr)

    # Dalga boyu araligi
    wl_min = min(wavelengths) if wavelengths else 0
    wl_max = max(wavelengths) if wavelengths else 0

    return {
        "file": fname,
        "plate": meta["plate"],
        "mjd": meta["mjd"],
        "fiberid": meta["fiberid"],
        "ra": meta["ra"],
        "dec": meta["dec"],
        "redshift": meta["z"],
        "obj_class": meta["class"],
        "n_pixels": len(flux),
        "wl_min_A": f"{wl_min:.1f}",
        "wl_max_A": f"{wl_max:.1f}",
        "flux_mean": f"{fmean(flux):.4f}" if flux else "0",
        "slope": f"{features['slope']:.6f}",
        "band_depth": f"{features['band_depth']:.4f}",
        "variability": f"{features['variability']:.4f}",
        "curvature": f"{features['curvature']:.6f}",
        "s_remote_hint": f"{features['s_remote_hint']:.4f}",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="SDSS FITS → S_remote pipeline")
    parser.add_argument("--fits-dir", default="raw/telescope/sdss/",
                        help="FITS dosyalarinin dizini")
    parser.add_argument("--output", default="sdss_features.csv",
                        help="Cikti CSV dosyasi")
    parser.add_argument("--json", action="store_true",
                        help="JSON formatinda cikti")
    args = parser.parse_args()

    fits_dir = Path(args.fits_dir)
    if not fits_dir.exists():
        print(f"HATA: {fits_dir} bulunamadi", file=sys.stderr)
        return 1

    fits_files = sorted(fits_dir.glob("*.fits"))
    if not fits_files:
        print(f"UYARI: {fits_dir} icinde FITS dosyasi bulunamadi", file=sys.stderr)
        return 1

    print(f"SDSS Pipeline: {len(fits_files)} FITS dosyasi isleniyor...")
    results: List[Dict] = []

    for fp in fits_files:
        result = process_fits_file(str(fp))
        if result:
            results.append(result)
            hint = float(result["s_remote_hint"])
            label = "Yuksek" if hint >= 0.60 else "Orta" if hint >= 0.35 else "Dusuk"
            print(f"  {result['file']}: S_remote={result['s_remote_hint']} [{label}]"
                  f"  z={result['redshift']}  class={result['obj_class']}")

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        if results:
            fieldnames = list(results[0].keys())
            out_path = Path(args.output)
            with out_path.open("w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=fieldnames)
                w.writeheader()
                w.writerows(results)
            print(f"\n=> {args.output} ({len(results)} satir)")

    # Aggregate S_remote for the scoring model
    if results:
        hints = [float(r["s_remote_hint"]) for r in results]
        top10 = sorted(hints, reverse=True)[:10]
        agg = min(1.0, fmean(top10))
        print(f"\n--- SDSS Toplu S_remote ---")
        print(f"  Toplam spektrum  : {len(results)}")
        print(f"  Ort S_remote     : {fmean(hints):.4f}")
        print(f"  Max S_remote     : {max(hints):.4f}")
        print(f"  Top-10 ort       : {agg:.4f}")
        print(f"  Pipeline giris   : S_remote = {agg:.4f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
