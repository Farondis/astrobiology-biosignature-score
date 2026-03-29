#!/usr/bin/env python3
"""Uctan uca biyo-iz pipeline: ozellik cikarma → puanlama → belirsizlik → rapor.

Bu araç feature_extractor ve score_evidence modüllerini birbirine baglar.
Insan-girisli boşluk olmadan manifest verisinden nihai skor uretir.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List, Optional

from feature_extractor import (
    aggregate_isotope_hints,
    aggregate_spectral_hints,
    extract_isotope_features,
    extract_spectral_features,
    read_csv,
)
from score_evidence import (
    EvidenceInput,
    calibrate_scores,
    monte_carlo_uncertainty,
    sensitivity_analysis,
    validate_input,
)


# ---------------------------------------------------------------------------
# Config — default context assumptions when data is not available
# ---------------------------------------------------------------------------

_DEFAULT_CONTEXT_SCORE = 0.50  # jeolojik baglam bilinmediginde varsayilan
_DEFAULT_MORPHOLOGY = 0.0
_DEFAULT_SPECTRAL = 0.0
_DEFAULT_CHEMISTRY = 0.0


# ---------------------------------------------------------------------------
# Pipeline core
# ---------------------------------------------------------------------------

def build_evidence_from_features(
    spectral_agg: Dict[str, float],
    isotope_agg: Dict[str, float],
    context_override: Optional[float] = None,
    in_situ_override: Optional[float] = None,
    morphology_override: Optional[float] = None,
) -> EvidenceInput:
    """Toplanan ozellik hintlerinden EvidenceInput olustur."""

    s_remote = spectral_agg.get("s_remote", 0.0)
    s_chem_iso = isotope_agg.get("s_chem_iso", 0.0)
    bio_ratio = spectral_agg.get("bio_ratio", 0.0)
    contam_spectral = spectral_agg.get("contam_spectral", 0.0)
    contam_isotope = isotope_agg.get("contam_isotope", 0.0)
    missing = int(isotope_agg.get("missing_channels", 3))

    # Spectral analog uyumu: bio-relevant oran
    spectral_analog = min(1.0, bio_ratio * 2.0)

    # Kimyasal analog: izotop skoru
    chemistry_analog = min(1.0, s_chem_iso * 1.3) if s_chem_iso > 0.1 else 0.0

    # Kontaminasyon: spectral + isotope
    contam = min(1.0, contam_spectral + contam_isotope)

    # Abiyotik risk: kaplama/mineral oranina gore
    abiotic_risk = contam_spectral

    # Context: override veya varsayilan
    context = context_override if context_override is not None else _DEFAULT_CONTEXT_SCORE

    # In-situ: override veya spectral-tabanli yakinsama
    in_situ = in_situ_override if in_situ_override is not None else min(1.0, s_remote * 0.5)

    # Morfoloji: override veya varsayilan
    morphology = morphology_override if morphology_override is not None else _DEFAULT_MORPHOLOGY

    return EvidenceInput(
        remote=s_remote,
        context=context,
        in_situ=in_situ,
        chem_iso=s_chem_iso,
        contam=contam,
        morphology_analog=morphology,
        spectral_analog=spectral_analog,
        chemistry_analog=chemistry_analog,
        abiotic_risk=abiotic_risk,
        missing_channels=missing,
    )


def run_pipeline(
    spectral_csv: Path,
    isotope_csv: Path,
    mc_samples: int = 1000,
    mc_sigma: float = 0.05,
    context_override: Optional[float] = None,
    in_situ_override: Optional[float] = None,
    morphology_override: Optional[float] = None,
    spectral_limit: int = 0,
) -> Dict:
    """Tam pipeline calistir, sonuclari dict olarak dondur."""

    # 1. Ozellik cikarma
    spectral_features: List[Dict[str, str]] = []
    if spectral_csv.exists():
        rows = read_csv(spectral_csv)
        if spectral_limit > 0:
            rows = rows[:spectral_limit]
        spectral_features = [extract_spectral_features(r) for r in rows]

    isotope_features: List[Dict[str, str]] = []
    if isotope_csv.exists():
        isotope_features = [extract_isotope_features(r) for r in read_csv(isotope_csv)]

    # 2. Toplama
    spectral_agg = aggregate_spectral_hints(spectral_features)
    isotope_agg = aggregate_isotope_hints(isotope_features)

    # 3. Evidence olustur
    evidence = build_evidence_from_features(
        spectral_agg, isotope_agg,
        context_override=context_override,
        in_situ_override=in_situ_override,
        morphology_override=morphology_override,
    )
    validate_input(evidence)

    # 4. Puanlama
    result = calibrate_scores(evidence)

    # 5. Monte Carlo belirsizlik
    mc_result = None
    if mc_samples > 0:
        mc_result = monte_carlo_uncertainty(evidence, mc_samples, mc_sigma, seed=42)

    # 6. Hassasiyet
    sens_result = sensitivity_analysis(evidence)

    return {
        "feature_counts": {
            "spectral": len(spectral_features),
            "isotope": len(isotope_features),
        },
        "aggregated_hints": {
            "spectral": {k: round(v, 4) if isinstance(v, float) else v for k, v in spectral_agg.items()},
            "isotope": {k: round(v, 4) if isinstance(v, float) else v for k, v in isotope_agg.items()},
        },
        "evidence_input": {k: round(v, 4) if isinstance(v, float) else v for k, v in vars(evidence).items()},
        "scoring_result": {
            "calibrated_remote": result.calibrated_remote,
            "calibrated_context": result.calibrated_context,
            "calibrated_in_situ": result.calibrated_in_situ,
            "calibrated_chem_iso": result.calibrated_chem_iso,
            "calibrated_contam": result.calibrated_contam,
            "combined_score": result.combined_score,
            "label": result.label,
            "positive_channels": result.positive_channels,
            "reasons": result.reasons,
        },
        "uncertainty": mc_result,
        "sensitivity": sens_result,
    }


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_report(pipeline: Dict) -> None:
    fc = pipeline["feature_counts"]
    ah = pipeline["aggregated_hints"]
    ev = pipeline["evidence_input"]
    sr = pipeline["scoring_result"]
    mc = pipeline.get("uncertainty")
    sens = pipeline.get("sensitivity")

    print("=" * 70)
    print("BIYO-IZ PIPELINE RAPORU")
    print("=" * 70)

    print(f"\n--- Veri Girisi ---")
    print(f"  Spektral ozellik satiri : {fc['spectral']}")
    print(f"  Izotop referans satiri  : {fc['isotope']}")

    print(f"\n--- Toplanan Hintler ---")
    print(f"  S_remote hint     : {ah['spectral']['s_remote']:.4f}")
    print(f"  S_chem_iso hint   : {ah['isotope']['s_chem_iso']:.4f}")
    print(f"  Bio-relevant oran : {ah['spectral']['bio_ratio']:.4f}")
    print(f"  Contam (spektral) : {ah['spectral']['contam_spectral']:.4f}")
    print(f"  Contam (izotop)   : {ah['isotope']['contam_isotope']:.4f}")

    print(f"\n--- Model Girisleri ---")
    for k, v in ev.items():
        print(f"  {k:25s}: {v}")

    print(f"\n--- Puanlama Sonucu ---")
    print(f"  S_remote_cal   : {sr['calibrated_remote']:.4f}")
    print(f"  S_context_cal  : {sr['calibrated_context']:.4f}")
    print(f"  S_in_situ_cal  : {sr['calibrated_in_situ']:.4f}")
    print(f"  S_chem_iso_cal : {sr['calibrated_chem_iso']:.4f}")
    print(f"  R_contam_cal   : {sr['calibrated_contam']:.4f}")
    print(f"  S_final        : {sr['combined_score']:.4f}")
    print(f"  Pozitif kanal  : {sr['positive_channels']}")
    print(f"  ETIKET         : {sr['label']}")
    if sr["reasons"]:
        print("  Nedenler:")
        for r in sr["reasons"]:
            print(f"    - {r}")

    if mc:
        print(f"\n--- Belirsizlik (MC N={mc['n_samples']}) ---")
        print(f"  Ortalama : {mc['mean']:.4f}")
        print(f"  Std      : {mc['std']:.4f}")
        print(f"  %90 GA   : [{mc['ci90'][0]:.4f}, {mc['ci90'][1]:.4f}]")
        print(f"  Medyan   : {mc['median']:.4f}")
        print(f"  Etiket dagilimi:")
        for lbl, cnt in sorted(mc["label_distribution"].items(), key=lambda x: -x[1]):
            pct = cnt / mc["n_samples"] * 100
            print(f"    {lbl:30s}: {cnt:5d} ({pct:.1f}%)")

    if sens:
        print(f"\n--- Hassasiyet Analizi (+/- 20%) ---")
        print(f"  {'Agirlik':<10} {'Yon':>6} {'Baz':>8} {'Yeni':>8} {'Delta':>8}")
        for s in sens:
            print(f"  {s['weight']:<10} {s['direction']:>6} {s['base_score']:>8.4f} {s['new_score']:>8.4f} {s['delta_score']:>+8.4f}")

    print("\n" + "=" * 70)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Uctan uca biyo-iz pipeline")
    p.add_argument(
        "--spectral-csv",
        default="raw/earth/usgs_splib07/usgs_spectral_summary.csv",
        help="Spektral ozet CSV (spectral_summary.py ciktisi)",
    )
    p.add_argument(
        "--isotope-csv",
        default="raw/mars/reference/mars_isotope_reference_values.csv",
        help="Izotop referans CSV",
    )
    p.add_argument("--mc-samples", type=int, default=1000, help="Monte Carlo ornekleme")
    p.add_argument("--mc-sigma", type=float, default=0.05, help="MC perturbasyon sigma")
    p.add_argument("--context", type=float, default=None, help="S_context override")
    p.add_argument("--in-situ", type=float, default=None, help="S_in_situ override")
    p.add_argument("--morphology", type=float, default=None, help="Morfoloji analog override")
    p.add_argument("--spectral-limit", type=int, default=0, help="Maks spektral satir")
    p.add_argument("--json", action="store_true", help="JSON cikti")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    result = run_pipeline(
        spectral_csv=Path(args.spectral_csv),
        isotope_csv=Path(args.isotope_csv),
        mc_samples=args.mc_samples,
        mc_sigma=args.mc_sigma,
        context_override=args.context,
        in_situ_override=args.in_situ,
        morphology_override=args.morphology,
        spectral_limit=args.spectral_limit,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        print_report(result)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
