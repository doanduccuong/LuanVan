from __future__ import annotations

import math
from collections import Counter, defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from io import StringIO
from statistics import median

import numpy as np
import pandas as pd
from sequenzo import SequenceData, get_distance_matrix
from sequenzo.clustering import (
    cluster_labels_from_kmedoids_result,
    medoid_indices_from_kmedoids_result,
    observation_silhouette,
)
from sequenzo.clustering.k_medoids_range import k_medoids_range


EXPRESSION_STATES = ("Angry", "Disgust", "Fear", "Happy", "Sad", "Surprise", "Neutral")
VOID_STATE = "%"
PREPROCESSING_VERSION = "touchpoint-segments-v1"
ALGORITHM_VERSION = "sequenzo-0.1.42:OM-CONSTANT2-INDEL1:PAM"


class SequenceAnalysisError(ValueError):
    pass


@dataclass(frozen=True)
class SequenceObservation:
    observation_id: str
    visit_id: str
    touchpoint_id: str
    touchpoint_name: str
    observed_at: object
    expression_label: str
    expression_confidence: float | None


@dataclass(frozen=True)
class VisitSequence:
    visit_id: str
    states: tuple[str, ...]
    metadata: tuple[dict, ...]


@dataclass(frozen=True)
class AnalysisConfig:
    min_states: int = 3
    min_cluster_size_abs: int = 2
    min_cluster_ratio: float = 0.05
    k_min: int = 2
    k_max: int | None = None
    asw_tolerance: float = 0.02
    random_state: int = 42

    def validate(self) -> None:
        if self.min_states < 2:
            raise SequenceAnalysisError("min_states phải từ 2 trở lên")
        if self.min_cluster_size_abs < 2:
            raise SequenceAnalysisError("min_cluster_size_abs phải từ 2 trở lên")
        if not 0 < self.min_cluster_ratio <= 0.5:
            raise SequenceAnalysisError("min_cluster_ratio phải nằm trong (0, 0.5]")
        if self.k_min < 2:
            raise SequenceAnalysisError("k_min phải từ 2 trở lên")
        if self.k_max is not None and self.k_max < self.k_min:
            raise SequenceAnalysisError("k_max không được nhỏ hơn k_min")
        if not 0 <= self.asw_tolerance <= 0.2:
            raise SequenceAnalysisError("asw_tolerance phải nằm trong [0, 0.2]")


@dataclass
class PreparedSequences:
    sequences: list[VisitSequence]
    received_visit_count: int
    excluded: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class ClusteredSequences:
    selected_k: int
    average_silhouette_width: float
    distance_matrix: np.ndarray
    candidate_metrics: list[dict]
    clusters: list[dict]
    assignments: list[dict]
    warnings: list[str]


def _timestamp_key(value: object) -> str:
    isoformat = getattr(value, "isoformat", None)
    return isoformat() if callable(isoformat) else str(value)


def _representative(segment: list[SequenceObservation]) -> SequenceObservation:
    counts = Counter(row.expression_label for row in segment)
    confidence_totals: dict[str, float] = defaultdict(float)
    for row in segment:
        confidence_totals[row.expression_label] += float(row.expression_confidence or 0.0)
    state_rank = {state: index for index, state in enumerate(EXPRESSION_STATES)}
    winning_label = min(
        counts,
        key=lambda label: (-counts[label], -confidence_totals[label], state_rank[label]),
    )
    candidates = [row for row in segment if row.expression_label == winning_label]
    return max(candidates, key=lambda row: (float(row.expression_confidence or 0.0), row.observation_id))


