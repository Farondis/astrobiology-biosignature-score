#!/usr/bin/env python3
"""Spektral ozet ve izotop referans verilerinden model girdisi ozellik vektorleri uretir.

Cikti: her spektrum/referans satiri icin S_remote, S_context, S_in_situ,
S_chem_iso hint degerleri ve tanimlanmis ozellikler.
"""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from statistics import fmean, stdev
from typing import Dict, List, Sequence


# ---------------------------------------------------------------------------
# Spectral feature computation
# ---------------------------------------------------------------------------

def parse_float_list(text: str) -> List[float]:
    """Virgul ayrili float string → list."""
    out: List[float] = []
    for token in text.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            v = float(token)
            if math.isfinite(v):
                out.append(v)
        except ValueError:
            continue
    return out


def spectral_slope(values: Sequence[float]) -> float:
    """Basit dogrusal regresyon egimi (en kucuk kareler)."""
    n = len(values)
    if n < 2:
        return 0.0
    x_mean = (n - 1) / 2.0
    y_mean = fmean(values)
    numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    if denominator == 0:
        return 0.0
    return numerator / denominator


def band_depth(values: Sequence[float]) -> float:
    """Continuum-removed band depth: 1 - (min / continuum).

    Continuum basitce ilk ve son deger ortalamasidir.
    """
    if len(values) < 3:
        return 0.0
    continuum = (values[0] + values[-1]) / 2.0
    if continuum <= 0:
        return 0.0
    min_val = min(values)
    depth = 1.0 - (min_val / continuum)
    return max(0.0, min(1.0, depth))


def absorption_center_index(values: Sequence[float]) -> int:
    """En derin absorpsiyon noktasinin indeksi (0-tabanli)."""
    if not values:
        return 0
    return int(values.index(min(values)))


def spectral_variability(values: Sequence[float]) -> float:
    """Standart sapma / ortalama (CV)."""
    if len(values) < 2:
        return 0.0
    mean = fmean(values)
    if mean == 0:
        return 0.0
    return stdev(values) / abs(mean)


def curvature_metric(values: Sequence[float]) -> float:
    """Ikinci turev ortalamasinin mutlak degeri — absorpsiyon keskinlik olcusu."""
    if len(values) < 3:
        return 0.0
    second_derivatives = [
        values[i + 1] - 2 * values[i] + values[i - 1]
        for i in range(1, len(values) - 1)
    ]
    return fmean(abs(d) for d in second_derivatives)


def extract_spectral_features(row: Dict[str, str]) -> Dict[str, str]:
    """Tek satirlik spectral_summary CSV satirindan ozellik cikar."""
    values = parse_float_list(row.get("first_n_values", ""))
    chapter = (row.get("chapter") or "").lower()

    slope = spectral_slope(values)
    depth = band_depth(values)
    abs_idx = absorption_center_index(values)
    variability = spectral_variability(values)
    curvature = curvature_metric(values)
    n_count = int(row.get("sample_count", "0") or "0")

    # Chapter-tabanli biyoiz hint skorlari
    is_organic = "organic" in chapter
    is_vegetation = "vegetation" in chapter
    is_coating = "coating" in chapter
    is_mineral = "mineral" in chapter
    is_bio_relevant = is_organic or is_vegetation

    # S_remote hint: guclu absorpsiyon + yuksek degiskenlik = ilginc
    s_remote_hint = min(1.0, depth * 1.5 + variability * 0.5)
    if is_bio_relevant:
        s_remote_hint = min(1.0, s_remote_hint + 0.15)

    # R_contam hint: kaplama veya mineral ise taklitci riski artar
    contam_hint = 0.0
    if is_coating:
        contam_hint = min(1.0, 0.3 + curvature * 2.0)
    if is_mineral and depth > 0.05:
        contam_hint = max(contam_hint, 0.2)

    return {
        "source_object_id": row.get("object_id", ""),
        "chapter": row.get("chapter", ""),
        "sample_file": row.get("sample_file", ""),
        "header": row.get("header", ""),
        "channel_count": str(n_count),
        "spectral_slope": f"{slope:.8f}",
        "band_depth": f"{depth:.6f}",
        "absorption_center_idx": str(abs_idx),
        "spectral_variability": f"{variability:.6f}",
        "curvature": f"{curvature:.8f}",
        "is_bio_relevant": str(int(is_bio_relevant)),
        "is_abiotic_mimic": str(int(is_coating or is_mineral)),
        "s_remote_hint": f"{s_remote_hint:.4f}",
        "contam_hint": f"{contam_hint:.4f}",
    }


