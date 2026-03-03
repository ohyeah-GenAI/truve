"""Baseline bot detection placeholder."""


def detect_bot(event: dict) -> dict:
    """Run a minimal bot detector.

    Returns a consistent output schema for downstream integration.
    """
    score = 0.0
    label = "human"
    return {"score": score, "label": label, "event_id": event.get("id")}
