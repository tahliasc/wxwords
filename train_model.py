"""Train a MobileNetV2-based cloud classifier on the CCSN dataset.

Uses tf.keras ImageDataGenerator with proper MobileNetV2 preprocessing.
Two-phase: frozen base then fine-tune.
"""

from pathlib import Path

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.model_selection import train_test_split
import shutil

# --- Config ---
DATA_DIR = Path("data/CCSN_v2")
SPLIT_DIR = Path("data/split")
MODEL_OUT = Path("models/cloud_classifier.keras")
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS_PHASE1 = 20
EPOCHS_PHASE2 = 30


def create_split_dirs() -> None:
    """Split dataset into train/val directories for ImageDataGenerator."""
    if SPLIT_DIR.exists():
        shutil.rmtree(SPLIT_DIR)

    class_dirs = sorted([d for d in DATA_DIR.iterdir() if d.is_dir()])

    for cls_dir in class_dirs:
        cls_name = cls_dir.name
        images = list(cls_dir.glob("*.jpg")) + list(cls_dir.glob("*.jpeg")) + list(cls_dir.glob("*.png"))

        train_imgs, val_imgs = train_test_split(
            images, test_size=0.2, random_state=42
        )

        for split, img_list in [("train", train_imgs), ("val", val_imgs)]:
            dest = SPLIT_DIR / split / cls_name
            dest.mkdir(parents=True, exist_ok=True)
            for img in img_list:
                shutil.copy2(img, dest / img.name)

    print(f"Split complete: {SPLIT_DIR}")


def main() -> None:
    print("Creating train/val split...")
    create_split_dirs()

    # Use MobileNetV2's own preprocessing
    train_datagen = ImageDataGenerator(
        preprocessing_function=keras.applications.mobilenet_v2.preprocess_input,
        rotation_range=15,
        width_shift_range=0.1,
        height_shift_range=0.1,
        horizontal_flip=True,
        zoom_range=0.1,
    )

    val_datagen = ImageDataGenerator(
        preprocessing_function=keras.applications.mobilenet_v2.preprocess_input,
    )

    train_gen = train_datagen.flow_from_directory(
        SPLIT_DIR / "train",
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        shuffle=True,
    )

    val_gen = val_datagen.flow_from_directory(
        SPLIT_DIR / "val",
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        shuffle=False,
    )

    class_names = list(train_gen.class_indices.keys())
    num_classes = len(class_names)
    print(f"Classes ({num_classes}): {class_names}")

    # Build model
    base = keras.applications.MobileNetV2(
        input_shape=(*IMG_SIZE, 3),
        include_top=False,
        weights="imagenet",
    )
    base.trainable = False

    model = keras.Sequential([
        base,
        layers.GlobalAveragePooling2D(),
        layers.BatchNormalization(),
        layers.Dropout(0.3),
        layers.Dense(256, activation="relu"),
        layers.BatchNormalization(),
        layers.Dropout(0.2),
        layers.Dense(num_classes, activation="softmax"),
    ])

    # Phase 1: Train head
    print("\n--- Phase 1: Training head (base frozen) ---")
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=1e-3),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=EPOCHS_PHASE1,
        callbacks=[
            keras.callbacks.EarlyStopping(
                monitor="val_accuracy", patience=5, restore_best_weights=True
            ),
        ],
    )

    # Phase 2: Unfreeze top layers
    print("\n--- Phase 2: Fine-tuning ---")
    base.trainable = True
    for layer in base.layers[:-50]:
        layer.trainable = False

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=5e-5),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=EPOCHS_PHASE2,
        callbacks=[
            keras.callbacks.EarlyStopping(
                monitor="val_accuracy", patience=7, restore_best_weights=True
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor="val_loss", factor=0.5, patience=3, min_lr=1e-6
            ),
        ],
    )

    val_loss, val_acc = model.evaluate(val_gen)
    print(f"\nFinal validation accuracy: {val_acc:.4f}")

    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    model.save(MODEL_OUT)
    print(f"Model saved to {MODEL_OUT}")

    # Save class names
    import json
    with open(MODEL_OUT.parent / "class_names.json", "w") as f:
        json.dump(class_names, f)
    print(f"Class names: {class_names}")


if __name__ == "__main__":
    main()