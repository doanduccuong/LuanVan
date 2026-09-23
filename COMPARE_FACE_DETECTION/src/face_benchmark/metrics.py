from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from scipy.io import loadmat

from .types import Detection, ImageRecord


def xywh_to_xyxy(boxes: np.ndarray) -> np.ndarray:
    converted = boxes.astype(np.float64, copy=True)
    if converted.size == 0:
        return converted.reshape(0, 4)
    converted[:, 2] = converted[:, 0] + converted[:, 2]
    converted[:, 3] = converted[:, 1] + converted[:, 3]
    return converted


def bbox_overlaps(boxes: np.ndarray, query_boxes: np.ndarray) -> np.ndarray:
    boxes = np.asarray(boxes, dtype=np.float64).reshape(-1, 4)
    query_boxes = np.asarray(query_boxes, dtype=np.float64).reshape(-1, 4)
    overlaps = np.zeros((len(boxes), len(query_boxes)), dtype=np.float64)
    if not len(boxes) or not len(query_boxes):
        return overlaps
    for query_index, query in enumerate(query_boxes):
        query_area = max(0.0, query[2] - query[0] + 1.0) * max(0.0, query[3] - query[1] + 1.0)
        intersection_width = np.maximum(
            0.0, np.minimum(boxes[:, 2], query[2]) - np.maximum(boxes[:, 0], query[0]) + 1.0
        )
        intersection_height = np.maximum(
            0.0, np.minimum(boxes[:, 3], query[3]) - np.maximum(boxes[:, 1], query[1]) + 1.0
        )
        intersection = intersection_width * intersection_height
        box_area = np.maximum(0.0, boxes[:, 2] - boxes[:, 0] + 1.0) * np.maximum(
            0.0, boxes[:, 3] - boxes[:, 1] + 1.0
        )
        union = box_area + query_area - intersection
        valid = union > 0
        overlaps[valid, query_index] = intersection[valid] / union[valid]
    return overlaps


def voc_ap(recall: np.ndarray, precision: np.ndarray) -> float:
    recall_envelope = np.concatenate(([0.0], recall, [1.0]))
    precision_envelope = np.concatenate(([0.0], precision, [0.0]))
    for index in range(precision_envelope.size - 1, 0, -1):
        precision_envelope[index - 1] = max(
            precision_envelope[index - 1], precision_envelope[index]
        )
    changing = np.where(recall_envelope[1:] != recall_envelope[:-1])[0]
    return float(
        np.sum(
            (recall_envelope[changing + 1] - recall_envelope[changing])
            * precision_envelope[changing + 1]
        )
    )


def _image_eval(
    predictions_xywhs: np.ndarray,
    ground_truth_xywh: np.ndarray,
    include_mask: np.ndarray,
    iou_threshold: float,
) -> tuple[np.ndarray, np.ndarray]:
    predictions = predictions_xywhs.copy()
    ground_truth = ground_truth_xywh.copy()
    predictions[:, 2] += predictions[:, 0]
    predictions[:, 3] += predictions[:, 1]
    ground_truth[:, 2] += ground_truth[:, 0]
    ground_truth[:, 3] += ground_truth[:, 1]
    overlaps = bbox_overlaps(predictions[:, :4], ground_truth)
    prediction_recall = np.zeros(len(predictions), dtype=np.float64)
    recalled = np.zeros(len(ground_truth), dtype=np.float64)
    proposal_mask = np.ones(len(predictions), dtype=np.float64)
    for prediction_index in range(len(predictions)):
        if not len(ground_truth):
            break
        best_gt = int(overlaps[prediction_index].argmax())
        best_overlap = overlaps[prediction_index, best_gt]
        if best_overlap >= iou_threshold:
            if include_mask[best_gt] == 0:
                recalled[best_gt] = -1
                proposal_mask[prediction_index] = -1
            elif recalled[best_gt] == 0:
                recalled[best_gt] = 1
        prediction_recall[prediction_index] = np.count_nonzero(recalled == 1)
    return prediction_recall, proposal_mask


def _image_pr_info(
    threshold_count: int,
    predictions: np.ndarray,
    proposal_mask: np.ndarray,
    prediction_recall: np.ndarray,
) -> np.ndarray:
    output = np.zeros((threshold_count, 2), dtype=np.float64)
    for threshold_index in range(threshold_count):
        threshold = 1.0 - (threshold_index + 1) / threshold_count
        included = np.where(predictions[:, 4] >= threshold)[0]
        if not len(included):
            continue
        last = included[-1]
        output[threshold_index, 0] = np.count_nonzero(proposal_mask[: last + 1] == 1)
        output[threshold_index, 1] = prediction_recall[last]
    return output


def _mat_string(value: np.ndarray) -> str:
    return str(value[0][0])