# ---------------------------------------------------------------------------
# Isotope feature computation
# ---------------------------------------------------------------------------

# Published biotic range boundaries (per mil)
_BIOTIC_D13C_LOW = -45.0
_BIOTIC_D13C_HIGH = -20.0
_BIOTIC_D34S_LOW = -10.0
_BIOTIC_D34S_HIGH = +15.0
_BIOTIC_DD_LOW = -150.0
_BIOTIC_DD_HIGH = -30.0


def _isotope_biotic_score(value: float, low: float, high: float) -> float:
    """Deger biyotik araliga ne kadar yakin? 0-1 arasi."""
    if low <= value <= high:
        # Merkezden uzaklik azaldikca skor artar
        center = (low + high) / 2.0
        half_range = (high - low) / 2.0
        return 1.0 - abs(value - center) / half_range * 0.3
    # Aralik disinda: uzakliya gore duser
    if value < low:
        dist = low - value
    else:
        dist = value - high
    span = high - low
    return max(0.0, 1.0 - dist / span)


def extract_isotope_features(row: Dict[str, str]) -> Dict[str, str]:
    """Tek satirlik izotop referans CSV satirindan ozellik cikar."""
    d13c_str = (row.get("delta_13C_permil") or "").strip()
    d34s_str = (row.get("delta_34S_permil") or "").strip()
    dD_str = (row.get("delta_D_permil") or "").strip()

    scores: List[float] = []
    channels_available = 0

    d13c_score = 0.0
    d34s_score = 0.0
    dD_score = 0.0

    if d13c_str:
        try:
            d13c = float(d13c_str)
            d13c_score = _isotope_biotic_score(d13c, _BIOTIC_D13C_LOW, _BIOTIC_D13C_HIGH)
            scores.append(d13c_score)
            channels_available += 1
        except ValueError:
            pass

    if d34s_str:
        try:
            d34s = float(d34s_str)
            d34s_score = _isotope_biotic_score(d34s, _BIOTIC_D34S_LOW, _BIOTIC_D34S_HIGH)
            scores.append(d34s_score)
            channels_available += 1
        except ValueError:
            pass

    if dD_str:
        try:
            dD = float(dD_str)
            dD_score = _isotope_biotic_score(dD, _BIOTIC_DD_LOW, _BIOTIC_DD_HIGH)
            scores.append(dD_score)
            channels_available += 1
        except ValueError:
            pass

    s_chem_iso_hint = fmean(scores) if scores else 0.0
    missing_channels = 3 - channels_available

    context_label = (row.get("context") or "").lower()
    is_abiotic_context = any(w in context_label for w in ("evaporite", "synthetic", "abiotic", "fischer"))

    contam_hint = 0.0
    if is_abiotic_context and s_chem_iso_hint > 0.5:
        contam_hint = min(1.0, s_chem_iso_hint * 0.6)

    return {
        "sample_id": row.get("sample_id", ""),
        "location": row.get("location", ""),
        "instrument": row.get("instrument", ""),
        "context": row.get("context", ""),
        "d13c_score": f"{d13c_score:.4f}",
        "d34s_score": f"{d34s_score:.4f}",
        "dD_score": f"{dD_score:.4f}",
        "channels_available": str(channels_available),
        "missing_channels": str(missing_channels),
        "s_chem_iso_hint": f"{s_chem_iso_hint:.4f}",
        "contam_hint": f"{contam_hint:.4f}",
        "is_abiotic_context": str(int(is_abiotic_context)),
    }


# ---------------------------------------------------------------------------
# Aggregate features → region-level score hints
# ---------------------------------------------------------------------------

def aggregate_spectral_hints(features: List[Dict[str, str]]) -> Dict[str, float]:
    """Tum spektral ozelliklerden bolge-seviyesi hint uret."""
    if not features:
        return {"s_remote": 0.0, "contam_spectral": 0.0, "bio_ratio": 0.0, "n_spectra": 0}

    s_remote_vals = [float(f["s_remote_hint"]) for f in features]
    contam_vals = [float(f["contam_hint"]) for f in features]
    bio_count = sum(int(f["is_bio_relevant"]) for f in features)

    return {
        "s_remote": min(1.0, fmean(sorted(s_remote_vals, reverse=True)[:10])),
        "contam_spectral": fmean(contam_vals),
        "bio_ratio": bio_count / len(features),
        "n_spectra": len(features),
    }


