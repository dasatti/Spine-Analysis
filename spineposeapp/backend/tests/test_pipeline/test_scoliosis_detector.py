from unittest.mock import MagicMock, patch

import pytest

from app.pipeline import scoliosis_detector
from app.pipeline.metric_engine import (
    AVAIL_NO_BACK,
    merge_ai_classifications,
)
from app.pipeline.scoliosis_detector import ScoliosisPrediction, predict_scoliosis, resolve_weights_path


def test_resolve_weights_path_uses_default_model():
    path = resolve_weights_path(None)
    assert path.name == "yolo26n-scoliosis.pt"
    assert path.exists()


@patch("app.pipeline.scoliosis_detector.settings")
@patch("app.pipeline.scoliosis_detector._get_model")
def test_predict_scoliosis_positive(mock_get_model, mock_settings, tmp_path):
    mock_settings.scoliosis_keypoint_conf_threshold = 0.25
    mock_settings.scoliosis_min_keypoints = 3
    mock_settings.scoliosis_lateral_index_threshold = 0.05

    image_path = tmp_path / "back.jpg"
    image_path.write_bytes(b"fake")

    class TensorValue:
        def __init__(self, value):
            self.value = value

        def item(self):
            return self.value

        def tolist(self):
            return self.value

    class FakeBoxes:
        cls = [TensorValue(1), TensorValue(0), TensorValue(0), TensorValue(0)]
        conf = [TensorValue(0.95), TensorValue(0.90), TensorValue(0.88), TensorValue(0.87)]
        xyxy = [
            TensorValue([100.0, 50.0, 300.0, 500.0]),
            TensorValue([150.0, 80.0, 160.0, 90.0]),
            TensorValue([220.0, 180.0, 230.0, 190.0]),
            TensorValue([260.0, 280.0, 270.0, 290.0]),
        ]

        def __len__(self):
            return 4

    result = MagicMock()
    result.boxes = FakeBoxes()
    result.names = {0: "KeyPoint", 1: "back"}
    result.orig_shape = (640, 640)

    model = MagicMock()
    model.predict.return_value = [result]
    mock_get_model.return_value = model

    scoliosis_detector._get_model.cache_clear()
    prediction = predict_scoliosis(str(image_path))
    assert prediction.class_name == "scoliosis"
    assert prediction.keypoint_count == 3
    assert prediction.lateral_index >= 0.05
    assert len(prediction.detections) == 4


@patch("app.pipeline.scoliosis_detector.predict_scoliosis")
def test_merge_ai_classifications_includes_scoliosis(mock_predict):
    mock_predict.return_value = ScoliosisPrediction(
        class_name="normal",
        confidence=0.91,
        lateral_index=0.02,
        keypoint_count=4,
        detections=(
            scoliosis_detector.ScoliosisDetectionBox(
                "keypoint", 150.0, 80.0, 160.0, 90.0, 0.9
            ),
        ),
        image_width=640,
        image_height=640,
    )
    metrics = {"ai_classification": {}, "normal_ranges": {}}
    merged = merge_ai_classifications(metrics, None, "/tmp/back.jpg")
    scoliosis = merged["ai_classification"]["scoliosis"]
    assert scoliosis["value"] == "normal"
    assert scoliosis["lateral_index"] == 0.02
    assert scoliosis["keypoint_count"] == 4
    assert len(scoliosis["detections"]) == 1
    assert scoliosis["detections"][0]["class"] == "keypoint"
    mock_predict.assert_called_once_with("/tmp/back.jpg")


def test_merge_ai_classifications_without_back_frame():
    metrics = {"ai_classification": {}, "normal_ranges": {}}
    merged = merge_ai_classifications(metrics, None, None)
    assert merged["ai_classification"]["scoliosis"]["availability"] == AVAIL_NO_BACK