def prepare_visit_sequences(
    observations: list[SequenceObservation],
    *,
    min_states: int,
) -> PreparedSequences:
    grouped: dict[str, list[SequenceObservation]] = defaultdict(list)
    for row in observations:
        if row.expression_label not in EXPRESSION_STATES:
            continue
        grouped[row.visit_id].append(row)

    excluded: list[dict] = []
    warnings: list[str] = []
    prepared: list[VisitSequence] = []
    for visit_id in sorted(grouped):
        rows = sorted(
            grouped[visit_id],
            key=lambda row: (_timestamp_key(row.observed_at), row.observation_id),
        )
        touchpoints_by_time: dict[str, set[str]] = defaultdict(set)
        for row in rows:
            touchpoints_by_time[_timestamp_key(row.observed_at)].add(row.touchpoint_id)
        conflicting_times = {key for key, values in touchpoints_by_time.items() if len(values) > 1}
        if conflicting_times:
            rows = [row for row in rows if _timestamp_key(row.observed_at) not in conflicting_times]
            warnings.append(
                f"Visit {visit_id}: loại {len(conflicting_times)} mốc thời gian xung đột điểm chạm"
            )

        segments: list[list[SequenceObservation]] = []
        for row in rows:
            if not segments or segments[-1][0].touchpoint_id != row.touchpoint_id:
                segments.append([row])
            else:
                segments[-1].append(row)

        states: list[str] = []
        metadata: list[dict] = []
        for segment in segments:
            representative = _representative(segment)
            states.append(representative.expression_label)
            confidences = [float(row.expression_confidence) for row in segment if row.expression_confidence is not None]
            metadata.append(
                {
                    "touchpoint_id": representative.touchpoint_id,
                    "touchpoint_name": representative.touchpoint_name,
                    "started_at": _timestamp_key(segment[0].observed_at),
                    "ended_at": _timestamp_key(segment[-1].observed_at),
                    "observation_ids": [row.observation_id for row in segment],
                    "support_count": len(segment),
                    "mean_confidence": float(sum(confidences) / len(confidences)) if confidences else None,
                }
            )

        if len(states) < min_states:
            excluded.append(
                {
                    "visit_id": visit_id,
                    "reason": "INSUFFICIENT_STATES",
                    "actual_states": len(states),
                    "required_states": min_states,
                }
            )
            continue
        prepared.append(VisitSequence(visit_id=visit_id, states=tuple(states), metadata=tuple(metadata)))

    return PreparedSequences(
        sequences=prepared,
        received_visit_count=len(grouped),
        excluded=excluded,
        warnings=warnings,
    )


def build_om_distance_matrix(sequences: list[VisitSequence]) -> np.ndarray:
    max_length = max(len(item.states) for item in sequences)
    rows = []
    time_columns = [f"state_{index + 1}" for index in range(max_length)]
    for item in sequences:
        padded = list(item.states) + [VOID_STATE] * (max_length - len(item.states))
        rows.append({"visit_id": item.visit_id, **dict(zip(time_columns, padded, strict=True))})
    frame = pd.DataFrame(rows)
    with redirect_stdout(StringIO()):
        sequence_data = SequenceData(
            frame,
            time=time_columns,
            states=[*EXPRESSION_STATES, VOID_STATE],
            labels=[*EXPRESSION_STATES, VOID_STATE],
            id_col="visit_id",
            void=VOID_STATE,
        )
        result = get_distance_matrix(
            seqdata=sequence_data,
            method="OM",
            sm="CONSTANT",
            indel=1,
            norm="none",
            full_matrix=True,
        )
    matrix = np.asarray(result, dtype=np.float64)
    if matrix.shape != (len(sequences), len(sequences)):
        raise SequenceAnalysisError("Sequenzo trả ma trận khoảng cách sai kích thước")
    if not np.allclose(matrix, matrix.T) or not np.allclose(np.diag(matrix), 0):
        raise SequenceAnalysisError("Ma trận khoảng cách OM không đối xứng hoặc đường chéo khác 0")
    if np.any(matrix < 0) or not np.isfinite(matrix).all():
        raise SequenceAnalysisError("Ma trận khoảng cách OM chứa giá trị không hợp lệ")
    return matrix


