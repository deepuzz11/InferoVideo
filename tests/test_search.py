"""
tests/test_search.py
Unit tests for the search module — TF-IDF and informative-filter logic.
"""
from __future__ import annotations
import pytest
from backend.app.core.search import search_segments, _is_informative

SEGMENTS = [
    {"id": 0, "start": 0.0,  "end": 5.0,  "text": "The quick brown fox jumps over the lazy dog"},
    {"id": 1, "start": 5.0,  "end": 10.0, "text": "Machine learning models require large datasets for training"},
    {"id": 2, "start": 10.0, "end": 15.0, "text": "Python is a popular programming language for data science"},
    {"id": 3, "start": 15.0, "end": 20.0, "text": "Neural networks learn representations from raw data"},
    {"id": 4, "start": 20.0, "end": 25.0, "text": "Deep learning has revolutionized computer vision tasks"},
    {"id": 5, "start": 25.0, "end": 27.0, "text": "music"},
    {"id": 6, "start": 27.0, "end": 32.0, "text": "Gradient descent optimises the loss function iteratively"},
]


class TestIsInformative:
    def test_long_text_passes(self):
        assert _is_informative("This is a reasonably long sentence here") is True

    def test_short_text_fails(self):
        assert _is_informative("music") is False

    def test_exact_five_words_passes(self):
        assert _is_informative("one two three four five") is True

    def test_four_words_fails(self):
        assert _is_informative("one two three four") is False

    def test_empty_fails(self):
        assert _is_informative("") is False


class TestSearchTFIDF:
    def test_returns_results_for_relevant_query(self):
        results = search_segments(SEGMENTS, "machine learning neural network", top_k=3)
        assert len(results) > 0

    def test_top_result_relevant(self):
        results = search_segments(SEGMENTS, "deep learning computer vision", top_k=5)
        assert results
        assert any("deep learning" in r["text"].lower() or "neural" in r["text"].lower()
                   for r in results)

    def test_short_filler_segments_filtered(self):
        results = search_segments(SEGMENTS, "music songs audio", top_k=5)
        for r in results:
            assert _is_informative(r["text"]), f"Short segment leaked: {r['text']}"

    def test_empty_query_returns_empty(self):
        assert search_segments(SEGMENTS, "", top_k=5) == []

    def test_whitespace_query_returns_empty(self):
        assert search_segments(SEGMENTS, "   ", top_k=5) == []

    def test_empty_segments_returns_empty(self):
        assert search_segments([], "machine learning", top_k=5) == []

    def test_top_k_respected(self):
        results = search_segments(SEGMENTS, "learning data", top_k=2)
        assert len(results) <= 2

    def test_top_k_one(self):
        results = search_segments(SEGMENTS, "python programming", top_k=1)
        assert len(results) <= 1

    def test_required_fields_present(self):
        results = search_segments(SEGMENTS, "python programming", top_k=3)
        for r in results:
            assert "text" in r
            assert "start" in r
            assert "end" in r
            assert "score" in r
            assert "backend" in r

    def test_scores_in_valid_range(self):
        results = search_segments(SEGMENTS, "gradient loss function", top_k=5)
        for r in results:
            assert 0.0 <= r["score"] <= 1.0

    def test_backend_label_is_tfidf(self):
        results = search_segments(SEGMENTS, "learning", top_k=3, backend="tfidf")
        for r in results:
            assert r["backend"] == "tfidf"

    def test_results_ordered_by_score_descending(self):
        results = search_segments(SEGMENTS, "deep learning gradient", top_k=5)
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_no_semantic_match_returns_empty(self):
        results = search_segments(SEGMENTS, "xyzzy frobnicate quux blargh", top_k=5)
        assert results == [] or all(r["score"] == 0.0 for r in results)

    def test_single_segment_corpus(self):
        single = [{"id": 0, "start": 0.0, "end": 5.0,
                   "text": "Machine learning is fascinating and very important"}]
        results = search_segments(single, "machine learning", top_k=1)
        assert len(results) <= 1

    def test_start_less_than_end_in_results(self):
        results = search_segments(SEGMENTS, "python data science", top_k=5)
        for r in results:
            assert r["start"] < r["end"]
