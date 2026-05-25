"""Compare the WxWords ResNet50V2 model against the native labels of
the TJNU and WEBCAM datasets, and produce a markdown skill report.

Inputs:
    data/tjnu_predictions.json     (predictions from presort_tjnu.py)
    data/webcam_predictions.json   (predictions from presort_webcam.py)

Output:
    classifier_skill_report.md
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TJNU_PRED = ROOT / "data" / "tjnu_predictions.json"
WEBCAM_PRED = ROOT / "data" / "webcam_predictions.json"
OUTPUT = ROOT / "classifier_skill_report.md"

CCSN_CLASSES = ["Ac", "As", "Cb", "Cc", "Ci", "Cs", "Ct", "Cu", "Ns", "Sc", "St"]

# TJNU class → set of CCSN classes that would be reasonable matches
TJNU_PLAUSIBLE = {
    "1": {"Cu"},
    "2": {"Ac", "Cc"},
    "3": {"Ci", "Cs"},
    "4": set(),  # Clear sky — no CCSN class matches (Clear isn't in CCSN)
    "5": {"Sc", "St", "As"},
    "6": {"Cb", "Ns"},
    "7": set(CCSN_CLASSES),  # Mixed — anything could match
}

TJNU_LABELS = {
    "1": "Cumulus",
    "2": "Altocumulus/Cirrocumulus",
    "3": "Cirrus/Cirrostratus",
    "4": "Clear sky",
    "5": "Stratocumulus/Stratus/Altostratus",
    "6": "Cumulonimbus/Nimbostratus",
    "7": "Mixed cloud",
}

# WEBCAM class → plausible CCSN classes
WEBCAM_PLAUSIBLE = {
    "ac": {"Ac"},
    "cb": {"Cb"},
    "ci": {"Ci"},
    "clear": set(),
    "cu": {"Cu"},
    "obsc": {"St", "Ns"},  # Obscured = fog-like, closest CCSN is St
    "precip": {"Ns", "Cb"},
    "st": {"St"},
    "tcu": {"Cu", "Cb"},  # Towering Cu — between Cu and Cb
}

WEBCAM_LABELS = {
    "ac": "Altocumulus",
    "cb": "Cumulonimbus",
    "ci": "Cirrus",
    "clear": "Clear sky",
    "cu": "Fair-weather Cumulus",
    "obsc": "Obscured / Fog",
    "precip": "Precipitation",
    "st": "Stratus",
    "tcu": "Towering Cumulus",
}


def build_confusion(predictions: list[dict], native_key: str) -> dict:
    """Build a confusion matrix: native class → Counter(predicted CCSN class)."""
    matrix = defaultdict(Counter)
    for entry in predictions:
        native = entry.get(native_key)
        predicted = entry.get("predicted")
        if native is None or predicted is None:
            continue
        matrix[native][predicted] += 1
    return matrix


def confusion_to_markdown(
    matrix: dict,
    native_labels: dict,
    plausible: dict,
    title: str,
) -> str:
    """Render confusion matrix and skill metrics as markdown."""
    lines = [f"## {title}\n"]

    # Header row
    header = "| Native class | n | " + " | ".join(CCSN_CLASSES) + " | Top match | Plausible % |"
    sep = "|" + "---|" * (len(CCSN_CLASSES) + 4)
    lines.append(header)
    lines.append(sep)

    total_correct_plausible = 0
    total_n = 0

    for native_class in sorted(matrix.keys(), key=lambda k: native_labels.get(k, k)):
        counts = matrix[native_class]
        n = sum(counts.values())
        total_n += n
        label = native_labels.get(native_class, native_class)

        # Find top predicted
        top_pred, top_count = counts.most_common(1)[0]
        top_pct = top_count / n * 100

        # Plausible match rate (any prediction in plausible set)
        plaus_set = plausible.get(native_class, set())
        plaus_count = sum(c for cls, c in counts.items() if cls in plaus_set)
        plaus_pct = plaus_count / n * 100 if n > 0 else 0
        total_correct_plausible += plaus_count

        # Per-CCSN-class cells
        cells = []
        for cls in CCSN_CLASSES:
            c = counts.get(cls, 0)
            pct = c / n * 100 if n > 0 else 0
            if pct >= 40:
                cells.append(f"**{pct:.0f}**")
            elif pct >= 15:
                cells.append(f"{pct:.0f}")
            elif pct > 0:
                cells.append(f"·")
            else:
                cells.append("")

        row = (
            f"| **{label}** ({native_class}) | {n} | "
            + " | ".join(cells)
            + f" | {top_pred} ({top_pct:.0f}%) | "
            + (f"{plaus_pct:.0f}%" if plaus_set else "n/a")
            + " |"
        )
        lines.append(row)

    if total_n > 0:
        overall = total_correct_plausible / total_n * 100
        lines.append("")
        lines.append(f"**Overall plausible-match rate: {overall:.1f}%** ({total_correct_plausible:,} / {total_n:,} images)")

    lines.append("")
    lines.append("_Values are % of native class's images predicted as each CCSN class. "
                 "**Bold** ≥40%, plain ≥15%, · means <15% but non-zero. "
                 "'Plausible %' is the rate at which the model predicted a class that overlaps "
                 "the native class's true cloud types._")
    lines.append("")

    return "\n".join(lines)


def confidence_distribution(predictions: list[dict], title: str) -> str:
    """Render a confidence distribution summary."""
    lines = [f"### {title} — model confidence distribution\n"]
    confs = [p["confidence"] for p in predictions if "confidence" in p]
    if not confs:
        return ""

    buckets = {
        ">= 80%": sum(1 for c in confs if c >= 80),
        "60-80%": sum(1 for c in confs if 60 <= c < 80),
        "40-60%": sum(1 for c in confs if 40 <= c < 60),
        "20-40%": sum(1 for c in confs if 20 <= c < 40),
        "< 20%":  sum(1 for c in confs if c < 20),
    }
    total = len(confs)
    lines.append("| Top-1 confidence | n | % |")
    lines.append("|---|---|---|")
    for bucket, n in buckets.items():
        lines.append(f"| {bucket} | {n:,} | {n / total * 100:.1f}% |")
    lines.append("")
    return "\n".join(lines)


def class_distribution(predictions: list[dict], title: str) -> str:
    """Show what classes the model predicts most for this dataset."""
    counter = Counter(p["predicted"] for p in predictions if "predicted" in p)
    total = sum(counter.values())
    lines = [f"### {title} — what the model predicted most\n"]
    lines.append("| Predicted CCSN class | n | % |")
    lines.append("|---|---|---|")
    for cls in sorted(counter.keys(), key=lambda c: -counter[c]):
        n = counter[cls]
        lines.append(f"| {cls} | {n:,} | {n / total * 100:.1f}% |")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    if not TJNU_PRED.exists() or not WEBCAM_PRED.exists():
        print("Missing predictions. Run presort_tjnu.py and presort_webcam.py first.")
        return

    tjnu = json.loads(TJNU_PRED.read_text())
    webcam = json.loads(WEBCAM_PRED.read_text())

    print(f"TJNU: {len(tjnu):,} predictions loaded")
    print(f"WEBCAM: {len(webcam):,} predictions loaded")

    sections = [
        "# Classifier Skill Report",
        "",
        "Comparison of the WxWords ResNet50V2 cloud classifier (trained on CCSN, 11 classes) "
        "against the native labels of two external ground-based cloud datasets: "
        "TJNU GCD (7 broad WMO categories) and WEBCAM aviation (9 operational classes).",
        "",
        "The model was trained only on CCSN. These datasets are out-of-sample tests of how "
        "well the model generalises to imagery captured by different cameras, in different "
        "locations, under different conditions.",
        "",
        "## How to read this report",
        "",
        "- Each row is a **native dataset class**, with the count of images and the distribution "
        "of CCSN predictions the model produced.",
        "- The **Top match** column shows which CCSN class the model picked most often for that native class.",
        "- The **Plausible %** column shows the share of predictions that fall within a "
        "human-judged set of acceptable CCSN matches. For example, TJNU class 2 "
        "(Altocumulus/Cirrocumulus) maps to Ac or Cc — a prediction of either counts as plausible.",
        "- The **Native class** column shows the dataset's own label, which is taken as ground truth.",
        "- **Limitations:** native datasets have their own labelling biases. WEBCAM 'precip' is "
        "a weather state not a cloud genus, so any CCSN mapping is approximate.",
        "",
        "---",
        "",
    ]

    # TJNU
    tjnu_matrix = build_confusion(tjnu, "tjnu_class")
    sections.append(
        confusion_to_markdown(
            tjnu_matrix,
            TJNU_LABELS,
            TJNU_PLAUSIBLE,
            "TJNU Ground-based Cloud Dataset (19,000 images, 7 classes)",
        )
    )
    sections.append(confidence_distribution(tjnu, "TJNU"))
    sections.append(class_distribution(tjnu, "TJNU"))
    sections.append("---\n")

    # WEBCAM
    webcam_matrix = build_confusion(webcam, "webcam_class")
    sections.append(
        confusion_to_markdown(
            webcam_matrix,
            WEBCAM_LABELS,
            WEBCAM_PLAUSIBLE,
            "WEBCAM Aviation Cloud Dataset (15,543 images, 9 classes)",
        )
    )
    sections.append(confidence_distribution(webcam, "WEBCAM"))
    sections.append(class_distribution(webcam, "WEBCAM"))
    sections.append("---\n")

    # Summary observations
    sections.append("## Observations")
    sections.append("")
    sections.append("This section is auto-generated from the data; treat it as a starting "
                    "point for analysis, not conclusions.")
    sections.append("")

    # Auto-find biggest disagreement classes
    for name, matrix, labels, plaus in [
        ("TJNU", tjnu_matrix, TJNU_LABELS, TJNU_PLAUSIBLE),
        ("WEBCAM", webcam_matrix, WEBCAM_LABELS, WEBCAM_PLAUSIBLE),
    ]:
        sections.append(f"### {name}")
        sections.append("")
        for cls, counts in sorted(matrix.items()):
            n = sum(counts.values())
            if n == 0:
                continue
            plaus_set = plaus.get(cls, set())
            if not plaus_set:
                continue
            plaus_n = sum(c for k, c in counts.items() if k in plaus_set)
            rate = plaus_n / n * 100
            label = labels.get(cls, cls)
            top_pred, top_count = counts.most_common(1)[0]
            in_plausible = top_pred in plaus_set
            mark = "✓" if rate >= 60 else ("⚠" if rate >= 30 else "✗")
            sections.append(
                f"- {mark} **{label}** — {rate:.0f}% plausible. "
                f"Model's top pick: {top_pred} "
                f"({'within' if in_plausible else 'outside'} plausible set)."
            )
        sections.append("")

    sections.append("### Takeaways for retraining")
    sections.append("")
    sections.append(
        "- Classes where plausible-match is low indicate either (a) genuine domain shift, "
        "(b) class mismatch between the native dataset and CCSN, or (c) under-representation "
        "in CCSN's 2,543 training images.")
    sections.append(
        "- Adding sorted images from TJNU and WEBCAM into the training set should "
        "lift performance on these classes substantially.")
    sections.append(
        "- The Clear / Fog / Rainbow classes you've added aren't in CCSN, so this report "
        "doesn't measure them — but TJNU class 4 (Clear sky) and WEBCAM 'obsc' contribute "
        "ready-labelled images for those classes once sorted.")
    sections.append("")

    OUTPUT.write_text("\n".join(sections))
    print(f"\nWrote {OUTPUT}")
    print(f"({OUTPUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
