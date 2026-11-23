"""Transparent TF-IDF term comparison for resume and role text."""

import math
import re
from collections import Counter

STOP_WORDS = frozenset(
    "a about above after again against all am an and any are as at be because been before being "
    "below between both but by can could did do does doing down during each few for from further "
    "had has have having he her here hers herself him himself his how i if in into is it its "
    "itself just me more most my myself no nor not of off on once only or other our ours ourselves "
    "out over own same she should so some such than that the their theirs them themselves then "
    "there these they this those through to too under until up very was we were what when where "
    "which while who whom why will with would you your yours yourself yourselves experience "
    "work working role team strong ability including using use used required preferred candidate "
    "skills skill knowledge years year responsibilities requirements company job position join "
    "across within able well plus etc".split()
)
TOKEN_RE = re.compile(r"[a-z][a-z0-9+#.-]{1,}", re.IGNORECASE)


def tokenize(text: str) -> Counter[str]:
    """Normalize words while preserving useful technical terms like C++ and CI/CD."""
    tokens = (token.casefold().strip(".-") for token in TOKEN_RE.findall(text))
    return Counter(token for token in tokens if token not in STOP_WORDS and len(token) > 1)


def compare_text(resume_text: str, job_description: str) -> dict[str, object]:
    """Return an explainable weighted overlap score and terms to review."""
    resume = tokenize(resume_text)
    job = tokenize(job_description)
    if not job:
        return {"score": 0, "matched_terms": [], "missing_terms": [], "resume_terms": [], "job_terms": []}

    # With two documents, IDF rewards terms specific to the role rather than shared boilerplate.
    max_job_count = max(job.values())
    document_frequency = {
        term: int(term in resume) + int(term in job)
        for term in job
    }
    weights = {
        term: (0.5 + 0.5 * count / max_job_count)
        * math.log(1 + 2 / (1 + document_frequency[term]))
        for term, count in job.items()
    }
    total_weight = sum(weights.values()) or 1
    matched = sorted((term for term in job if term in resume), key=lambda t: weights[t], reverse=True)
    missing = sorted((term for term in job if term not in resume), key=lambda t: weights[t], reverse=True)
    score = round(100 * sum(weights[t] for t in matched) / total_weight)
    return {
        "score": score,
        "matched_terms": matched[:10],
        "missing_terms": missing[:10],
        "resume_terms": [term for term, _ in resume.most_common(10)],
        "job_terms": [term for term, _ in job.most_common(10)],
    }
