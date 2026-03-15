"""
tests/test_summarise.py
Unit tests for the summarisation module (extractive backend).
"""
from __future__ import annotations
import pytest
from backend.app.core.summarise import (
    summarise_text, summarise_transcript, summarise_chapters, _extractive_summary,
)

LONG_TEXT = (
    "Machine learning is a subset of artificial intelligence that focuses on "
    "building systems that learn from data. Neural networks are computational "
    "models inspired by the human brain. Deep learning uses many layers to "
    "extract hierarchical features from raw input. Gradient descent is the "
    "optimisation algorithm used to train these models by minimising loss. "
    "Regularisation techniques prevent overfitting on training data. "
    "Transfer learning allows models pre-trained on large datasets to be "
    "fine-tuned for specific downstream tasks efficiently."
)

SEGMENTS = [
    {"id": i, "start": float(i * 5), "end": float(i * 5 + 5), "text": sent}
    for i, sent in enumerate(LONG_TEXT.split(". "))
]

CHAPTERS = [
    {"start": 0.0,  "end": 20.0, "title": "Introduction to ML",      "segment_count": 4},
    {"start": 20.0, "end": 40.0, "title": "Training and Optimisation", "segment_count": 3},
]


class TestExtractiveSummary:
    def test_returns_string(self):
        assert isinstance(_extractive_summary(LONG_TEXT), str)

    def test_non_empty(self):
        assert _extractive_summary(LONG_TEXT).strip() != ""

    def test_shorter_than_input(self):
        result = _extractive_summary(LONG_TEXT, max_sentences=3)
        assert len(result) < len(LONG_TEXT)

    def test_single_sentence_passthrough(self):
        sent = "Machine learning is fascinating and important for AI research"
        result = _extractive_summary(sent, max_sentences=3)
        assert isinstance(result, str) and len(result) > 0

    def test_max_sentences_respected(self):
        result = _extractive_summary(LONG_TEXT, max_sentences=2)
        # Very rough check — should not be the entire text
        assert len(result) < len(LONG_TEXT)

    def test_very_short_text(self):
        result = _extractive_summary("Short text.")
        assert isinstance(result, str)


class TestSummariseText:
    def test_extractive_backend(self):
        result = summarise_text(LONG_TEXT, backend="extractive")
        assert isinstance(result, str) and len(result) > 0

    def test_empty_text_returns_empty(self):
        assert summarise_text("", backend="extractive") == ""

    def test_whitespace_returns_empty(self):
        assert summarise_text("   \n  ", backend="extractive") == ""

    def test_result_is_condensed(self):
        result = summarise_text(LONG_TEXT, backend="extractive")
        assert len(result) <= len(LONG_TEXT)


class TestSummariseTranscript:
    def test_returns_string(self):
        result = summarise_transcript(SEGMENTS, backend="extractive")
        assert isinstance(result, str)

    def test_non_empty(self):
        assert summarise_transcript(SEGMENTS, backend="extractive").strip() != ""

    def test_empty_segments(self):
        result = summarise_transcript([], backend="extractive")
        assert result == ""

    def test_single_segment(self):
        single = [{"id": 0, "start": 0.0, "end": 5.0,
                   "text": "Machine learning is transforming many industries today"}]
        result = summarise_transcript(single, backend="extractive")
        assert isinstance(result, str)


class TestSummariseChapters:
    def test_returns_list(self):
        result = summarise_chapters(SEGMENTS, CHAPTERS, backend="extractive")
        assert isinstance(result, list)

    def test_one_entry_per_chapter(self):
        result = summarise_chapters(SEGMENTS, CHAPTERS, backend="extractive")
        assert len(result) == len(CHAPTERS)

    def test_required_fields(self):
        result = summarise_chapters(SEGMENTS, CHAPTERS, backend="extractive")
        for entry in result:
            assert {"title", "start", "end", "summary"} <= entry.keys()

    def test_titles_match_chapters(self):
        result = summarise_chapters(SEGMENTS, CHAPTERS, backend="extractive")
        for entry, ch in zip(result, CHAPTERS):
            assert entry["title"] == ch["title"]

    def test_empty_chapters(self):
        result = summarise_chapters(SEGMENTS, [], backend="extractive")
        assert result == []

    def test_summary_is_string(self):
        result = summarise_chapters(SEGMENTS, CHAPTERS, backend="extractive")
        for entry in result:
            assert isinstance(entry["summary"], str)
