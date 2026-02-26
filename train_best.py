"""Extended training of ResNet50V2 (best backbone) with tuned hyperparameters.

- Larger image size (256x256)
- More aggressive augmentation
- Cosine decay learning rate
- Longer fine-tuning with more layers unfrozen
"""

from pathlib import Path
import json

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.preprocessing.image import ImageDataGenerator

SPLIT_DIR = Path("data/split")
MODELS_DIR = Path("models")
MODEL_OUT = MODELS_DIR / "cloud_best.keras"

IMG_SIZE = (224, 224)
BATCH_SIZE = 16  # Smaller batch for better generalization
EPOCHS_P1 = 30
EPOCHS_P2 = 60


def main() -> None:
    preprocess_fn = keras.applications.resnet_v2.preprocess_input

    train_datagen = ImageDataGenerator(
        preprocessing_function=preprocess_fn,
        rotation_range=30,
        width_shift_range=0.2,
        height_shift_range=0.2,
        horizontal_flip=True,
        vertical_flip=False,
        zoom_range=0.2,
        shear_range=0.15,
        brightness_range=(0.7, 1.3),
        fill_mode="reflect",
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

    class_names = list(train_gen.class_indices.keys())
    num_classes = len(class_names)
    print(f"Classes ({num_classes}): {class_names}")

    # Class weights
    from sklearn.utils.class_weight import compute_class_weight
    class_weights = compute_class_weight(
        "balanced", classes=np.arange(num_classes), y=train_gen.classes
    )
    class_weight_dict = dict(enumerate(class_weights))

    # Build model with label smoothing
    base = keras.applications.ResNet50V2(
        input_shape=(*IMG_SIZE, 3),
        include_top=False,
        weights="imagenet",
    )
    base.trainable = False

    model = keras.Sequential([
        base,
        layers.GlobalAveragePooling2D(),
        layers.BatchNormalization(),
        layers.Dense(512, activation="relu",
                     kernel_regularizer=keras.regularizers.l2(1e-4)),
        layers.Dropout(0.5),
        layers.Dense(256, activation="relu",
                     kernel_regularizer=keras.regularizers.l2(1e-4)),
        layers.Dropout(0.4),
        layers.Dense(num_classes, activation="softmax"),
    ])

    # Phase 1: Train head with label smoothing
    print("\n--- Phase 1: Head training (ResNet50V2 extended) ---")
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=5e-4),
        loss=keras.losses.CategoricalCrossentropy(label_smoothing=0.1),
        metrics=["accuracy"],
    )

    model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=EPOCHS_P1,
        class_weight=class_weight_dict,
        callbacks=[
            keras.callbacks.EarlyStopping(
                monitor="val_accuracy", patience=8, restore_best_weights=True
            ),
        ],
    )

    p1_loss, p1_acc = model.evaluate(val_gen)
    print(f"\n  Phase 1 val accuracy: {p1_acc:.4f}")

    # Phase 2: Fine-tune more layers with cosine decay
    print("\n--- Phase 2: Fine-tuning (more layers, cosine decay) ---")
    base.trainable = True
    # Unfreeze more layers than before
    for layer in base.layers[:-80]:
        layer.trainable = False

    trainable = sum(1 for l in base.layers if l.trainable)
    print(f"  Unfroze {trainable} of {len(base.layers)} base layers")

    steps_per_epoch = len(train_gen)
    total_steps = steps_per_epoch * EPOCHS_P2

    lr_schedule = keras.optimizers.schedules.CosineDecay(
        initial_learning_rate=5e-5,
        decay_steps=total_steps,
        alpha=1e-6,
    )

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=lr_schedule),
        loss=keras.losses.CategoricalCrossentropy(label_smoothing=0.1),
        metrics=["accuracy"],
    )

    model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=EPOCHS_P2,
        class_weight=class_weight_dict,
        callbacks=[
            keras.callbacks.EarlyStopping(
                monitor="val_accuracy", patience=12, restore_best_weights=True
            ),
        ],
    )

    final_loss, final_acc = model.evaluate(val_gen)
    print(f"\n  FINAL val accuracy: {final_acc:.4f}")

    model.save(MODEL_OUT)
    print(f"  Model saved to {MODEL_OUT}")

    with open(MODELS_DIR / "class_names.json", "w") as f:
        json.dump(class_names, f)


if __name__ == "__main__":
    main()
