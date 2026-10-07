# -*- coding: utf-8 -*-
"""
Saudi custom recognizers.

* Pattern matching uses Microsoft Presidio's `PatternRecognizer` (the foundation).
* The Saudi-specific VALIDATION logic (ID checksum, IBAN mod-97) and the CONTEXT logic are ours.
  We validate OUTSIDE Presidio on purpose: Presidio drops matches whose validation fails, but we want to
  keep them and simply give them lower confidence (explainability!).
* If Presidio is not installed, the same regexes run through Python's `re` module (graceful fallback).
"""
import random
import re
from dataclasses import dataclass
from typing import Callable, Optional

try:  # Presidio is the foundation, but the app still works without it.
    from presidio_analyzer import Pattern, PatternRecognizer
    PRESIDIO_AVAILABLE = True
except Exception:  # pragma: no cover
    PRESIDIO_AVAILABLE = False


# ------------------------------------------------------------------ validators
def saudi_id_valid(s: str) -> bool:
    """Saudi National ID (starts with 1) / Iqama (starts with 2): 10 digits + Luhn-style checksum."""
    s = re.sub(r"\D", "", s)
    if not re.fullmatch(r"[12]\d{9}", s):
        return False
    total = 0
    for i, ch in enumerate(s):
        d = int(ch)
        if i % 2 == 0:          # odd positions (1st, 3rd, ...) are doubled
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def make_saudi_id(rng: random.Random, first: str = "1") -> str:
    """Generate a FAKE but checksum-valid ID (used by the demo dataset and by format-preserving replacement)."""
    body = first + "".join(str(rng.randint(0, 9)) for _ in range(8))
    for c in range(10):
        if saudi_id_valid(body + str(c)):
            return body + str(c)


def iban_valid(s: str) -> bool:
    """Saudi IBAN = 'SA' + 2 check digits + 20 characters (24 total); ISO 13616 mod-97 check."""
    s = re.sub(r"\s", "", s).upper()
    if not re.fullmatch(r"SA\d{2}[0-9A-Z]{20}", s):
        return False
    rearranged = s[4:] + s[:4]
    return int("".join(str(int(c, 36)) for c in rearranged)) % 97 == 1


def make_iban(rng: random.Random, bank_code: str = "80") -> str:
    """FAKE but mod-97-valid Saudi IBAN."""
    bban = bank_code + "".join(str(rng.randint(0, 9)) for _ in range(18))
    check = 98 - int(bban + "281000") % 97          # 'SA' -> 2810, check digits placeholder 00
    return f"SA{check:02d}{bban}"


# ------------------------------------------------------------------ entity specifications
@dataclass
class EntitySpec:
    entity: str
    regex: str
    label: str                          # human-friendly name used in explanations
    pattern_weight: float               # confidence contributed by "value matches the pattern"
    validation_weight: float            # extra confidence if the checksum / validation passes
    validator: Optional[Callable] = None
    base_risk: str = "HIGH"


PATTERN_SPECS = {
    "SAUDI_NATIONAL_ID": EntitySpec(
        "SAUDI_NATIONAL_ID", r"(?<!\d)[12]\d{9}(?!\d)", "Saudi National ID / Iqama",
        0.45, 0.15, saudi_id_valid),
    "SAUDI_MOBILE": EntitySpec(
        "SAUDI_MOBILE", r"(?<![\d+])(?:\+?966|00966|0)?[\s-]?5\d[\s-]?\d{3}[\s-]?\d{4}(?!\d)", "Saudi mobile number",
        0.60, 0.0, None),
    "SAUDI_IBAN": EntitySpec(
        "SAUDI_IBAN", r"\bSA\d{2}\s?(?:[0-9A-Z]{4}\s?){4}[0-9A-Z]{4}\b", "Saudi IBAN",
        0.50, 0.15, iban_valid),
    "EMAIL_ADDRESS": EntitySpec(
        "EMAIL_ADDRESS", r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "Email address",
        0.85, 0.0, None),
}

# ------------------------------------------------------------------ Presidio recognizers
_RECOGNIZERS = {}


def _get_recognizer(entity: str):
    if entity not in _RECOGNIZERS:
        spec = PATTERN_SPECS[entity]
        if PRESIDIO_AVAILABLE:
            _RECOGNIZERS[entity] = PatternRecognizer(
                supported_entity=entity,
                patterns=[Pattern(name=entity.lower() + "_regex", regex=spec.regex, score=0.5)],
                supported_language="ar",
            )
        else:
            _RECOGNIZERS[entity] = re.compile(spec.regex, re.IGNORECASE)
    return _RECOGNIZERS[entity]


def find_spans(entity: str, text: str):
    """Return [(start, end), ...] of pattern matches for one entity. `text` must be digit-normalised."""
    rec = _get_recognizer(entity)
    if PRESIDIO_AVAILABLE:
        results = rec.analyze(text, [entity])
        return sorted({(r.start, r.end) for r in results})
    return [(m.start(), m.end()) for m in rec.finditer(text)]
