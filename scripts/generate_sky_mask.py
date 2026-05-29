"""Generate a one-time sky mask for the Windy webcam using SegFormer-B0
(ADE20K). Saves PNG mask and a small JSON with bounding box.

Usage:
    python scripts/generate_sky_mask.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from transformers import SegformerImageProcessor, SegformerForSemanticSegmentation

ROOT = Path(__file__).resolve().parent.parent
WEBCAM_IMG = ROOT / "data" / "webcam_sample.jpg"
MASK_PNG = ROOT / "data" / "webcam_sky_mask.png"
MASK_JSON = ROOT / "data" / "webcam_sky_mask.json"
OVERLAY_PNG = ROOT / "data" / "webcam_sky_overlay.png"

MODEL_NAME = "nvidia/segformer-b0-finetuned-ade-512-512"
SKY_CLASS_ID = 2  # ADE20K class 2 = "sky"


def main() -> None:
    if not WEBCAM_IMG.exists():
        print(f"Sample webcam image not found at {WEBCAM_IMG}")
        return

    print(f"Loading {MODEL_NAME}...")
    processor = SegformerImageProcessor.from_pretrained(MODEL_NAME)
    model = SegformerForSemanticSegmentation.from_pretrained(MODEL_NAME).eval()

    print(f"Loading webcam image: {WEBCAM_IMG}")
    img = Image.open(WEBCAM_IMG).convert("RGB")
    orig_w, orig_h = img.size
    print(f"  Original size: {orig_w}x{orig_h}")

    print("Running SegFormer...")
    inputs = processor(images=img, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
    logits = outputs.logits  # (1, num_classes, H/4, W/4)

    # Upsample to original size
    upsampled = torch.nn.functional.interpolate(
        logits, size=(orig_h, orig_w), mode="bilinear", align_corners=False
    )
    labels = upsampled.argmax(dim=1)[0].cpu().numpy()

    sky_mask = (labels == SKY_CLASS_ID).astype(np.uint8) * 255
    sky_pixels = int((sky_mask > 0).sum())
    sky_pct = sky_pixels / sky_mask.size * 100
    print(f"  Sky pixels: {sky_pixels:,} ({sky_pct:.1f}% of image)")

    if sky_pct < 5:
        print("  WARNING: very little sky detected. Check the image and model output.")

    # Compute bounding box of sky region
    ys, xs = np.where(sky_mask > 0)
    if len(ys) == 0:
        print("  ERROR: no sky pixels found")
        return
    bbox = {
        "x_min": int(xs.min()),
        "x_max": int(xs.max()),
        "y_min": int(ys.min()),
        "y_max": int(ys.max()),
        "width": int(xs.max() - xs.min() + 1),
        "height": int(ys.max() - ys.min() + 1),
    }

    # Mask out watermark areas (top-left cam name, top-right timestamp)
    # These are roughly top 30px and known regions
    pre_count = sky_pixels
    sky_mask[:30, :230] = 0   # "Taylors Mistake Cam 01" logo top-left
    sky_mask[:30, -260:] = 0  # Timestamp top-right
    post_count = int((sky_mask > 0).sum())
    print(f"  Removed {pre_count - post_count} pixels for watermark/timestamp")

    # Save mask as PNG
    Image.fromarray(sky_mask).save(MASK_PNG)
    print(f"  Saved mask to {MASK_PNG}")

    # Save metadata
    mask_data = {
        "source_image": str(WEBCAM_IMG.relative_to(ROOT)),
        "model": MODEL_NAME,
        "image_size": {"width": orig_w, "height": orig_h},
        "sky_bbox": bbox,
        "sky_pixel_count": post_count,
        "sky_percent": post_count / sky_mask.size * 100,
        "ade20k_class_used": SKY_CLASS_ID,
    }
    MASK_JSON.write_text(json.dumps(mask_data, indent=2))
    print(f"  Saved metadata to {MASK_JSON}")

    # Save overlay visualization for review
    overlay = np.array(img).astype(float)
    mask_3ch = np.stack([sky_mask] * 3, axis=-1) / 255.0
    # Brighten sky pixels (visualization)
    overlay[..., 0] += mask_3ch[..., 0] * 0  # red channel unchanged in sky
    overlay[..., 1] += mask_3ch[..., 1] * 30  # green slightly up
    overlay[..., 2] += mask_3ch[..., 2] * 60  # blue boosted in sky
    # Dim non-sky
    non_sky = (1 - mask_3ch) * 0.4
    overlay = overlay * (1 - non_sky) + np.zeros_like(overlay) * non_sky
    overlay = np.clip(overlay, 0, 255).astype(np.uint8)
    Image.fromarray(overlay).save(OVERLAY_PNG)
    print(f"  Saved overlay preview to {OVERLAY_PNG}")

    print("\nDone.")
    print(f"\nBounding box: x={bbox['x_min']}-{bbox['x_max']}, "
          f"y={bbox['y_min']}-{bbox['y_max']} "
          f"({bbox['width']}x{bbox['height']})")


if __name__ == "__main__":
    main()
