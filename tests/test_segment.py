"""
tests/test_segment.py
Unit tests for chapter segmentation and title extraction.
"""
from __future__ import annotations
import pytest
from backend.app.core.segment import segment_chapters, _make_title, _clean


def _make_segs(texts: list[str], gap: float = 5.0) -> list[dict]:
    segs, t = [], 0.0
    for i, text in enumerate(texts):
        segs.append({"id": i, "start": t, "end": t + gap, "text": text})
        t += gap
    return segs


TECH_TALK = _make_segs([
    "Today we will discuss machine learning fundamentals and neural networks",
    "Supervised learning requires labelled training data for optimisation",
    "Neural networks learn hierarchical representations from raw inputs",
    "Backpropagation computes gradients through the computational graph",
    "Regularisation techniques like dropout prevent model overfitting",
    "Now let us explore natural language processing and transformers",
    "Attention mechanisms allow models to focus on relevant tokens",
    "BERT and GPT are examples of large pre-trained language models",
    "Fine-tuning adapts pre-trained weights to downstream NLP tasks",
    "Tokenisation splits raw text into subword or word-level units",
    "Computer vision deals with extracting information from images",
    "Convolutional networks apply learned filters across spatial dimensions",
    "Object detection locates and classifies multiple objects in one pass",
    "Semantic segmentation assigns a class label to every pixel",
    "Transfer learning from ImageNet improves vision model accuracy greatly",
])


class TestClean:
    def test_strips_extra_whitespace(self):
        assert _clean("  hello   world  ") == "hello world"

    def test_collapses_newlines(self):
        assert _clean("line\none") == "line one"

    def test_tabs_collapsed(self):
        assert _clean("a\t\tb") == "a b"


class TestMakeTitle:
    def test_returns_string(self):
        assert isinstance(_make_title(["Machine learning is a key AI subfield"]), str)

    def test_not_empty(self):
        assert _make_title(["Something useful and interesting here"]) != ""

    def test_truncates_long_text(self):
        title = _make_title(["word " * 50], max_len=72)
        assert len(title) <= 75  # +3 for ellipsis

    def test_handles_all_short_texts(self):
        title = _make_title(["hi", "ok", "yes"])
        assert isinstance(title, str)

    def test_empty_list_returns_chapter(self):
        assert _make_title([]) == "Chapter"

    def test_prefers_informative_sentence(self):
        texts = [
            "um",
            "Neural networks learn complex hierarchical feature representations",
            "ok",
        ]
        title = _make_title(texts)
        assert len(title) > 5


class TestSegmentChapters:
    def test_returns_list(self):
        assert isinstance(segment_chapters(TECH_TALK), list)

    def test_at_least_one_chapter(self):
        assert len(segment_chapters(TECH_TALK)) >= 1

    def test_first_chapter_starts_at_zero(self):
        chapters = segment_chapters(TECH_TALK)
        assert chapters[0]["start"] == pytest.approx(TECH_TALK[0]["start"])

    def test_last_chapter_ends_at_last_segment(self):
        chapters = segment_chapters(TECH_TALK)
        assert chapters[-1]["end"] == pytest.approx(TECH_TALK[-1]["end"])

    def test_chapters_contiguous(self):
        chapters = segment_chapters(TECH_TALK)
        for i in range(len(chapters) - 1):
            assert chapters[i]["end"] == pytest.approx(chapters[i + 1]["start"]), \
                f"Gap between chapter {i} and {i + 1}"

    def test_all_titles_non_empty(self):
        for ch in segment_chapters(TECH_TALK):
            assert isinstance(ch["title"], str) and len(ch["title"]) > 0

    def test_required_fields(self):
        for ch in segment_chapters(TECH_TALK):
            assert {"start", "end", "title", "segment_count"} <= ch.keys()

    def test_segment_counts_sum_to_total(self):
        chapters = segment_chapters(TECH_TALK)
        assert sum(ch["segment_count"] for ch in chapters) == len(TECH_TALK)

    def test_empty_input(self):
        assert segment_chapters([]) == []

    def test_single_segment(self):
        single = _make_segs(["A single meaningful sentence about machine learning"])
        chapters = segment_chapters(single)
        assert len(chapters) == 1

    def test_large_window_forces_single_chapter(self):
        chapters = segment_chapters(TECH_TALK, window_size=1000)
        assert len(chapters) == 1

    def test_chapter_end_gte_start(self):
        for ch in segment_chapters(TECH_TALK):
            assert ch["end"] >= ch["start"]
