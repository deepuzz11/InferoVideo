from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)

def extract_insights(segments: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Extract named entities and top keywords from transcript segments.
    """
    full_text = " ".join(s["text"] for s in segments if s.get("text"))
    if not full_text.strip():
        return {"entities": [], "keywords": []}

    # 1. Named Entity Recognition (NER)
    entities = []
    try:
        import spacy
        # Load small model - should be downloaded during setup
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model 'en_core_web_sm' not found. Skipping NER.")
            nlp = None

        if nlp:
            # entities can be long, so we process in chunks if needed
            doc = nlp(full_text[:100000]) # cap for safety
            
            seen = set()
            for ent in doc.ents:
                if ent.label_ in ("PERSON", "ORG", "GPE", "PRODUCT", "EVENT"):
                    cleaned = ent.text.strip().title()
                    if cleaned and cleaned not in seen and len(cleaned) > 2:
                        entities.append({"text": cleaned, "label": ent.label_})
                        seen.add(cleaned)
    except ImportError:
        logger.warning("spaCy not installed. Skipping NER.")

    # 2. Keyword Extraction (TF-IDF based)
    keywords = []
    try:
        # We treat each segment as a "document" to find globally important words
        texts = [s["text"] for s in segments if len(s.get("text", "").split()) > 3]
        if len(texts) > 2:
            vec = TfidfVectorizer(stop_words="english", max_features=20)
            X = vec.fit_transform(texts)
            # Sum TF-IDF scores across all segments
            scores = np.asarray(X.sum(axis=0)).flatten()
            words = vec.get_feature_names_out()
            
            indices = scores.argsort()[::-1]
            for i in indices[:12]:
                keywords.append({"text": words[i], "score": round(float(scores[i]), 3)})
    except Exception as exc:
        logger.error("Keyword extraction failed: %s", exc)

    return {
        "entities": entities[:20],
        "keywords": keywords
    }

def save_insights(job_id: str, insights: dict, insights_dir: Path) -> Path:
    insights_dir.mkdir(parents=True, exist_ok=True)
    out = insights_dir / f"{job_id}.json"
    out.write_text(json.dumps(insights, indent=2, ensure_ascii=False))
    return out

def load_insights(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Insights not found: {path}")
    return json.loads(path.read_text())
