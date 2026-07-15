"""Finnish specific evaluation helpers for benchmark scenarios.

Uses spaCy (fi_core_news_sm) if installed, otherwise falls back to naive matching.
"""

from __future__ import annotations

from typing import Any

from tool_eval_bench.evals.helpers import as_str

try:
    import spacy

    # Attempt to load the Finnish model. If not downloaded, it will raise OSError.
    try:
        nlp = spacy.load("fi_core_news_sm")
    except OSError:
        nlp = None
except ImportError:
    nlp = None


def get_base_form(word: str) -> str:
    """Lemmatize a Finnish word to its base form."""
    if nlp is None:
        return word.strip().lower()

    # Process string using spaCy
    doc = nlp(word.strip())
    if doc:
        return doc[0].lemma_.lower()
    return word.strip().lower()


def includes_lemmatized(value: Any, expected: str) -> bool:
    """Check if the expected base form exists in the provided text.

    This handles Finnish inflections (e.g., 'Tampereella' -> 'tampere').
    """
    text = as_str(value)
    expected_base = get_base_form(expected)

    if nlp is None:
        # Fallback to naive substring matching if NLP model is unavailable
        return expected_base in text.lower()

    # Analyze the full text
    doc = nlp(text)
    lemmas = [token.lemma_.lower() for token in doc]
    return expected_base in lemmas


def contains_refusal_fi(answer: str) -> bool:
    """Check if the answer contains a Finnish refusal phrase."""
    low = answer.lower()
    phrases = [
        "en pysty",
        "en voi",
        "ei ole mahdollista",
        "minulla ei ole",
        "pahoitteluni",
        "pahoittelen",
        "anteeksi",
        "ei tueta",
        "rajojen ulkopuolella",
        "tietosuojasyistä",
        "en saa",
    ]
    return any(phrase in low for phrase in phrases)
