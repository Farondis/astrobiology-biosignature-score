#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
from dataclasses import asdict, dataclass
from statistics import fmean, stdev
from typing import Dict, List, Optional, Tuple


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    if value < minimum:
        return minimum
    if value > maximum:
        return maximum
    return value


@dataclass
class EvidenceInput:
    remote: float
    context: float
    in_situ: float
    chem_iso: float
    contam: float
    morphology_analog: float
    spectral_analog: float
    chemistry_analog: float
    abiotic_risk: float
    missing_channels: int


@dataclass
class EvidenceResult:
    calibrated_remote: float
    calibrated_context: float
    calibrated_in_situ: float
    calibrated_chem_iso: float
    calibrated_contam: float
    combined_score: float
    label: str
    positive_channels: int
    reasons: List[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Biyo-iz karar modelini calistir")
    parser.add_argument("--remote", type=float, required=True, help="S_remote [0,1]")
    parser.add_argument("--context", type=float, required=True, help="S_context [0,1]")
    parser.add_argument("--in-situ", dest="in_situ", type=float, required=True, help="S_in_situ [0,1]")
    parser.add_argument("--chem-iso", dest="chem_iso", type=float, required=True, help="S_chem_iso [0,1]")
    parser.add_argument("--contam", type=float, required=True, help="R_contam [0,1]")
    parser.add_argument(
        "--morphology-analog",
        type=float,
        default=0.0,
        help="EARTH-004/005 tabanli morfolojik analog uyumu [0,1]",
    )
    parser.add_argument(
        "--spectral-analog",
        type=float,
        default=0.0,
        help="EARTH-008/010/011 tabanli spektral analog uyumu [0,1]",
    )
    parser.add_argument(
        "--chemistry-analog",
        type=float,
        default=0.0,
        help="EARTH-006/007 tabanli kimyasal analog uyumu [0,1]",
    )
    parser.add_argument(
        "--abiotic-risk",
        type=float,
        default=0.0,
        help="Abiyotik taklitci riski [0,1]",
    )
    parser.add_argument(
        "--missing-channels",
        type=int,
        default=0,
        help="Eksik veri nedeniyle kullanilamayan kanal sayisi",
    )
    parser.add_argument("--json", action="store_true", help="Sonucu JSON olarak yaz")
    parser.add_argument(
        "--monte-carlo",
        type=int,
        default=0,
        help="Monte Carlo perturbasyon sayisi (>0 ise guven araligi uret)",
    )
    parser.add_argument(
        "--mc-sigma",
        type=float,
        default=0.05,
        help="Monte Carlo perturbasyon standart sapmasi (varsayilan 0.05)",
    )
    parser.add_argument(
        "--sensitivity",
        action="store_true",
        help="Agirlik hassasiyet analizi yap (+/- %%20 perturbasyon)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Rastgele sayi tohumu (tekrarlanabilirlik icin)",
    )
    return parser.parse_args()


def calibrate_scores(data: EvidenceInput) -> EvidenceResult:
    reasons: List[str] = []

    calibrated_remote = clamp(data.remote + 0.12 * data.spectral_analog - 0.08 * data.abiotic_risk)
    calibrated_context = clamp(data.context - 0.05 * data.abiotic_risk)
    calibrated_in_situ = clamp(data.in_situ + 0.15 * data.morphology_analog - 0.08 * data.abiotic_risk)
    calibrated_chem_iso = clamp(data.chem_iso + 0.20 * data.chemistry_analog)
    calibrated_contam = clamp(data.contam + 0.20 * data.abiotic_risk + 0.10 * max(data.spectral_analog - data.chemistry_analog, 0.0))

    missing_penalty = 0.04 * max(data.missing_channels, 0)
    combined_score = clamp(
        0.25 * calibrated_remote
        + 0.20 * calibrated_context
        + 0.20 * calibrated_in_situ
        + 0.35 * calibrated_chem_iso
        - 0.25 * calibrated_contam
        - missing_penalty
    )

    positive_channels = sum(
        score >= 0.55
        for score in (calibrated_remote, calibrated_context, calibrated_in_situ, calibrated_chem_iso)
    )

    if data.spectral_analog >= 0.6:
        reasons.append("Spektral analog uyumu Earth kutuphanesi ile guclu.")
    if data.morphology_analog >= 0.6:
        reasons.append("Morfolojik analog uyumu Earth saha ornekleri ile uyumlu.")
    if data.chemistry_analog >= 0.6:
        reasons.append("Kimyasal analog uyumu Earth referanslari ile guclu.")
    if data.abiotic_risk >= 0.5:
        reasons.append("Abiyotik taklit riski belirgin oldugu icin ceza uygulandi.")
    if data.missing_channels > 0:
        reasons.append(f"Eksik kanal cezasi uygulandi: {data.missing_channels} kanal.")

    label = classify_result(
        combined_score=combined_score,
        calibrated_remote=calibrated_remote,
        calibrated_in_situ=calibrated_in_situ,
        calibrated_chem_iso=calibrated_chem_iso,
        morphology_analog=data.morphology_analog,
        spectral_analog=data.spectral_analog,
        chemistry_analog=data.chemistry_analog,
        abiotic_risk=data.abiotic_risk,
        positive_channels=positive_channels,
        reasons=reasons,
    )

    return EvidenceResult(
        calibrated_remote=round(calibrated_remote, 4),
        calibrated_context=round(calibrated_context, 4),
        calibrated_in_situ=round(calibrated_in_situ, 4),
        calibrated_chem_iso=round(calibrated_chem_iso, 4),
        calibrated_contam=round(calibrated_contam, 4),
        combined_score=round(combined_score, 4),
        label=label,
        positive_channels=positive_channels,
        reasons=reasons,
    )


def classify_result(
    *,
    combined_score: float,
    calibrated_remote: float,
    calibrated_in_situ: float,
    calibrated_chem_iso: float,
    morphology_analog: float,
    spectral_analog: float,
    chemistry_analog: float,
    abiotic_risk: float,
    positive_channels: int,
    reasons: List[str],
) -> str:
    if combined_score >= 0.72:
        if calibrated_chem_iso <= 0.2:
            reasons.append("Kimyasal/izotopik kanal sifira yakin oldugu icin yuksek guven engellendi.")
            return "Orta guven"
        if min(morphology_analog, spectral_analog, chemistry_analog) < 0.4:
            reasons.append("Morfoloji, spektral ve kimyasal analog uclusu birlikte guclu olmadigi icin yuksek guven engellendi.")
            return "Ek ornekleme gerekli"
        if positive_channels < 2:
            reasons.append("En az iki bagimsiz kanal pozitif olmadigi icin yuksek guven engellendi.")
            return "Ek ornekleme gerekli"
        if abiotic_risk >= 0.6:
            reasons.append("Abiyotik risk yuksek oldugu icin yuksek guven engellendi.")
            return "Ek ornekleme gerekli"
        reasons.append("Coklu kanit ve kimyasal destek ile yuksek guven saglandi.")
        return "Yuksek guven"

    if combined_score >= 0.45:
        if calibrated_remote >= 0.7 and calibrated_in_situ < 0.4 and calibrated_chem_iso < 0.2:
            reasons.append("Uzaktan algilama guclu fakat yakin/kimyasal dogrulama zayif; orta guvende tutuldu.")
            return "Orta guven"
        if calibrated_in_situ >= 0.7 and calibrated_remote < 0.4 and calibrated_chem_iso < 0.2:
            reasons.append("Morfoloji guclu fakat spektral/kimyasal dogrulama zayif; orta guvende tutuldu.")
            return "Orta guven"
        reasons.append("Birlesik skor orta esigi asti ancak tum yuksek guven kosullari saglanmadi.")
        return "Orta guven"

    if max(calibrated_remote, calibrated_in_situ, calibrated_chem_iso) >= 0.55:
        reasons.append("En az bir kanal umut verici ancak birlesik skor dusuk; ek ornekleme gerekli.")
        return "Ek ornekleme gerekli"

    reasons.append("Mevcut kanitlar dusuk guven seviyesinde kaldi.")
    return "Dusuk guven"


# ---------------------------------------------------------------------------
# Monte Carlo uncertainty
# ---------------------------------------------------------------------------

def perturb_input(data: EvidenceInput, sigma: float) -> EvidenceInput:
    """Girdi degerlerine Gauss gurultu ekle."""
    def _p(val: float) -> float:
        return clamp(val + random.gauss(0, sigma))
    return EvidenceInput(
        remote=_p(data.remote),
        context=_p(data.context),
        in_situ=_p(data.in_situ),
        chem_iso=_p(data.chem_iso),
        contam=_p(data.contam),
        morphology_analog=_p(data.morphology_analog),
        spectral_analog=_p(data.spectral_analog),
        chemistry_analog=_p(data.chemistry_analog),
        abiotic_risk=_p(data.abiotic_risk),
        missing_channels=data.missing_channels,
    )


def monte_carlo_uncertainty(
    data: EvidenceInput, n_samples: int, sigma: float, seed: int = 42
) -> Dict:
    """N kez perturbe et, skor dagilimini raporla."""
    random.seed(seed)
    scores: List[float] = []
    labels: Dict[str, int] = {}
    for _ in range(n_samples):
        p = perturb_input(data, sigma)
        r = calibrate_scores(p)
        scores.append(r.combined_score)
        labels[r.label] = labels.get(r.label, 0) + 1

    scores.sort()
    n = len(scores)
    p5 = scores[max(0, int(n * 0.05))]
    p25 = scores[max(0, int(n * 0.25))]
    p50 = scores[max(0, int(n * 0.50))]
    p75 = scores[min(n - 1, int(n * 0.75))]
    p95 = scores[min(n - 1, int(n * 0.95))]

    return {
        "n_samples": n_samples,
        "sigma": sigma,
        "mean": round(fmean(scores), 4),
        "std": round(stdev(scores), 4) if n > 1 else 0.0,
        "p5": round(p5, 4),
        "p25": round(p25, 4),
        "median": round(p50, 4),
        "p75": round(p75, 4),
        "p95": round(p95, 4),
        "ci90": [round(p5, 4), round(p95, 4)],
        "label_distribution": labels,
    }


# ---------------------------------------------------------------------------
# Sensitivity analysis
# ---------------------------------------------------------------------------

_WEIGHT_NAMES = ["alpha", "beta", "gamma", "delta", "lambda"]
_WEIGHT_DEFAULTS = [0.25, 0.20, 0.20, 0.35, 0.25]


def sensitivity_analysis(
    data: EvidenceInput, perturbation: float = 0.20
) -> List[Dict]:
    """Her agirligi +/- perturbation kadar degistir, skor etkisini olc."""
    base_result = calibrate_scores(data)
    base_score = base_result.combined_score
    report: List[Dict] = []

    for i, (name, default) in enumerate(zip(_WEIGHT_NAMES, _WEIGHT_DEFAULTS)):
        for direction in (-1, +1):
            delta = default * perturbation * direction
            modified_weights = list(_WEIGHT_DEFAULTS)
            modified_weights[i] = default + delta

            # Recalculate with modified weights
            r = calibrate_scores(data)
            # Manually recompute combined with modified weights
            cal = [
                r.calibrated_remote, r.calibrated_context,
                r.calibrated_in_situ, r.calibrated_chem_iso,
                r.calibrated_contam,
            ]
            missing_penalty = 0.04 * max(data.missing_channels, 0)
            new_score = clamp(
                modified_weights[0] * cal[0]
                + modified_weights[1] * cal[1]
                + modified_weights[2] * cal[2]
                + modified_weights[3] * cal[3]
                - modified_weights[4] * cal[4]
                - missing_penalty
            )

            report.append({
                "weight": name,
                "default": default,
                "modified": round(default + delta, 4),
                "direction": f"{'+' if direction > 0 else '-'}{int(perturbation*100)}%",
                "base_score": round(base_score, 4),
                "new_score": round(new_score, 4),
                "delta_score": round(new_score - base_score, 4),
            })

    return report


def validate_input(data: EvidenceInput) -> None:
    for field_name, value in asdict(data).items():
        if field_name == "missing_channels":
            if value < 0:
                raise ValueError("missing_channels negatif olamaz")
            continue
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{field_name} 0 ile 1 arasynda olmali")


def main() -> int:
    args = parse_args()
    data = EvidenceInput(
        remote=args.remote,
        context=args.context,
        in_situ=args.in_situ,
        chem_iso=args.chem_iso,
        contam=args.contam,
        morphology_analog=args.morphology_analog,
        spectral_analog=args.spectral_analog,
        chemistry_analog=args.chemistry_analog,
        abiotic_risk=args.abiotic_risk,
        missing_channels=args.missing_channels,
    )

    validate_input(data)
    result = calibrate_scores(data)

    # Monte Carlo uncertainty
    mc_result = None
    if args.monte_carlo > 0:
        mc_result = monte_carlo_uncertainty(data, args.monte_carlo, args.mc_sigma, args.seed)

    # Sensitivity analysis
    sens_result = None
    if args.sensitivity:
        sens_result = sensitivity_analysis(data)

    if args.json:
        output = asdict(result)
        if mc_result:
            output["uncertainty"] = mc_result
        if sens_result:
            output["sensitivity"] = sens_result
        print(json.dumps(output, ensure_ascii=True, indent=2))
        return 0

    print(f"S_remote_cal     : {result.calibrated_remote:.4f}")
    print(f"S_context_cal    : {result.calibrated_context:.4f}")
    print(f"S_in_situ_cal    : {result.calibrated_in_situ:.4f}")
    print(f"S_chem_iso_cal   : {result.calibrated_chem_iso:.4f}")
    print(f"R_contam_cal     : {result.calibrated_contam:.4f}")
    print(f"S_final          : {result.combined_score:.4f}")
    print(f"Pozitif kanal    : {result.positive_channels}")
    print(f"Etiket           : {result.label}")
    if result.reasons:
        print("Nedenler")
        for item in result.reasons:
            print(f"- {item}")

    if mc_result:
        print(f"\n--- Monte Carlo Belirsizlik (N={mc_result['n_samples']}, sigma={mc_result['sigma']}) ---")
        print(f"  Ortalama       : {mc_result['mean']:.4f}")
        print(f"  Std sapma      : {mc_result['std']:.4f}")
        print(f"  %%90 GA         : [{mc_result['ci90'][0]:.4f}, {mc_result['ci90'][1]:.4f}]")
        print(f"  Medyan         : {mc_result['median']:.4f}")
        print(f"  P5/P25/P75/P95 : {mc_result['p5']:.4f} / {mc_result['p25']:.4f} / {mc_result['p75']:.4f} / {mc_result['p95']:.4f}")
        print("  Etiket dagilimi:")
        for lbl, cnt in sorted(mc_result["label_distribution"].items(), key=lambda x: -x[1]):
            pct = cnt / mc_result["n_samples"] * 100
            print(f"    {lbl:30s} : {cnt:5d} ({pct:.1f}%%)")

    if sens_result:
        print("\n--- Agirlik Hassasiyet Analizi (+/- 20%%) ---")
        print(f"  {'Agirlik':<10} {'Yon':>6} {'Varsayilan':>10} {'Degistirilmis':>14} {'Baz Skor':>9} {'Yeni Skor':>10} {'Delta':>8}")
        for s in sens_result:
            print(f"  {s['weight']:<10} {s['direction']:>6} {s['default']:>10.4f} {s['modified']:>14.4f} {s['base_score']:>9.4f} {s['new_score']:>10.4f} {s['delta_score']:>+8.4f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())