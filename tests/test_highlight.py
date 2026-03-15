"""
tests/test_highlight.py
Unit tests for highlight scoring, selection and merging.
"""
from __future__ import annotations
import numpy as np
import pytest
from backend.app.core.highlight import score_segments, select_highlights, merge_adjacent


def _segs(data):
    return [
        {"id": i, "start": s, "end": e, "text": t, "no_speech_prob": 0.05}
        for i, (t, s, e) in enumerate(data)
    ]


SEGMENTS = _segs([
    ("Machine learning is transforming modern data analysis completely", 0.0, 5.0),
    ("ok", 5.0, 7.0),
    ("Neural networks approximate complex non-linear decision boundaries well", 7.0, 12.0),
    ("Deep learning requires substantial computational resources and large data", 12.0, 17.0),
    ("The gradient descent algorithm minimises the objective loss function", 17.0, 22.0),
])


class TestScoreSegments:
    def test_returns_ndarray(self):
        scores = score_segments(SEGMENTS)
        assert isinstance(scores, np.ndarray)

    def test_length_matches_input(self):
        assert len(score_segments(SEGMENTS)) == len(SEGMENTS)

    def test_scores_bounded_0_1(self):
        scores = score_segments(SEGMENTS)
        assert np.all(scores >= 0.0) and np.all(scores <= 1.0)

    def test_filler_segment_lowest_score(self):
        scores = score_segments(SEGMENTS)
        # index 1 is "ok" — shortest, least informative
        assert scores[1] == scores.min()

    def test_no_speech_prob_penalises_score(self):
        high_noise = [{"id": 0, "start": 0, "end": 5,
                       "text": "Very informative technical content here indeed",
                       "no_speech_prob": 0.99}]
        low_noise  = [{"id": 0, "start": 0, "end": 5,
                       "text": "Very informative technical content here indeed",
                       "no_speech_prob": 0.01}]
        assert score_segments(high_noise)[0] < score_segments(low_noise)[0]

    def test_single_segment(self):
        single = _segs([("Only one segment with meaningful content here", 0.0, 5.0)])
        scores = score_segments(single)
        assert len(scores) == 1


class TestSelectHighlights:
    def test_returns_list(self):
        assert isinstance(select_highlights(SEGMENTS, score_segments(SEGMENTS)), list)

    def test_threshold_1_returns_empty(self):
        assert select_highlights(SEGMENTS, score_segments(SEGMENTS), threshold=1.01) == []

    def test_threshold_0_returns_all(self):
        result = select_highlights(SEGMENTS, score_segments(SEGMENTS), threshold=0.0)
        assert len(result) == len(SEGMENTS)

    def test_selected_above_threshold(self):
        scores = np.array([0.9, 0.2, 0.8, 0.6, 0.4])
        highlights = select_highlights(SEGMENTS, scores, threshold=0.5)
        for h in highlights:
            idx = next(i for i, s in enumerate(SEGMENTS) if s["start"] == h["start"])
            assert scores[idx] >= 0.5

    def test_required_fields(self):
        highlights = select_highlights(SEGMENTS, score_segments(SEGMENTS), threshold=0.0)
        for h in highlights:
            assert {"start", "end", "score", "text"} <= h.keys()


class TestMergeAdjacent:
    def test_empty_input(self):
        assert merge_adjacent([]) == []

    def test_single_item_unchanged(self):
        h = [{"start": 0.0, "end": 5.0, "score": 0.9, "text": "text"}]
        assert merge_adjacent(h) == h

    def test_close_highlights_merged(self):
        h = [
            {"start": 0.0,  "end": 5.0,  "score": 0.8, "text": "a"},
            {"start": 6.0,  "end": 10.0, "score": 0.9, "text": "b"},  # gap=1 < 3
        ]
        merged = merge_adjacent(h, gap=3.0)
        assert len(merged) == 1
        assert merged[0]["end"] == 10.0
        assert merged[0]["score"] == 0.9

    def test_distant_highlights_not_merged(self):
        h = [
            {"start": 0.0,  "end": 5.0,  "score": 0.8, "text": "a"},
            {"start": 20.0, "end": 25.0, "score": 0.7, "text": "b"},  # gap=15 > 3
        ]
        assert len(merge_adjacent(h, gap=3.0)) == 2

    def test_score_takes_maximum_on_merge(self):
        h = [
            {"start": 0.0, "end": 5.0,  "score": 0.5, "text": "a"},
            {"start": 6.0, "end": 10.0, "score": 0.95, "text": "b"},
        ]
        merged = merge_adjacent(h, gap=3.0)
        assert merged[0]["score"] == 0.95

    def test_text_concatenated_on_merge(self):
        h = [
            {"start": 0.0, "end": 5.0,  "score": 0.8, "text": "hello"},
            {"start": 6.0, "end": 10.0, "score": 0.8, "text": "world"},
        ]
        merged = merge_adjacent(h, gap=3.0)
        assert "hello" in merged[0]["text"]
        assert "world" in merged[0]["text"]

    def test_chain_of_three_merged(self):
        h = [
            {"start": 0.0,  "end": 5.0,  "score": 0.8, "text": "a"},
            {"start": 6.0,  "end": 10.0, "score": 0.7, "text": "b"},
            {"start": 11.0, "end": 15.0, "score": 0.9, "text": "c"},
        ]
        merged = merge_adjacent(h, gap=3.0)
        assert len(merged) == 1
        assert merged[0]["end"] == 15.0
