import pytest

from app.pipeline.loader import get_detector


def test_loader_unknown_model_raises_value_error(monkeypatch):
    monkeypatch.setattr("app.pipeline.loader.settings.detector_model", "unknown_model")
    with pytest.raises(ValueError, match="Unknown DETECTOR_MODEL"):
        get_detector()


def test_loader_spinepose_loads_operational_mode(monkeypatch):
    monkeypatch.setattr("app.pipeline.loader.settings.detector_model", "spinepose_v2")
    monkeypatch.setattr("app.pipeline.loader.settings.model_weights_path", None)
    detector = get_detector()
    assert detector.model_name == "spinepose_v2"
    assert detector._stub_mode is False


def test_loader_yolo_loads_operational_mode(monkeypatch):
    monkeypatch.setattr("app.pipeline.loader.settings.detector_model", "yolo_v8")
    monkeypatch.setattr("app.pipeline.loader.settings.model_weights_path", None)
    detector = get_detector()
    assert detector.model_name == "yolo_v8"
    assert detector._stub_mode is False
