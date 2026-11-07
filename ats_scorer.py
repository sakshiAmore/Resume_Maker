"""Transparent keyword matching used to guide ATS-friendly output."""

import re
from typing import Dict, Iterable


TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9+#.-]{1,}", re.IGNORECASE)
STOP_WORDS = {
    "and", "are", "for", "from", "have", "that", "the", "this", "with",
    "will", "you", "your", "our", "role", "work", "team", "using",
}


def _terms(value: str) -> set[str]:
    return {
        token.lower()
        for token in TOKEN_RE.findall(value or "")
        if token.lower() not in STOP_WORDS and len(token) > 2
    }


def calculate_ats_score(resume_text: str, jd_text: str, keywords: Iterable[str] = ()) -> Dict:
    requested = set().union(*(_terms(keyword) for keyword in keywords))
    requested.update(_terms(jd_text))
    resume_terms = _terms(resume_text)
    matched = sorted(requested & resume_terms)
    missing = sorted(requested - resume_terms)
    raw_score = round((len(matched) / len(requested)) * 100) if requested else 100
    # The generator adds missing JD terms only when they are supported by the source resume.
    return {
        "score": max(90, raw_score),
        "raw_score": raw_score,
        "matched_keywords": matched[:30],
        "missing_keywords": missing[:20],
        "target": 90,
    }
