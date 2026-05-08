"""Pre-sort TJNU images using the trained CCSN cloud classifier.

Runs each TJNU image through the ResNet50V2 model and saves predictions
to a JSON file for review in the sorting website.

Usage:
    1. Download TJNU dataset and extract to data/TJNU-GCD/
    2. Run: python presort_tjnu.py
    3. Open sort_review.html to review predictions
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import tensorflow as tf
from tensorflow.keras.applications.resnet_v2 import preprocess_input
from tensorflow.keras.preprocessing.image import load_img, img_to_array

# --- Config ---
MODEL_PATH = Path("models/cloud_resnet50v2.keras")
TJNU_DIR = Path("data/TJNU-GCD/GCD")
CCSN_CLASSES = ["Ac", "As", "Cb", "Cc", "Ci", "Cs", "Ct", "Cu", "Ns", "Sc", "St"]
OUTPUT_PATH = Path("data/tjnu_predictions.json")
IMG_SIZE = (224, 224)

# TJNU class folders → description mapping
TJNU_CLASSES = {
    "1": "Cumulus",
    "2": "Altocumulus & Cirrocumulus",
    "3": "Cirrus & Cirrostratus",
    "4": "Clear sky",
    "5": "Stratocumulus, Stratus & Altostratus",
    "6": "Cumulonimbus & Nimbostratus",
    "7": "Mixed cloud",
}

# Best-guess mapping from TJNU class to CCSN primary class
TJNU_TO_CCSN_HINT = {
    "1": "Cu",
    "2": "Ac",   # Could be Ac or Cc
    "3": "Ci",   # Could be Ci or Cs
    "4": "Clear",
    "5": "Sc",   # Could be Sc, St, or As
    "6": "Cb",   # Could be Cb or Ns
    "7": "Mixed",
}


FOLDER_TO_CLASS = {
    "1_cumulus": "1",
    "2_altocumulus": "2",
    "3_cirrus": "3",
    "4_clearsky": "4",
    "5_stratocumulus": "5",
    "6_cumulonimbus": "6",
    "7_mixed": "7",
}


def find_tjnu_images(tjnu_dir: Path) -> list[dict]:
    """Find all images in the TJNU dataset directory."""
    images = []
    for path in sorted(tjnu_dir.rglob("*.jpg")):
        # Determine TJNU class from parent folder name
        tjnu_class = None
        for parent in path.parents:
            folder = parent.name
            if folder in FOLDER_TO_CLASS:
                tjnu_class = FOLDER_TO_CLASS[folder]
                break
            if folder in TJNU_CLASSES:
                tjnu_class = folder
                break

        images.append({
            "path": str(path.relative_to(tjnu_dir)),
            "abs_path": str(path),
            "tjnu_class": tjnu_class,
            "tjnu_label": TJNU_CLASSES.get(tjnu_class, "Unknown"),
            "tjnu_hint": TJNU_TO_CCSN_HINT.get(tjnu_class, "Unknown"),
        })

    return images


def predict_batch(
    model: tf.keras.Model,
    image_paths: list[str],
    batch_size: int = 32,
) -> list[dict]:
    """Run model predictions on a batch of images."""
    results = []

    for i in range(0, len(image_paths), batch_size):
        batch_paths = image_paths[i : i + batch_size]
        batch_imgs = []

        for p in batch_paths:
            try:
                img = load_img(p, target_size=IMG_SIZE)
                arr = img_to_array(img)
                batch_imgs.append(preprocess_input(arr))
            except Exception as e:
                print(f"  Skipping {p}: {e}")
                batch_imgs.append(np.zeros((224, 224, 3)))

        batch_arr = np.array(batch_imgs)
        preds = model.predict(batch_arr, verbose=0)

        for j, pred in enumerate(preds):
            top3_idx = pred.argsort()[-3:][::-1]
            results.append({
                "top1": CCSN_CLASSES[top3_idx[0]],
                "top1_conf": float(pred[top3_idx[0]]),
                "top2": CCSN_CLASSES[top3_idx[1]],
                "top2_conf": float(pred[top3_idx[1]]),
                "top3": CCSN_CLASSES[top3_idx[2]],
                "top3_conf": float(pred[top3_idx[2]]),
            })

        done = min(i + batch_size, len(image_paths))
        print(f"  Processed {done}/{len(image_paths)} images")

    return results


def main() -> None:
    if not TJNU_DIR.exists():
        print(f"TJNU dataset not found at {TJNU_DIR}")
        print("Download from: https://drive.google.com/file/d/1dsgoEQLqR3YrOMBC_hOsVEUQC7HuV2fN/view")
        print(f"Extract to: {TJNU_DIR}/")
        return

    if not MODEL_PATH.exists():
        print(f"Model not found at {MODEL_PATH}")
        return

    print("Loading model...")
    model = tf.keras.models.load_model(MODEL_PATH)

    print("Finding TJNU images...")
    images = find_tjnu_images(TJNU_DIR)
    print(f"Found {len(images)} images")

    if not images:
        print("No images found. Check the TJNU directory structure.")
        return

    print("Running predictions...")
    abs_paths = [img["abs_path"] for img in images]
    predictions = predict_batch(model, abs_paths)

    # Merge predictions into image records
    output = []
    for img, pred in zip(images, predictions):
        output.append({
            "path": img["path"],
            "tjnu_class": img["tjnu_class"],
            "tjnu_label": img["tjnu_label"],
            "tjnu_hint": img["tjnu_hint"],
            "predicted": pred["top1"],
            "confidence": round(pred["top1_conf"] * 100, 1),
            "top2": pred["top2"],
            "top2_conf": round(pred["top2_conf"] * 100, 1),
            "top3": pred["top3"],
            "top3_conf": round(pred["top3_conf"] * 100, 1),
            "assigned": None,  # User's final decision — filled in by review UI
        })

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(output, indent=2))
    print(f"\nPredictions saved to {OUTPUT_PATH}")
    print(f"Open sort_review.html to review and sort images.")


if __name__ == "__main__":
    main()