def aggregate_isotope_hints(features: List[Dict[str, str]]) -> Dict[str, float]:
    """Tum izotop ozelliklerden bolge-seviyesi hint uret."""
    if not features:
        return {"s_chem_iso": 0.0, "contam_isotope": 0.0, "missing_channels": 3}

    chem_vals = [float(f["s_chem_iso_hint"]) for f in features if not int(f.get("is_abiotic_context", "0"))]
    contam_vals = [float(f["contam_hint"]) for f in features]
    missing = min(int(f["missing_channels"]) for f in features)

    return {
        "s_chem_iso": fmean(chem_vals) if chem_vals else 0.0,
        "contam_isotope": fmean(contam_vals),
        "missing_channels": missing,
    }


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------

def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[Dict[str, str]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Spektral ozet + izotop referansindan model giris ozellikleri uretir"
    )
    p.add_argument(
        "--spectral-csv",
        default="raw/earth/usgs_splib07/usgs_spectral_summary.csv",
        help="spectral_summary.py ciktisi",
    )
    p.add_argument(
        "--isotope-csv",
        default="raw/mars/reference/mars_isotope_reference_values.csv",
        help="Izotop referans tablosu CSV",
    )
    p.add_argument(
        "--output-spectral",
        default="features_spectral.csv",
        help="Uretilecek spektral ozellik CSV",
    )
    p.add_argument(
        "--output-isotope",
        default="features_isotope.csv",
        help="Uretilecek izotop ozellik CSV",
    )
    p.add_argument(
        "--output-aggregate",
        default="features_aggregate.csv",
        help="Bolge-seviyesi toplu ozellik CSV",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Islenecek maks spektral satir (0 = sinirsiz)",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()

    # --- Spectral features ---
    spectral_features: List[Dict[str, str]] = []
    spectral_csv = Path(args.spectral_csv)
    if spectral_csv.exists():
        rows = read_csv(spectral_csv)
        if args.limit > 0:
            rows = rows[: args.limit]
        for row in rows:
            spectral_features.append(extract_spectral_features(row))
        print(f"Spektral ozellik: {len(spectral_features)} satir")
    else:
        print(f"UYARI: {spectral_csv} bulunamadi, spektral ozellik cikarilmadi.")

    # --- Isotope features ---
    isotope_features: List[Dict[str, str]] = []
    isotope_csv = Path(args.isotope_csv)
    if isotope_csv.exists():
        for row in read_csv(isotope_csv):
            isotope_features.append(extract_isotope_features(row))
        print(f"Izotop ozellik : {len(isotope_features)} satir")
    else:
        print(f"UYARI: {isotope_csv} bulunamadi, izotop ozellik cikarilmadi.")

    # --- Write per-item features ---
    if spectral_features:
        sf = list(spectral_features[0].keys())
        write_csv(Path(args.output_spectral), spectral_features, sf)
        print(f"  → {args.output_spectral}")

    if isotope_features:
        iso_f = list(isotope_features[0].keys())
        write_csv(Path(args.output_isotope), isotope_features, iso_f)
        print(f"  → {args.output_isotope}")

    # --- Aggregate ---
    spectral_agg = aggregate_spectral_hints(spectral_features)
    isotope_agg = aggregate_isotope_hints(isotope_features)

    agg_row = {
        "s_remote_hint": f"{spectral_agg['s_remote']:.4f}",
        "s_chem_iso_hint": f"{isotope_agg['s_chem_iso']:.4f}",
        "contam_spectral": f"{spectral_agg['contam_spectral']:.4f}",
        "contam_isotope": f"{isotope_agg['contam_isotope']:.4f}",
        "bio_ratio": f"{spectral_agg['bio_ratio']:.4f}",
        "n_spectra": str(spectral_agg["n_spectra"]),
        "isotope_missing_channels": str(isotope_agg["missing_channels"]),
    }
    agg_fields = list(agg_row.keys())
    write_csv(Path(args.output_aggregate), [agg_row], agg_fields)
    print(f"  → {args.output_aggregate}")

    # --- Summary to stdout ---
    print("\n--- Toplu Ozellik Ozeti ---")
    print(f"  S_remote hint        : {spectral_agg['s_remote']:.4f}")
    print(f"  S_chem_iso hint      : {isotope_agg['s_chem_iso']:.4f}")
    print(f"  Contam (spektral)    : {spectral_agg['contam_spectral']:.4f}")
    print(f"  Contam (izotop)      : {isotope_agg['contam_isotope']:.4f}")
    print(f"  Bio-relevant oran    : {spectral_agg['bio_ratio']:.4f}")
    print(f"  Toplam spektrum      : {spectral_agg['n_spectra']}")
    print(f"  Izotop eksik kanal   : {isotope_agg['missing_channels']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
