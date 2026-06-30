"""Tests para shared.confidence."""

from shared.confidence import get_confidence_review_threshold, is_high_confidence


def test_default_threshold():
    assert get_confidence_review_threshold() == 0.7


def test_is_high_confidence():
    assert is_high_confidence(0.85) is True
    assert is_high_confidence(0.5) is False
    assert is_high_confidence(None) is False
