"""Offline ablations of pixel scaling and face cropping, without changing the service."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

from app.engine import LABELS, RetinaFaceMobileNetDetector, align_face, estimate_face_alignment


def image_rows(root: Path) -> list[dict[str, str]]:
    with (root / "events.csv").open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def classification(expected: np.ndarray, scores: np.ndarray) -> dict:
    predicted = scores.argmax(axis=1)
    classes = {}
    for index, label in enumerate(LABELS):
        tp = int(((expected == index) & (predicted == index)).sum())
        fp = int(((expected != index) & (predicted == index)).sum())
        fn = int(((expected == index) & (predicted != index)).sum())
        classes[label] = {"correct": tp, "support": tp + fn,
                          "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0}
    return {"correct": int((expected == predicted).sum()), "count": len(expected),
            "accuracy": float((expected == predicted).mean()),
            "macro_f1": sum(row["f1"] for row in classes.values()) / len(LABELS),
            "predicted_distribution": dict(Counter(LABELS[i] for i in predicted)),
            "per_class": classes, "predicted_labels": [LABELS[i] for i in predicted]}


def main(dataset: Path, output: Path, original_weights: Path, finetuned_weights: Path) -> None:
    detector = RetinaFaceMobileNetDetector()
    from deepface import DeepFace
    from deepface.modules import preprocessing, detection

    client = DeepFace.build_model(model_name="Emotion", task="facial_attribute")
    events = image_rows(dataset)
    output.mkdir(parents=True, exist_ok=True)
    previews = output / "previews"
    previews.mkdir(exist_ok=True)
    records, tensors, examples = [], {}, {}
    by_hash = {}
    # Reconstruct the exact service tensor, including RGB/BGR conversion and
    # normalized 224x224 padding before Emotion's grayscale 48x48 conversion.
    def service_tensor(image: np.ndarray) -> np.ndarray:
        face = detection.extract_faces(image, detector_backend="skip", enforce_detection=False,
                                       align=False, normalize_face=True)[0]["face"]
        bgr = face[:, :, ::-1]
        padded = preprocessing.resize_image(img=bgr, target_size=(224, 224))[0]
        return client._preprocess_image(padded).astype(np.float32)

    for event in events:
        path = dataset / event["image_path"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest in by_hash:
            records.append(by_hash[digest])
            continue
        image = cv2.imread(str(path))
        detections = detector.detect(image)
        if len(detections) != 1:
            raise ValueError(f"Expected one face: {path}, got {len(detections)}")
        det = detections[0]
        height, width = image.shape[:2]
        x1, y1, x2, y2 = (int(v) for v in det["box"])
        x1, y1 = max(x1, 0), max(y1, 0)
        x2, y2 = min(x2, width), min(y2, height)
        box = image[y1:y2, x1:x2]
        aligned = align_face(image, det["landmarks"])
        matrix = estimate_face_alignment(det["landmarks"]) * 2.0
        aligned224 = cv2.warpAffine(image, matrix, (224, 224), flags=cv2.INTER_LINEAR)
        dx, dy = round((x2 - x1) * 0.1), round((y2 - y1) * 0.1)
        expanded = image[max(0,y1-dy):min(height,y2+dy),max(0,x1-dx):min(width,x2+dx)]
        geometries = {
            "deployed_arcface112": service_tensor(aligned),
            "arcface224": service_tensor(aligned224),
            "bbox_padded": service_tensor(box),
            "bbox_expanded_padded": service_tensor(expanded),
            "full_source_padded": service_tensor(image),
            "bbox_direct48": cv2.resize(cv2.cvtColor(box, cv2.COLOR_BGR2GRAY), (48,48)).astype(np.float32)/255,
        }
        index = len(tensors)
        tensors[digest] = geometries
        record = {"index": index, "sha256": digest, "image_path": event["image_path"],
                  "label": event["expected_expression_label"], "source_filename": event["source_filename"],
                  "box": det["box"], "landmarks": det["landmarks"],
                  "deployed_tensor": {"min": float(geometries['deployed_arcface112'].min()),
                                      "max": float(geometries['deployed_arcface112'].max()),
                                      "mean": float(geometries['deployed_arcface112'].mean())}}
        records.append(record)
        by_hash[digest] = record
        label = event["expected_expression_label"]
        if label not in examples:
            examples[label] = record
            cv2.imwrite(str(previews/f"{label}_source.jpg"), image)
            cv2.imwrite(str(previews/f"{label}_bbox.jpg"), box)
            cv2.imwrite(str(previews/f"{label}_aligned112.jpg"), aligned)
            cv2.imwrite(str(previews/f"{label}_tensor48.png"),
                        np.clip(geometries['deployed_arcface112']*255,0,255).astype(np.uint8))
    print(f"Detected {len(tensors)} unique sources for {len(events)} observations", flush=True)
    expected = np.asarray([LABELS.index(event["expected_expression_label"]) for event in events])
    indices = np.asarray([record["index"] for record in records])
    results = {}
    for weights_name, weights_path in (("original", original_weights), ("finetuned", finetuned_weights)):
        client.model.load_weights(str(weights_path))
        results[weights_name] = {}
        for geometry in next(iter(tensors.values())):
            base = np.stack([value[geometry] for value in tensors.values()])[...,None]
            results[weights_name][geometry] = {}
            for scale_name, scale in (("0_to_1", 1.0), ("0_to_255", 255.0)):
                tensor = base * scale
                scores = np.asarray(client.model(tensor, training=False).numpy(), dtype=np.float64)[indices]
                result = classification(expected, scores)
                result["scores"] = scores.tolist()
                result["tensor_range"] = [float(tensor.min()), float(tensor.max())]
                results[weights_name][geometry][scale_name] = result
                print(f"{weights_name:9} {geometry:22} {scale_name:8}: "
                      f"correct={result['correct']}/{len(expected)} macro_f1={result['macro_f1']:.4f}", flush=True)
    summary = {"events": len(events), "unique_images": len(tensors),
               "original_weights_sha256": hashlib.sha256(original_weights.read_bytes()).hexdigest(),
               "finetuned_weights_sha256": hashlib.sha256(finetuned_weights.read_bytes()).hexdigest(),
               "records": records, "results": results,
               "scope": "Offline diagnostic; service, database and thesis remain unchanged"}
    (output/"preprocessing-ablation.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--original-weights", type=Path, required=True)
    parser.add_argument("--finetuned-weights", type=Path, required=True)
    args = parser.parse_args()
    main(args.dataset,args.output,args.original_weights,args.finetuned_weights)
