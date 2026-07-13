from unittest.mock import MagicMock, patch

import pytest

from app.pipeline import kyphosis_classifier, lordosis_classifier, side_view_classifier
from app.pipeline.kyphosis_classifier import predict_kyphosis, resolve_weights_path
from app.pipeline.lordosis_classifier import predict_lordosis
from app.pipeline.side_view_classifier import ClassificationPrediction
from app.pipeline.metric_engine import (
    AVAIL_NO_SIDE,
    merge_ai_classifications,
    merge_kyphosis_classification,
    preserve_ai_classification,
    serialize_ai_classification,
    serialize_kyphosis_classification,
)


def test_resolve_weights_path_uses_default_kyphosis_model():
    path = resolve_weights_path(None)
    assert path.name == "yolo26n-cls-kyphosis.pt"
    assert path.exists()


def test_serialize_ai_classification():
    payload = serialize_ai_classification("lordosis", 0.8123)
    assert payload["value"] == "lordosis"
    assert payload["confidence"] == 0.8123
    assert payload["metric_type"] == "classification"


def test_serialize_kyphosis_classification_alias():
    payload = serialize_kyphosis_classification("kyphosis", 0.9123)
    assert payload["value"] == "kyphosis"
    assert payload["confidence"] == 0.9123


def test_merge_ai_classifications_without_side_frame():
    metrics = {"ai_classification": {}, "normal_ranges": {}}
    merged = merge_ai_classifications(metrics, None)
    assert merged["ai_classification"]["kyphosis"]["availability"] == AVAIL_NO_SIDE
    assert merged["ai_classification"]["lordosis"]["availability"] == AVAIL_NO_SIDE


@patch("app.pipeline.lordosis_classifier.predict_lordosis")
@patch("app.pipeline.kyphosis_classifier.predict_kyphosis")
def test_merge_ai_classifications_with_predictions(mock_kyphosis, mock_lordosis):
    mock_kyphosis.return_value = ClassificationPrediction(class_name="normal", confidence=0.88)
    mock_lordosis.return_value = ClassificationPrediction(class_name="lordosis", confidence=0.91)
    metrics = {"ai_classification": {}, "normal_ranges": {}}
    merged = merge_ai_classifications(metrics, "/tmp/side.jpg")
    assert merged["ai_classification"]["kyphosis"]["value"] == "normal"
    assert merged["ai_classification"]["lordosis"]["value"] == "lordosis"
    assert merged["ai_classification"]["lordosis"]["confidence"] == 0.91


def test_merge_kyphosis_classification_alias():
    metrics = {"ai_classification": {}, "normal_ranges": {}}
    merged = merge_kyphosis_classification(metrics, None)
    assert "kyphosis" in merged["ai_classification"]
    assert "lordosis" in merged["ai_classification"]


def test_preserve_ai_classification():
    prior = {
        "ai_classification": {
            "kyphosis": serialize_ai_classification("kyphosis", 0.91),
            "lordosis": serialize_ai_classification("normal", 0.84),
        }
    }
    new_metrics = {"spinal_curves": {}, "normal_ranges": {}}
    merged = preserve_ai_classification(new_metrics, prior)
    assert merged["ai_classification"]["kyphosis"]["value"] == "kyphosis"
    assert merged["ai_classification"]["lordosis"]["value"] == "normal"


@patch("app.pipeline.side_view_classifier._get_model")
def test_predict_kyphosis_returns_top_class(mock_get_model, tmp_path):
    image_path = tmp_path / "side.jpg"
    image_path.write_bytes(b"fake")

    probs = MagicMock()
    probs.top1 = 1
    probs.top1conf = 0.93

    result = MagicMock()
    result.probs = probs
    result.names = {0: "normal", 1: "kyphosis"}

    model = MagicMock()
    model.predict.return_value = [result]
    mock_get_model.return_value = model

    side_view_classifier._get_model.cache_clear()
    prediction = predict_kyphosis(str(image_path))
    assert prediction.class_name == "kyphosis"
    assert prediction.confidence == pytest.approx(0.93)


@patch("app.pipeline.side_view_classifier._get_model")
def test_predict_lordosis_returns_top_class(mock_get_model, tmp_path):
    image_path = tmp_path / "side.jpg"
    image_path.write_bytes(b"fake")

    probs = MagicMock()
    probs.top1 = 1
    probs.top1conf = 0.87

    result = MagicMock()
    result.probs = probs
    result.names = {0: "normal", 1: "lordosis"}

    model = MagicMock()
    model.predict.return_value = [result]
    mock_get_model.return_value = model

    side_view_classifier._get_model.cache_clear()
    prediction = predict_lordosis(str(image_path))
    assert prediction.class_name == "lordosis"
    assert prediction.confidence == pytest.approx(0.87)
