from __future__ import annotations

from importlib.metadata import version
from pathlib import Path
from typing import Any

import numpy as np

from .constants import LABELS
from .metrics import classification_metrics


def prepare_images(images: np.ndarray) -> np.ndarray:
    if images.ndim != 3 or images.shape[1:] != (48, 48):
        raise ValueError("Ảnh phải có dạng N x 48 x 48.")
    if len(images) == 0:
        raise ValueError("Không có ảnh để xử lý.")
    return images[..., None].astype(np.float32, copy=False)


class EmotionFineTuner:
    def __init__(self, *, initial_weights: Path, batch_size: int) -> None:
        try:
            from deepface import DeepFace
            from deepface.models.demography.DemographyUtils import EMOTION_LABELS
        except ImportError as exc:
            raise RuntimeError("Thiếu DeepFace hoặc TensorFlow trong môi trường.") from exc

        actual_labels = tuple(str(label).title() for label in EMOTION_LABELS)
        if actual_labels != LABELS:
            raise RuntimeError(f"Thứ tự nhãn DeepFace không khớp: {actual_labels}.")
        self.client = DeepFace.build_model(
            model_name="Emotion",
            task="facial_attribute",
        )
        self.model = self.client.model
        self.initial_weights = initial_weights.expanduser().resolve()
        if not self.initial_weights.exists():
            raise FileNotFoundError(f"Không tìm thấy trọng số ban đầu: {self.initial_weights}")
        self.model.load_weights(str(self.initial_weights))
        self.batch_size = batch_size
        self.deepface_version = version("deepface")

    def predict_scores(self, images: np.ndarray) -> np.ndarray:
        return np.asarray(
            self.model.predict(
                prepare_images(images),
                batch_size=self.batch_size,
                verbose=0,
            ),
            dtype=np.float64,
        )

    def fit(
        self,
        *,
        training_images: np.ndarray,
        training_labels: np.ndarray,
        validation_images: np.ndarray,
        validation_labels: np.ndarray,
        checkpoint_path: Path,
        class_weight: dict[int, float] | None,
        seed: int,
        epochs: int,
        learning_rate: float,
        patience: int,
        min_delta: float,
        deterministic_ops: bool,
        augmentation: dict[str, Any],
    ) -> dict[str, Any]:
        import tensorflow as tf

        tf.keras.utils.set_random_seed(seed)
        if deterministic_ops:
            tf.config.experimental.enable_op_determinism()

        train_x = prepare_images(training_images)
        validation_x = prepare_images(validation_images)
        training_model = self._training_model(tf, augmentation, seed)
        training_model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"],
        )

        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        tracker = self._validation_tracker(
            tf=tf,
            validation_images=validation_x,
            validation_labels=validation_labels,
            checkpoint_path=checkpoint_path,
            patience=patience,
            min_delta=min_delta,
        )
        history = training_model.fit(
            train_x,
            training_labels,
            validation_data=(validation_x, validation_labels),
            batch_size=self.batch_size,
            epochs=epochs,
            class_weight=class_weight,
            callbacks=[tracker],
            shuffle=True,
            verbose=2,
        )
        self.model.load_weights(str(checkpoint_path))
        return {
            "epochs_requested": epochs,
            "epochs_completed": len(history.history.get("loss", [])),
            "best_epoch": tracker.best_epoch,
            "best_validation_macro_f1": tracker.best_score,
            "validation_by_epoch": tracker.records,
            "keras_history": {
                key: [float(value) for value in values]
                for key, values in history.history.items()
            },
        }

    def _training_model(self, tf: Any, augmentation: dict[str, Any], seed: int) -> Any:
        inputs = tf.keras.Input(shape=(48, 48, 1), name="fer2013_image")
        output = inputs
        if bool(augmentation.get("horizontal_flip", False)):
            output = tf.keras.layers.RandomFlip(
                "horizontal", seed=seed, name="random_horizontal_flip"
            )(output)
        rotation = float(augmentation.get("rotation_factor", 0.0))
        if rotation > 0:
            output = tf.keras.layers.RandomRotation(
                rotation,
                fill_mode="nearest",
                seed=seed + 1,
                name="random_rotation",
            )(output)
        translation = float(augmentation.get("translation_factor", 0.0))
        if translation > 0:
            output = tf.keras.layers.RandomTranslation(
                translation,
                translation,
                fill_mode="nearest",
                seed=seed + 2,
                name="random_translation",
            )(output)
        contrast = float(augmentation.get("contrast_factor", 0.0))
        if contrast > 0:
            output = tf.keras.layers.RandomContrast(
                contrast,
                seed=seed + 3,
                name="random_contrast",
            )(output)
        return tf.keras.Model(
            inputs=inputs,
            outputs=self.model(output),
            name="emotion_finetuning",
        )

    def _validation_tracker(
        self,
        *,
        tf: Any,
        validation_images: np.ndarray,
        validation_labels: np.ndarray,
        checkpoint_path: Path,
        patience: int,
        min_delta: float,
    ) -> Any:
        base_model = self.model
        batch_size = self.batch_size

        class MacroF1Checkpoint(tf.keras.callbacks.Callback):
            def __init__(self) -> None:
                super().__init__()
                scores = np.asarray(
                    base_model.predict(
                        validation_images,
                        batch_size=batch_size,
                        verbose=0,
                    )
                )
                metrics = classification_metrics(
                    validation_labels,
                    np.argmax(scores, axis=1).astype(np.int64),
                )
                self.best_score = float(metrics["macro_f1"])
                self.best_epoch = 0
                self.wait = 0
                self.records: list[dict[str, Any]] = [
                    {
                        "epoch": 0,
                        "macro_f1": self.best_score,
                        "accuracy": float(metrics["accuracy"]),
                        "balanced_accuracy": float(metrics["balanced_accuracy"]),
                        "checkpoint_updated": True,
                    }
                ]
                base_model.save_weights(str(checkpoint_path))

            def on_epoch_end(
                self,
                epoch: int,
                logs: dict[str, Any] | None = None,
            ) -> None:
                scores = np.asarray(
                    base_model.predict(
                        validation_images,
                        batch_size=batch_size,
                        verbose=0,
                    )
                )
                metrics = classification_metrics(
                    validation_labels,
                    np.argmax(scores, axis=1).astype(np.int64),
                )
                score = float(metrics["macro_f1"])
                improved = score > self.best_score + min_delta
                if improved:
                    self.best_score = score
                    self.best_epoch = epoch + 1
                    self.wait = 0
                    base_model.save_weights(str(checkpoint_path))
                else:
                    self.wait += 1
                record: dict[str, Any] = {
                    "epoch": epoch + 1,
                    "macro_f1": score,
                    "accuracy": float(metrics["accuracy"]),
                    "balanced_accuracy": float(metrics["balanced_accuracy"]),
                    "checkpoint_updated": improved,
                }
                if logs:
                    for key, value in logs.items():
                        if np.isscalar(value):
                            record[key] = float(value)
                    logs["val_macro_f1"] = score
                self.records.append(record)
                print(
                    f"[finetune] epoch={epoch + 1} "
                    f"validation_macro_f1={score:.4f} "
                    f"best={self.best_score:.4f}",
                    flush=True,
                )
                if self.wait >= patience:
                    self.model.stop_training = True

        return MacroF1Checkpoint()
