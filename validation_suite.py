#!/usr/bin/env python3
"""Biyo-iz karar modeli dogrulama test takimi.

Bilinen Earth pozitif/negatif/belirsiz senaryolari tanimlar,
score_evidence puanlama motorundan gecirir ve basari raporu uretir.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional

from score_evidence import EvidenceInput, calibrate_scores, validate_input, monte_carlo_uncertainty


# ---------------------------------------------------------------------------
# Test case definitions
# ---------------------------------------------------------------------------

@dataclass
class TestCase:
    name: str
    description: str
    expected_label: str          # beklenen karar etiketi
    min_score: float             # beklenen minimum S_final
    max_score: float             # beklenen maksimum S_final
    evidence: EvidenceInput


# Canon test cases — gercek analog senaryolari

CANON_TESTS: List[TestCase] = [
    # --- Earth pozitif kontroller ---
    TestCase(
        name="earth_stromatolite_full",
        description="Shark Bay stromatoliti: morfoloji + spektral + kimya + izotop hepsi guclu",
        expected_label="Yuksek guven",
        min_score=0.70,
        max_score=1.00,
        evidence=EvidenceInput(
            remote=0.82, context=0.78, in_situ=0.85, chem_iso=0.80, contam=0.08,
            morphology_analog=0.92, spectral_analog=0.88, chemistry_analog=0.85,
            abiotic_risk=0.05, missing_channels=0,
        ),
    ),
    TestCase(
        name="earth_yellowstone_sinter",
        description="Yellowstone silisli sinter: morfoloji + kimya guclu, spektral orta",
        expected_label="Yuksek guven",
        min_score=0.65,
        max_score=1.00,
        evidence=EvidenceInput(
            remote=0.68, context=0.72, in_situ=0.80, chem_iso=0.75, contam=0.12,
            morphology_analog=0.88, spectral_analog=0.65, chemistry_analog=0.82,
            abiotic_risk=0.10, missing_channels=0,
        ),
    ),
    TestCase(
        name="earth_microbial_mat_arsenic",
        description="Arsenik turlesmesi mikrobiyal mat: kimya cok guclu, morfoloji orta",
        expected_label="Orta guven",
        min_score=0.45,
        max_score=0.80,
        evidence=EvidenceInput(
            remote=0.55, context=0.60, in_situ=0.50, chem_iso=0.78, contam=0.15,
            morphology_analog=0.45, spectral_analog=0.60, chemistry_analog=0.90,
            abiotic_risk=0.12, missing_channels=0,
        ),
    ),

    # --- Earth negatif kontroller ---
    TestCase(
        name="earth_evaporite_abiotic",
        description="Death Valley evaporit: morfoloji var ama abiyotik",
        expected_label="Dusuk guven",
        min_score=0.00,
        max_score=0.40,
        evidence=EvidenceInput(
            remote=0.30, context=0.25, in_situ=0.35, chem_iso=0.10, contam=0.60,
            morphology_analog=0.50, spectral_analog=0.20, chemistry_analog=0.10,
            abiotic_risk=0.75, missing_channels=1,
        ),
    ),
    TestCase(
        name="earth_iron_oxide_mimic",
        description="Demir oksit kaplama: spektral benzerlik ama kimyasal destek yok",
        expected_label="Dusuk guven",
        min_score=0.00,
        max_score=0.40,
        evidence=EvidenceInput(
            remote=0.45, context=0.30, in_situ=0.20, chem_iso=0.05, contam=0.55,
            morphology_analog=0.15, spectral_analog=0.40, chemistry_analog=0.05,
            abiotic_risk=0.70, missing_channels=2,
        ),
    ),
    TestCase(
        name="earth_fischer_tropsch_false_positive",
        description="Fischer-Tropsch sentetik organik: izotop biyotik aralikta ama abiyotik",
        expected_label="Ek ornekleme gerekli",
        min_score=0.25,
        max_score=0.55,
        evidence=EvidenceInput(
            remote=0.40, context=0.35, in_situ=0.30, chem_iso=0.55, contam=0.40,
            morphology_analog=0.10, spectral_analog=0.35, chemistry_analog=0.30,
            abiotic_risk=0.60, missing_channels=1,
        ),
    ),

    # --- Mars senaryolari ---
    TestCase(
        name="mars_jezero_delta_promising",
        description="Jezero delta: orbital + baglam guclu, in-situ ve kimya orta",
        expected_label="Orta guven",
        min_score=0.45,
        max_score=0.75,
        evidence=EvidenceInput(
            remote=0.75, context=0.80, in_situ=0.55, chem_iso=0.45, contam=0.20,
            morphology_analog=0.60, spectral_analog=0.70, chemistry_analog=0.50,
            abiotic_risk=0.18, missing_channels=1,
        ),
    ),
    TestCase(
        name="mars_sulfate_vein_ambiguous",
        description="Mars sulfat damar: kimya ilginc ama morfoloji zayif",
        expected_label="Ek ornekleme gerekli",
        min_score=0.30,
        max_score=0.60,
        evidence=EvidenceInput(
            remote=0.50, context=0.55, in_situ=0.30, chem_iso=0.60, contam=0.25,
            morphology_analog=0.20, spectral_analog=0.55, chemistry_analog=0.65,
            abiotic_risk=0.30, missing_channels=1,
        ),
    ),
    TestCase(
        name="mars_basalt_no_signal",
        description="Mars bazalt: hicbir kanal anlamli sinyal vermiyor",
        expected_label="Dusuk guven",
        min_score=0.00,
        max_score=0.35,
        evidence=EvidenceInput(
            remote=0.20, context=0.15, in_situ=0.10, chem_iso=0.05, contam=0.05,
            morphology_analog=0.05, spectral_analog=0.10, chemistry_analog=0.05,
            abiotic_risk=0.10, missing_channels=2,
        ),
    ),

    # --- Tek-kanalli baskinlik kontrolleri ---
    TestCase(
        name="single_channel_remote_only",
        description="Yalnizca S_remote guclu — yuksek guven engellenmeli, ek ornekleme onerilmeli",
        expected_label="Ek ornekleme gerekli",
        min_score=0.20,
        max_score=0.55,
        evidence=EvidenceInput(
            remote=0.90, context=0.80, in_situ=0.10, chem_iso=0.05, contam=0.10,
            morphology_analog=0.10, spectral_analog=0.85, chemistry_analog=0.05,
            abiotic_risk=0.05, missing_channels=2,
        ),
    ),
    TestCase(
        name="single_channel_morphology_only",
        description="Yalnizca S_in_situ guclu — yuksek guven engellenmeli, ek ornekleme onerilmeli",
        expected_label="Ek ornekleme gerekli",
        min_score=0.20,
        max_score=0.55,
        evidence=EvidenceInput(
            remote=0.15, context=0.50, in_situ=0.85, chem_iso=0.10, contam=0.12,
            morphology_analog=0.90, spectral_analog=0.10, chemistry_analog=0.10,
            abiotic_risk=0.08, missing_channels=1,
        ),
    ),

    # --- Eksik kanal ceza testi ---
    TestCase(
        name="missing_channels_penalty",
        description="Guclu sinyaller ama 3 kanal eksik — ceza skoru dusurur",
        expected_label="Orta guven",
        min_score=0.35,
        max_score=0.70,
        evidence=EvidenceInput(
            remote=0.70, context=0.65, in_situ=0.60, chem_iso=0.55, contam=0.15,
            morphology_analog=0.70, spectral_analog=0.65, chemistry_analog=0.60,
            abiotic_risk=0.10, missing_channels=3,
        ),
    ),
]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

@dataclass
class TestResult:
    name: str
    passed: bool
    expected_label: str
    actual_label: str
    expected_score_range: str
    actual_score: float
    label_match: bool
    score_in_range: bool
    mc_stability: Optional[float] = None  # dominant label % in MC


def run_test(tc: TestCase, mc_samples: int = 500) -> TestResult:
    validate_input(tc.evidence)
    result = calibrate_scores(tc.evidence)

    label_match = result.label == tc.expected_label
    score_in_range = tc.min_score <= result.combined_score <= tc.max_score

    mc_stability = None
    if mc_samples > 0:
        mc = monte_carlo_uncertainty(tc.evidence, mc_samples, 0.05, seed=42)
        dominant = max(mc["label_distribution"].values())
        mc_stability = dominant / mc_samples

    passed = label_match and score_in_range

    return TestResult(
        name=tc.name,
        passed=passed,
        expected_label=tc.expected_label,
        actual_label=result.label,
        expected_score_range=f"[{tc.min_score:.2f}, {tc.max_score:.2f}]",
        actual_score=result.combined_score,
        label_match=label_match,
        score_in_range=score_in_range,
        mc_stability=mc_stability,
    )


def run_all(mc_samples: int = 500) -> List[TestResult]:
    return [run_test(tc, mc_samples) for tc in CANON_TESTS]


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def print_report(results: List[TestResult]) -> None:
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed

    print("=" * 90)
    print("DOGRULAMA TEST SONUCLARI")
    print("=" * 90)
    print(f"{'Test':40s} {'Etiket':12s} {'Skor':>8s} {'Aralik':>16s} {'MC%':>6s} {'Sonuc':>8s}")
    print("-" * 90)

    for r in results:
        status = "GECTI" if r.passed else "KALDI"
        mc_str = f"{r.mc_stability:.0%}" if r.mc_stability is not None else "  -  "
        score_color = "" 
        print(
            f"  {r.name:38s} "
            f"{'OK' if r.label_match else 'XX':>2s} {r.actual_label:10s} "
            f"{r.actual_score:8.4f} "
            f"{r.expected_score_range:>16s} "
            f"{mc_str:>6s} "
            f"{'  ' + status:>8s}"
        )
        if not r.label_match:
            print(f"    ^ Beklenen etiket: {r.expected_label}")
        if not r.score_in_range:
            print(f"    ^ Skor beklenen aralik disinda")

    print("-" * 90)
    print(f"TOPLAM: {total} test | GECTI: {passed} | KALDI: {failed}")

    if failed == 0:
        print("TUM TESTLER BASARILI")
    else:
        print(f"{failed} TEST BASARISIZ — karar sinirlarini gozden gecirin")

    # Confusion matrix
    print("\n--- Etiket Confusion Matrix ---")
    labels = sorted(set(r.expected_label for r in results) | set(r.actual_label for r in results))
    matrix: Dict[str, Dict[str, int]] = {e: {a: 0 for a in labels} for e in labels}
    for r in results:
        matrix[r.expected_label][r.actual_label] += 1

    header = f"{'Beklenen \\\\ Gercek':>25s}"
    for lbl in labels:
        header += f"  {lbl[:12]:>12s}"
    print(header)
    for expected in labels:
        row_str = f"  {expected:>23s}"
        for actual in labels:
            count = matrix[expected][actual]
            row_str += f"  {count:>12d}"
        print(row_str)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Biyo-iz karar modeli dogrulama test takimi")
    p.add_argument("--mc-samples", type=int, default=500, help="MC stabilite ornekleme sayisi")
    p.add_argument("--json", action="store_true", help="JSON cikti")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    results = run_all(mc_samples=args.mc_samples)

    if args.json:
        output = [asdict(r) for r in results]
        print(json.dumps(output, ensure_ascii=True, indent=2))
    else:
        print_report(results)

    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
