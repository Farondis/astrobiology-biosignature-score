#!/usr/bin/env python3
"""Baseline ML siniflandirici — kural tabanli model ile karsilastirma.

Stdlib-only: KNN ve karar agaci (CART) uygulamasi.
Veri kaynagi: validation_suite.py Canon senaryolari + MC data augmentation.

Kullanim:
    python baseline_ml.py                 # Tam analiz
    python baseline_ml.py --json          # JSON cikti
    python baseline_ml.py --augment 200   # Senaryo basina 200 MC ornek uret
"""
from __future__ import annotations

import argparse
import json
import math
import random
from collections import Counter
from dataclasses import dataclass
from statistics import fmean
from typing import Dict, List, Optional, Sequence, Tuple

from score_evidence import EvidenceInput, calibrate_scores, clamp
from validation_suite import CANON_TESTS, TestCase

# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------

FEATURE_NAMES = [
    "remote", "context", "in_situ", "chem_iso", "contam",
    "morphology_analog", "spectral_analog", "chemistry_analog",
    "abiotic_risk", "missing_channels",
]

LABEL_NAMES = ["Dusuk guven", "Ek ornekleme gerekli", "Orta guven", "Yuksek guven"]


def evidence_to_vector(ev: EvidenceInput) -> List[float]:
    return [
        ev.remote, ev.context, ev.in_situ, ev.chem_iso, ev.contam,
        ev.morphology_analog, ev.spectral_analog, ev.chemistry_analog,
        ev.abiotic_risk, float(ev.missing_channels),
    ]


def perturb_evidence(ev: EvidenceInput, sigma: float = 0.05) -> EvidenceInput:
    def _p(val: float) -> float:
        return clamp(val + random.gauss(0, sigma))
    return EvidenceInput(
        remote=_p(ev.remote), context=_p(ev.context),
        in_situ=_p(ev.in_situ), chem_iso=_p(ev.chem_iso),
        contam=_p(ev.contam), morphology_analog=_p(ev.morphology_analog),
        spectral_analog=_p(ev.spectral_analog), chemistry_analog=_p(ev.chemistry_analog),
        abiotic_risk=_p(ev.abiotic_risk), missing_channels=ev.missing_channels,
    )


# ---------------------------------------------------------------------------
# KNN Classifier
# ---------------------------------------------------------------------------

