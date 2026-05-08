"""Pre-sort WEBCAM aviation dataset using the trained cloud classifier.

Runs each WEBCAM image through the ResNet50V2 model and saves predictions
to a JSON file for review in the sorting website.

Usage:
    1. Download WEBCAM_v1.zip and extract to data/WEBCAM/WEBCAM_v1/
    2. Run: python presort_webcam.py
    3. Open sort_review_webcam.html to review predictions
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
WEBCAM_DIR = Path("data/WEBCAM/WEBCAM_v1")
CCSN_CLASSES = ["Ac", "As", "Cb", "Cc", "Ci", "Cs", "Ct", "Cu", "Ns", "Sc", "St"]
OUTPUT_PATH = Path("data/webcam_predictions.json")
IMG_SIZE = (224, 224)

# WEBCAM folder → label and best-guess mapping
WEBCAM_CLASSES = {
    "ac": "Altocumulus",
    "cb": "Cumulonimbus",
    "ci": "Cirrus",
    "clear": "Clear sky",
    "cu": "Fair-weather Cumulus",
    "obsc": "Obscured / Fog",
    "precip": "Precipitation / Rain",
    "st": "Stratus",
    "tcu": "Towering Cumulus",
}

WEBCAM_TO_HINT = {
    "ac": "Ac",
    "cb": "Cb",
    "ci": "Ci",
    "clear": "Clear",
    "cu": "Cu",
    "obsc": "Fog",
    "precip": "Ns",
    "st": "St",
    "tcu": "Cb",
}


def find_webcam_images(webcam_dir: Path) -> list[dict]:
    """Find all images in the WEBCAM dataset directory."""
    images = []
    for path in sorted(webcam_dir.rglob("*")):
        if path.suffix.lower() not in (".jpg", ".jpeg", ".png"):
            continue

        webcam_class = None
        for parent in path.parents:
            if parent.name in WEBCAM_CLASSES:
                webcam_class = parent.name
                break

        images.append({
            "path": str(path.relative_to(webcam_dir)),
            "abs_path": str(path),
            "webcam_class": webcam_class,
            "webcam_label": WEBCAM_CLASSES.get(webcam_class, "Unknown"),
            "webcam_hint": WEBCAM_TO_HINT.get(webcam_class, "Unknown"),
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
    if not WEBCAM_DIR.exists():
        print(f"WEBCAM dataset not found at {WEBCAM_DIR}")
        print("Download from: https://github.com/MarcusCoteFIT/webcam-ground-based-cloud-image-dataset/releases")
        print(f"Extract to: {WEBCAM_DIR}/")
        return

    if not MODEL_PATH.exists():
        print(f"Model not found at {MODEL_PATH}")
        return

    print("Loading model...")
    model = tf.keras.models.load_model(MODEL_PATH)

    print("Finding WEBCAM images...")
    images = find_webcam_images(WEBCAM_DIR)
    print(f"Found {len(images)} images")

    if not images:
        print("No images found. Check the WEBCAM directory structure.")
        return

    print("Running predictions...")
    abs_paths = [img["abs_path"] for img in images]
    predictions = predict_batch(model, abs_paths)

    # Merge predictions into image records
    output = []
    for img, pred in zip(images, predictions):
        output.append({
            "path": img["path"],
            "webcam_class": img["webcam_class"],
            "webcam_label": img["webcam_label"],
            "webcam_hint": img["webcam_hint"],
            "predicted": pred["top1"],
            "confidence": round(pred["top1_conf"] * 100, 1),
            "top2": pred["top2"],
            "top2_conf": round(pred["top2_conf"] * 100, 1),
            "top3": pred["top3"],
            "top3_conf": round(pred["top3_conf"] * 100, 1),
            "assigned": None,
        })

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(output, indent=2))
    print(f"\nPredictions saved to {OUTPUT_PATH}")
    print(f"Open sort_review_webcam.html to review and sort images.")


if __name__ == "__main__":
    main()
