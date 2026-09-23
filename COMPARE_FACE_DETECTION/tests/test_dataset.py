from pathlib import Path

from face_benchmark.dataset import parse_wider_annotations


def test_parse_wider_annotations(tmp_path: Path) -> None:
    annotation = tmp_path / "annotations.txt"
    annotation.write_text(
        "0--Parade/0_Parade_test.jpg\n2\n10 20 30 40 0 0 0 0 0 0\n1 2 3 4 0 0 0 0 0 0\n",
        encoding="utf-8",
    )
    records = parse_wider_annotations(annotation, tmp_path / "images")
    assert len(records) == 1
    assert records[0].image_id == "0--Parade/0_Parade_test.jpg"
    assert records[0].boxes_xywh == ((10.0, 20.0, 30.0, 40.0), (1.0, 2.0, 3.0, 4.0))