def wider_face_ap(
    predictions: dict[str, dict[str, np.ndarray]],
    ground_truth_dir: Path,
    iou_threshold: float = 0.5,
    threshold_count: int = 1000,
) -> dict[str, float]:
    gt_mat = loadmat(ground_truth_dir / "wider_face_val.mat")
    difficulty_mats = {
        "easy": loadmat(ground_truth_dir / "wider_easy_val.mat")["gt_list"],
        "medium": loadmat(ground_truth_dir / "wider_medium_val.mat")["gt_list"],
        "hard": loadmat(ground_truth_dir / "wider_hard_val.mat")["gt_list"],
    }
    face_boxes = gt_mat["face_bbx_list"]
    events = gt_mat["event_list"]
    files = gt_mat["file_list"]

    all_scores = [
        boxes[:, 4]
        for event in predictions.values()
        for boxes in event.values()
        if len(boxes)
    ]
    if all_scores:
        minimum = min(float(scores.min()) for scores in all_scores)
        maximum = max(float(scores.max()) for scores in all_scores)
        score_range = maximum - minimum
        for event in predictions.values():
            for boxes in event.values():
                if len(boxes):
                    boxes[:, 4] = (boxes[:, 4] - minimum) / score_range if score_range else 1.0

    results: dict[str, float] = {}
    for difficulty, difficulty_gt in difficulty_mats.items():
        face_total = 0
        pr_curve = np.zeros((threshold_count, 2), dtype=np.float64)
        for event_index in range(len(events)):
            event_name = _mat_string(events[event_index])
            image_files = files[event_index][0]
            event_boxes = face_boxes[event_index][0]
            event_keep = difficulty_gt[event_index][0]
            for image_index in range(len(image_files)):
                image_name = _mat_string(image_files[image_index])
                prediction = predictions.get(event_name, {}).get(
                    image_name, np.empty((0, 5), dtype=np.float64)
                )
                gt_boxes = event_boxes[image_index][0].astype(np.float64)
                keep_indices = event_keep[image_index][0].reshape(-1).astype(int)
                face_total += len(keep_indices)
                if not len(gt_boxes) or not len(prediction):
                    continue
                include_mask = np.zeros(len(gt_boxes), dtype=np.float64)
                if len(keep_indices):
                    include_mask[keep_indices - 1] = 1
                prediction_recall, proposal_mask = _image_eval(
                    prediction, gt_boxes, include_mask, iou_threshold
                )
                pr_curve += _image_pr_info(
                    threshold_count, prediction, proposal_mask, prediction_recall
                )
        precision = np.divide(
            pr_curve[:, 1],
            pr_curve[:, 0],
            out=np.zeros(threshold_count, dtype=np.float64),
            where=pr_curve[:, 0] > 0,
        )
        recall = pr_curve[:, 1] / face_total
        results[difficulty] = voc_ap(recall, precision)
    return results


@dataclass(frozen=True)
class OperatingMetrics:
    precision: float
    recall: float
    f1: float
    false_positives_per_image: float
    no_detection_rate: float


def operating_point_metrics(
    records: Iterable[ImageRecord],
    predictions: dict[str, list[Detection]],
    score_threshold: float | None,
    iou_threshold: float,
) -> OperatingMetrics:
    true_positive = 0
    false_positive = 0
    false_negative = 0
    images_with_faces = 0
    images_without_detection = 0
    record_list = list(records)
    for record in record_list:
        valid_ground_truth = [box for box in record.boxes_xywh if box[2] > 0 and box[3] > 0]
        ground_truth = xywh_to_xyxy(np.asarray(valid_ground_truth, dtype=np.float64))
        selected = [
            item
            for item in predictions.get(record.image_id, [])
            if score_threshold is None or item.score >= score_threshold
        ]
        selected.sort(key=lambda item: item.score, reverse=True)
        prediction_boxes = np.asarray(
            [[item.x1, item.y1, item.x2, item.y2] for item in selected], dtype=np.float64
        ).reshape(-1, 4)
        if len(ground_truth):
            images_with_faces += 1
            if not len(prediction_boxes):
                images_without_detection += 1
        matched: set[int] = set()
        overlaps = bbox_overlaps(prediction_boxes, ground_truth)
        for prediction_index in range(len(prediction_boxes)):
            candidates = [
                index
                for index in np.argsort(overlaps[prediction_index])[::-1]
                if index not in matched
            ]
            if candidates and overlaps[prediction_index, candidates[0]] >= iou_threshold:
                matched.add(candidates[0])
                true_positive += 1
            else:
                false_positive += 1
        false_negative += len(ground_truth) - len(matched)
    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return OperatingMetrics(
        precision=precision,
        recall=recall,
        f1=f1,
        false_positives_per_image=false_positive / len(record_list) if record_list else 0.0,
        no_detection_rate=images_without_detection / images_with_faces if images_with_faces else 0.0,
    )
