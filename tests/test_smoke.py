from vqa.pipeline import run_vqa_pipeline
from bot_detection.detector import detect_bot


def test_vqa_pipeline_schema():
    result = run_vqa_pipeline("sample.jpg", "What is shown?")
    assert {"image_path", "question", "answer", "confidence"}.issubset(result.keys())


def test_bot_detector_schema():
    result = detect_bot({"id": "evt-1", "ua": "test"})
    assert {"score", "label", "event_id"}.issubset(result.keys())