def euclidean_distance(a: Sequence[float], b: Sequence[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def knn_predict(
    train_X: List[List[float]],
    train_y: List[str],
    query: List[float],
    k: int = 3,
) -> str:
    distances = [(euclidean_distance(query, tx), ty) for tx, ty in zip(train_X, train_y)]
    distances.sort(key=lambda x: x[0])
    neighbors = [d[1] for d in distances[:k]]
    counter = Counter(neighbors)
    return counter.most_common(1)[0][0]


# ---------------------------------------------------------------------------
# Decision Tree (CART, Gini impurity)
# ---------------------------------------------------------------------------

@dataclass
class TreeNode:
    feature_idx: Optional[int] = None
    threshold: Optional[float] = None
    left: Optional[TreeNode] = None
    right: Optional[TreeNode] = None
    label: Optional[str] = None  # leaf node


def gini_impurity(labels: List[str]) -> float:
    if not labels:
        return 0.0
    n = len(labels)
    counts = Counter(labels)
    return 1.0 - sum((c / n) ** 2 for c in counts.values())


def best_split(
    X: List[List[float]], y: List[str]
) -> Tuple[Optional[int], Optional[float], float]:
    n = len(y)
    if n < 2:
        return None, None, 0.0

    best_gain = 0.0
    best_feat = None
    best_thresh = None
    parent_gini = gini_impurity(y)

    n_features = len(X[0])
    for feat in range(n_features):
        values = sorted(set(row[feat] for row in X))
        for i in range(len(values) - 1):
            thresh = (values[i] + values[i + 1]) / 2.0
            left_y = [y[j] for j in range(n) if X[j][feat] <= thresh]
            right_y = [y[j] for j in range(n) if X[j][feat] > thresh]
            if not left_y or not right_y:
                continue
            gain = parent_gini - (
                len(left_y) / n * gini_impurity(left_y)
                + len(right_y) / n * gini_impurity(right_y)
            )
            if gain > best_gain:
                best_gain = gain
                best_feat = feat
                best_thresh = thresh

    return best_feat, best_thresh, best_gain


def build_tree(
    X: List[List[float]], y: List[str], max_depth: int = 6, min_samples: int = 2
) -> TreeNode:
    if len(set(y)) == 1 or len(y) < min_samples or max_depth <= 0:
        return TreeNode(label=Counter(y).most_common(1)[0][0])

    feat, thresh, gain = best_split(X, y)
    if feat is None or gain < 1e-6:
        return TreeNode(label=Counter(y).most_common(1)[0][0])

    left_idx = [i for i in range(len(y)) if X[i][feat] <= thresh]
    right_idx = [i for i in range(len(y)) if X[i][feat] > thresh]

    left_X = [X[i] for i in left_idx]
    left_y = [y[i] for i in left_idx]
    right_X = [X[i] for i in right_idx]
    right_y = [y[i] for i in right_idx]

    return TreeNode(
        feature_idx=feat,
        threshold=thresh,
        left=build_tree(left_X, left_y, max_depth - 1, min_samples),
        right=build_tree(right_X, right_y, max_depth - 1, min_samples),
    )


def tree_predict(node: TreeNode, query: List[float]) -> str:
    if node.label is not None:
        return node.label
    if query[node.feature_idx] <= node.threshold:
        return tree_predict(node.left, query)
    return tree_predict(node.right, query)


def tree_depth(node: TreeNode) -> int:
    if node.label is not None:
        return 0
    return 1 + max(tree_depth(node.left), tree_depth(node.right))


def tree_size(node: TreeNode) -> int:
    if node.label is not None:
        return 1
    return 1 + tree_size(node.left) + tree_size(node.right)


def tree_rules(node: TreeNode, prefix: str = "") -> List[str]:
    if node.label is not None:
        return [f"{prefix}=> {node.label}"]
    feat = FEATURE_NAMES[node.feature_idx]
    rules = []
    rules.extend(tree_rules(node.left, f"{prefix}{feat} <= {node.threshold:.3f} -> "))
    rules.extend(tree_rules(node.right, f"{prefix}{feat} > {node.threshold:.3f} -> "))
    return rules


# ---------------------------------------------------------------------------
# Cross-validation
# ---------------------------------------------------------------------------

def leave_one_out_cv(
    X: List[List[float]], y: List[str], method: str = "knn", k: int = 3
) -> Tuple[float, List[Tuple[str, str]]]:
    """LOO-CV: accuracy ve (expected, predicted) listesi dondur."""
    predictions = []
    for i in range(len(y)):
        train_X = X[:i] + X[i + 1 :]
        train_y = y[:i] + y[i + 1 :]
        query = X[i]
        if method == "knn":
            pred = knn_predict(train_X, train_y, query, k)
        else:
            tree = build_tree(train_X, train_y, max_depth=4, min_samples=2)
            pred = tree_predict(tree, query)
        predictions.append((y[i], pred))
    accuracy = sum(1 for e, p in predictions if e == p) / len(predictions)
    return accuracy, predictions


def confusion_matrix(pairs: List[Tuple[str, str]], labels: List[str]) -> Dict[str, Dict[str, int]]:
    matrix = {e: {a: 0 for a in labels} for e in labels}
    for expected, actual in pairs:
        matrix[expected][actual] += 1
    return matrix


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Baseline ML siniflandirici")
    parser.add_argument("--augment", type=int, default=100,
                        help="Senaryo basina MC augmentation ornegi (varsayilan: 100)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    random.seed(args.seed)

    # --- 1. Ogrenme verisi olustur ---
    base_X: List[List[float]] = []
    base_y: List[str] = []
    for tc in CANON_TESTS:
        base_X.append(evidence_to_vector(tc.evidence))
        base_y.append(tc.expected_label)

    print(f"Temel senaryo sayisi: {len(base_X)}")
    print(f"Sinif dagilimi: {dict(Counter(base_y))}")

    # --- 2. MC data augmentation ---
    aug_X: List[List[float]] = list(base_X)
    aug_y: List[str] = list(base_y)
    for tc in CANON_TESTS:
        for _ in range(args.augment):
            pert = perturb_evidence(tc.evidence, sigma=0.05)
            aug_X.append(evidence_to_vector(pert))
            aug_y.append(tc.expected_label)

    print(f"Augmented veri seti: {len(aug_X)} ornek ({args.augment} x {len(CANON_TESTS)} + {len(CANON_TESTS)})")

    # --- 3. LOO-CV on base data ---
    print("\n" + "=" * 60)
    print("Leave-One-Out Cross-Validation (12 temel senaryo)")
    print("=" * 60)

    # Rule-based model
    rule_preds = []
    for tc in CANON_TESTS:
        result = calibrate_scores(tc.evidence)
        rule_preds.append((tc.expected_label, result.label))
    rule_acc = sum(1 for e, p in rule_preds if e == p) / len(rule_preds)

    # KNN (k=3)
    knn3_acc, knn3_preds = leave_one_out_cv(base_X, base_y, method="knn", k=3)
    # KNN (k=1)
    knn1_acc, knn1_preds = leave_one_out_cv(base_X, base_y, method="knn", k=1)
    # Decision tree
    dt_acc, dt_preds = leave_one_out_cv(base_X, base_y, method="tree")

    print(f"  Kural tabanli model  : {rule_acc:.2%} ({sum(1 for e,p in rule_preds if e==p)}/{len(rule_preds)})")
    print(f"  KNN (k=1) LOO-CV     : {knn1_acc:.2%} ({sum(1 for e,p in knn1_preds if e==p)}/{len(knn1_preds)})")
    print(f"  KNN (k=3) LOO-CV     : {knn3_acc:.2%} ({sum(1 for e,p in knn3_preds if e==p)}/{len(knn3_preds)})")
    print(f"  Decision Tree LOO-CV : {dt_acc:.2%} ({sum(1 for e,p in dt_preds if e==p)}/{len(dt_preds)})")

    # --- 4. Train on augmented data, test on base ---
    print("\n" + "=" * 60)
    print(f"Augmented egitim ({len(aug_X)}) → Temel test ({len(base_X)})")
    print("=" * 60)

    # KNN on augmented
    knn_aug_correct = 0
    knn_aug_preds = []
    for i in range(len(base_X)):
        pred = knn_predict(aug_X, aug_y, base_X[i], k=5)
        knn_aug_preds.append((base_y[i], pred))
        if pred == base_y[i]:
            knn_aug_correct += 1
    knn_aug_acc = knn_aug_correct / len(base_X)

    # Tree on augmented
    tree_aug = build_tree(aug_X, aug_y, max_depth=6, min_samples=5)
    tree_aug_correct = 0
    tree_aug_preds = []
    for i in range(len(base_X)):
        pred = tree_predict(tree_aug, base_X[i])
        tree_aug_preds.append((base_y[i], pred))
        if pred == base_y[i]:
            tree_aug_correct += 1
    tree_aug_acc = tree_aug_correct / len(base_X)

    print(f"  KNN (k=5, augmented) : {knn_aug_acc:.2%} ({knn_aug_correct}/{len(base_X)})")
    print(f"  Decision Tree (aug)  : {tree_aug_acc:.2%} ({tree_aug_correct}/{len(base_X)})")

    # --- 5. Decision tree structure ---
    print(f"\n  Karar agaci derinligi: {tree_depth(tree_aug)}")
    print(f"  Karar agaci dugum sayisi: {tree_size(tree_aug)}")
    print(f"\n  Karar kurallari:")
    for rule in tree_rules(tree_aug):
        print(f"    {rule}")

    # --- 6. Confusion matrices ---
    print("\n" + "=" * 60)
    print("Confusion Matrix — Augmented Decision Tree")
    print("=" * 60)
    cm = confusion_matrix(tree_aug_preds, LABEL_NAMES)
    header = f"{'Beklenen \\\\ Tahmin':>25s}"
    for lbl in LABEL_NAMES:
        header += f"  {lbl[:12]:>12s}"
    print(header)
    for expected in LABEL_NAMES:
        row = f"  {expected:>23s}"
        for actual in LABEL_NAMES:
            row += f"  {cm[expected][actual]:>12d}"
        print(row)

    # --- 7. Per-class metrics ---
    print("\n--- Sinif bazli metrikler (Decision Tree, augmented) ---")
    print(f"{'Sinif':>25s}  {'Precision':>9s}  {'Recall':>6s}  {'F1':>6s}")
    for lbl in LABEL_NAMES:
        tp = cm[lbl][lbl]
        fp = sum(cm[e][lbl] for e in LABEL_NAMES if e != lbl)
        fn = sum(cm[lbl][a] for a in LABEL_NAMES if a != lbl)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        print(f"  {lbl:>23s}  {precision:>9.2%}  {recall:>6.2%}  {f1:>6.2%}")

    # --- JSON output ---
    if args.json:
        output = {
            "base_scenarios": len(base_X),
            "augmented_total": len(aug_X),
            "augment_per_scenario": args.augment,
            "loo_cv": {
                "rule_based": {"accuracy": rule_acc, "correct": sum(1 for e,p in rule_preds if e==p)},
                "knn_k1": {"accuracy": knn1_acc},
                "knn_k3": {"accuracy": knn3_acc},
                "decision_tree": {"accuracy": dt_acc},
            },
            "augmented_test": {
                "knn_k5": {"accuracy": knn_aug_acc},
                "decision_tree": {"accuracy": tree_aug_acc, "depth": tree_depth(tree_aug), "nodes": tree_size(tree_aug)},
            },
            "tree_rules": tree_rules(tree_aug),
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