def cluster_visit_sequences(
    sequences: list[VisitSequence],
    config: AnalysisConfig,
) -> ClusteredSequences:
    config.validate()
    n_sequences = len(sequences)
    if n_sequences < 4:
        raise SequenceAnalysisError("Cần ít nhất 4 chuỗi hợp lệ để phân cụm")

    n_min = max(config.min_cluster_size_abs, math.ceil(config.min_cluster_ratio * n_sequences))
    unique_sequence_count = len({item.states for item in sequences})
    calculated_k_max = min(n_sequences - 1, n_sequences // n_min, unique_sequence_count)
    if config.k_max is not None:
        calculated_k_max = min(calculated_k_max, config.k_max)
    if calculated_k_max < config.k_min:
        raise SequenceAnalysisError(
            f"Không đủ dữ liệu để tạo ít nhất {config.k_min} cụm, mỗi cụm tối thiểu {n_min} chuỗi"
        )

    matrix = build_om_distance_matrix(sequences)
    kvals = list(range(config.k_min, calculated_k_max + 1))
    with redirect_stdout(StringIO()):
        range_result = k_medoids_range(
            matrix,
            kvals,
            method="PAM",
            npass=1,
            n_boot=1,
            random_state=config.random_state,
        )

    solutions: dict[int, dict] = {}
    candidate_metrics: list[dict] = []
    degenerate_silhouette_candidates: list[tuple[int, int]] = []
    for k in kvals:
        column = f"cluster{k}"
        raw_assignments = np.asarray(range_result.clustering[column], dtype=np.int32)
        labels = cluster_labels_from_kmedoids_result(raw_assignments)
        medoid_indices = medoid_indices_from_kmedoids_result(raw_assignments)
        sizes = np.bincount(labels, minlength=k)
        raw_silhouette = np.asarray(observation_silhouette(matrix, labels), dtype=np.float64)
        undefined_silhouette_count = int(np.count_nonzero(~np.isfinite(raw_silhouette)))
        # Sequenzo can return NaN for a degenerate observation when both its
        # within-cluster and nearest-cluster mean distances are zero.  The
        # standard silhouette convention for an undefined observation is 0:
        # it provides no evidence of either separation or misassignment.
        silhouette = np.nan_to_num(raw_silhouette, nan=0.0, posinf=0.0, neginf=0.0)
        asw = float(np.mean(silhouette))
        rejected = bool(np.any(sizes < n_min))
        metric = {
            "k": k,
            "asw": asw,
            "min_cluster_size": int(sizes.min()),
            "max_cluster_size": int(sizes.max()),
            "required_min_cluster_size": n_min,
            "accepted": not rejected,
            "rejection_reason": "CLUSTER_TOO_SMALL" if rejected else None,
            "undefined_silhouette_count": undefined_silhouette_count,
        }
        candidate_metrics.append(metric)
        if undefined_silhouette_count:
            degenerate_silhouette_candidates.append((k, undefined_silhouette_count))
        if not rejected:
            solutions[k] = {
                "raw": raw_assignments,
                "labels": labels,
                "medoids": medoid_indices,
                "silhouette": silhouette,
                "asw": asw,
                "sizes": sizes,
            }

    if not solutions:
        raise SequenceAnalysisError("Không có phương án K nào thỏa ngưỡng kích thước cụm")
    best_asw = max(item["asw"] for item in solutions.values())
    selected_k = min(
        k for k, item in solutions.items() if best_asw - item["asw"] <= config.asw_tolerance
    )
    selected = solutions[selected_k]

    clusters: list[dict] = []
    assignments: list[dict] = []
    for cluster_label, medoid_index in enumerate(selected["medoids"]):
        member_indices = np.flatnonzero(selected["labels"] == cluster_label)
        distances = matrix[member_indices, medoid_index]
        cluster_id = cluster_label + 1
        clusters.append(
            {
                "cluster_id": cluster_id,
                "medoid_visit_id": sequences[int(medoid_index)].visit_id,
                "medoid_sequence": list(sequences[int(medoid_index)].states),
                "size": int(len(member_indices)),
                "proportion": float(len(member_indices) / n_sequences),
                "mean_silhouette": float(np.mean(selected["silhouette"][member_indices])),
                "median_distance": float(median(float(value) for value in distances)),
            }
        )
        for member_index in member_indices:
            sequence = sequences[int(member_index)]
            assignments.append(
                {
                    "visit_id": sequence.visit_id,
                    "cluster_id": cluster_id,
                    "sequence": list(sequence.states),
                    "sequence_metadata": list(sequence.metadata),
                    "distance_to_medoid": float(matrix[int(member_index), int(medoid_index)]),
                    "silhouette": float(selected["silhouette"][int(member_index)]),
                }
            )

    warnings: list[str] = []
    if degenerate_silhouette_candidates:
        details = ", ".join(
            f"K={k}: {count}" for k, count in degenerate_silhouette_candidates
        )
        warnings.append(
            "Silhouette không xác định ở một số quan sát suy biến được quy ước bằng 0 "
            f"({details})"
        )
    if unique_sequence_count < min(n_sequences - 1, n_sequences // n_min):
        warnings.append(
            f"Giới hạn K tối đa ở {unique_sequence_count} vì chỉ có từng đó chuỗi trạng thái phân biệt"
        )
    if selected_k == calculated_k_max:
        warnings.append("Phương án được chọn nằm tại K lớn nhất trong phạm vi khảo sát")
    if any(item["silhouette"] < 0 for item in assignments):
        warnings.append("Có chuỗi có silhouette âm; cần xem lại khả năng diễn giải của cụm")
    return ClusteredSequences(
        selected_k=selected_k,
        average_silhouette_width=float(selected["asw"]),
        distance_matrix=matrix,
        candidate_metrics=candidate_metrics,
        clusters=clusters,
        assignments=sorted(assignments, key=lambda item: item["visit_id"]),
        warnings=warnings,
    )
