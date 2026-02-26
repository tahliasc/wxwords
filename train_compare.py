"""Compare backbone architectures for cloud classification.

Tests EfficientNetB0, ResNet50V2, and MobileNetV2 on CCSN dataset.
Phase 1: frozen base. Phase 2: fine-tune top layers.
"""

from pathlib import Path
import json
import sys

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.preprocessing.image import ImageDataGenerator

SPLIT_DIR = Path("data/split")
MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)

IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS_P1 = 20
EPOCHS_P2 = 40

BACKBONES = {
    "efficientnet": {
        "base_fn": keras.applications.EfficientNetB0,
        "preprocess": keras.applications.efficientnet.preprocess_input,
        "unfreeze_layers": 40,
    },
    "resnet50v2": {
        "base_fn": keras.applications.ResNet50V2,
        "preprocess": keras.applications.resnet_v2.preprocess_input,
        "unfreeze_layers": 30,
    },
    "mobilenetv2": {
        "base_fn": keras.applications.MobileNetV2,
        "preprocess": keras.applications.mobilenet_v2.preprocess_input,
        "unfreeze_layers": 50,
    },
}


def create_generators(preprocess_fn: callable) -> tuple:
    train_datagen = ImageDataGenerator(
        preprocessing_function=preprocess_fn,
        rotation_range=20,
        width_shift_range=0.15,
        height_shift_range=0.15,
        horizontal_flip=True,
        zoom_range=0.15,
        shear_range=0.1,
        brightness_range=(0.8, 1.2),
    )
    val_datagen = ImageDataGenerator(preprocessing_function=preprocess_fn)

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
    return train_gen, val_gen


def build_model(config: dict, num_classes: int) -> tuple[keras.Model, keras.Model]:
    base = config["base_fn"](
        input_shape=(*IMG_SIZE, 3),
        include_top=False,
        weights="imagenet",
    )
    base.trainable = False

    model = keras.Sequential([
        base,
        layers.GlobalAveragePooling2D(),
        layers.BatchNormalization(),
        layers.Dense(512, activation="relu"),
        layers.Dropout(0.4),
        layers.Dense(256, activation="relu"),
        layers.Dropout(0.3),
        layers.Dense(num_classes, activation="softmax"),
    ])
    return model, base


def train_backbone(name: str) -> float:
    print(f"\n{'='*60}")
    print(f"  Training: {name.upper()}")
    print(f"{'='*60}\n")

    config = BACKBONES[name]
    train_gen, val_gen = create_generators(config["preprocess"])
    num_classes = len(train_gen.class_indices)
    class_names = list(train_gen.class_indices.keys())

    # Compute class weights to handle imbalance
    from sklearn.utils.class_weight import compute_class_weight
    class_weights = compute_class_weight(
        "balanced",
        classes=np.arange(num_classes),
        y=train_gen.classes,
    )
    class_weight_dict = dict(enumerate(class_weights))
    print(f"Class weights: {class_weight_dict}")

    model, base = build_model(config, num_classes)

    # Phase 1: frozen base
    print(f"\n--- Phase 1: Head training ({name}) ---")
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=1e-3),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=EPOCHS_P1,
        class_weight=class_weight_dict,
        callbacks=[
            keras.callbacks.EarlyStopping(
                monitor="val_accuracy", patience=5, restore_best_weights=True
            ),
        ],
    )

    p1_loss, p1_acc = model.evaluate(val_gen)
    print(f"\n  Phase 1 val accuracy ({name}): {p1_acc:.4f}")

    # Phase 2: fine-tune
    print(f"\n--- Phase 2: Fine-tuning ({name}) ---")
    base.trainable = True
    n_unfreeze = config["unfreeze_layers"]
    for layer in base.layers[:-n_unfreeze]:
        layer.trainable = False

    trainable_count = sum(1 for l in base.layers if l.trainable)
    print(f"  Unfroze {trainable_count} of {len(base.layers)} base layers")

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=1e-4),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=EPOCHS_P2,
        class_weight=class_weight_dict,
        callbacks=[
            keras.callbacks.EarlyStopping(
                monitor="val_accuracy", patience=8, restore_best_weights=True
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor="val_loss", factor=0.5, patience=4, min_lr=1e-6
            ),
        ],
    )

    final_loss, final_acc = model.evaluate(val_gen)
    print(f"\n  FINAL val accuracy ({name}): {final_acc:.4f}")

    # Save
    out_path = MODELS_DIR / f"cloud_{name}.keras"
    model.save(out_path)
    print(f"  Saved to {out_path}")

    with open(MODELS_DIR / "class_names.json", "w") as f:
        json.dump(class_names, f)

    return final_acc


def main() -> None:
    # Allow training a single backbone via CLI arg
    if len(sys.argv) > 1:
        name = sys.argv[1]
        if name not in BACKBONES:
            print(f"Unknown backbone: {name}. Choose from: {list(BACKBONES.keys())}")
            sys.exit(1)
        acc = train_backbone(name)
        print(f"\n{name}: {acc:.4f}")
        return

    results = {}
    for name in BACKBONES:
        results[name] = train_backbone(name)

    print(f"\n{'='*60}")
    print("  RESULTS COMPARISON")
    print(f"{'='*60}")
    for name, acc in sorted(results.items(), key=lambda x: -x[1]):
        print(f"  {name:20s}: {acc:.4f}")

    best = max(results, key=results.get)
    print(f"\n  Best: {best} ({results[best]:.4f})")


if __name__ == "__main__":
    main()
