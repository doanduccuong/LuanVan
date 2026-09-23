import numpy as np

from face_benchmark.metrics import bbox_overlaps, operating_point_metrics, voc_ap
from face_benchmark.types import Detection, ImageRecord


def test_identical_boxes_have_unit_iou() -> None:
    boxes = np.asarray([[10, 20, 30, 40]], dtype=float)
    result = bbox_overlaps(boxes, boxes)
    assert result.shape == (1, 1)
    assert result[0, 0] == 1.0


def test_disjoint_boxes_have_zero_iou() -> None:
    first = np.asarray([[0, 0, 10, 10]], dtype=float)
    second = np.asarray([[20, 20, 30, 30]], dtype=float)
    assert bbox_overlaps(first, second)[0, 0] == 0.0


def test_duplicate_prediction_is_false_positive() -> None:
    record = ImageRecord(
        image_id="event/image.jpg",
        path="unused",
        width=100,
        height=100,
        boxes_xywh=((10, 10, 20, 20),),
    )
    predictions = {
        record.image_id: [
            Detection(10, 10, 30, 30, 0.9),
            Detection(10, 10, 30, 30, 0.8),
        ]
    }
    metrics = operating_point_metrics([record], predictions, 0.0, 0.5)
    assert metrics.precision == 0.5
    assert metrics.recall == 1.0


def test_voc_ap_for_perfect_curve() -> None:
    recall = np.asarray([0.5, 1.0])
    precision = np.asarray([1.0, 1.0])
    assert voc_ap(recall, precision) == 1.0


def test_degenerate_ground_truth_is_ignored() -> None:
    record = ImageRecord(
        image_id="event/image.jpg",
        path="unused",
        width=100,
        height=100,
        boxes_xywh=((0, 0, 0, 0), (10, 10, 20, 20)),
    )
    predictions = {record.image_id: [Detection(10, 10, 30, 30, 0.9)]}
    metrics = operating_point_metrics([record], predictions, 0.0, 0.5)
    assert metrics.precision == 1.0
    assert metrics.recall == 1.0
