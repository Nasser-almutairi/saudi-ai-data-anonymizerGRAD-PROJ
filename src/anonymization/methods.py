# -*- coding: utf-8 -*-
"""
The five anonymization techniques (+ Keep). Each function works on ONE column.
Presidio's AnonymizerEngine is used for the in-text masking of detected spans (custom operators);
a plain-Python fallback keeps the app working if Presidio Anonymizer is unavailable.
"""
import hashlib
import math
import random
import re

import pandas as pd

from ..detection.lexicon import (CITY_TO_REGION, FAKE_AR_FAMILY, FAKE_AR_FIRST, FAKE_EN_FAMILY, FAKE_EN_FIRST,
                                 normalize_ar, normalize_digits)
from ..detection.saudi_recognizers import PATTERN_SPECS, find_spans, make_iban, make_saudi_id

REMOVED = "[REMOVED]"

try:
    from presidio_anonymizer import AnonymizerEngine
    from presidio_anonymizer.entities import OperatorConfig, RecognizerResult
    _ENGINE = AnonymizerEngine()
except Exception:  # pragma: no cover
    _ENGINE = None


# =================================================================== MASKING
MASK_RULES = {  # entity -> strength -> (keep_start, keep_end)  [counted on alphanumeric characters]
    "SAUDI_NATIONAL_ID": {"strong": (0, 2), "medium": (2, 2)},
    "SAUDI_MOBILE": {"strong": (2, 2), "medium": (3, 3)},
    "SAUDI_IBAN": {"strong": (2, 4), "medium": (4, 4)},
}


def mask_alnum(s: str, keep_start: int, keep_end: int) -> str:
    """Replace alphanumerics with '*' except the first/last few; separators (space, -, @, .) are kept."""
    idx = [i for i, ch in enumerate(s) if ch.isalnum()]
    n = len(idx)
    if n <= keep_start + keep_end + 1:
        keep_start, keep_end = min(keep_start, 1), 0
    out = list(s)
    for k, i in enumerate(idx):
        if keep_start <= k < n - keep_end:
            out[i] = "*"
    return "".join(out)


def mask_value(value: str, entity: str, strength: str) -> str:
    """Entity-aware masking. Example: 0551234567 -> 055****567."""
    v = str(value)
    t = normalize_digits(v)
    if entity == "SAUDI_MOBILE":
        digits = re.sub(r"\D", "", t)
        local = "0" + digits[-9:] if len(digits) >= 9 else digits       # canonical local form 05XXXXXXXX
        ks, ke = MASK_RULES[entity][strength]
        return mask_alnum(local, ks, ke)
    if entity == "SAUDI_NATIONAL_ID":
        ks, ke = MASK_RULES[entity][strength]
        return mask_alnum(re.sub(r"\D", "", t), ks, ke)
    if entity == "SAUDI_IBAN":
        ks, ke = MASK_RULES[entity][strength]
        return mask_alnum(re.sub(r"\s", "", t).upper(), ks, ke)
    if entity == "EMAIL_ADDRESS" and "@" in v:
        local, domain = v.split("@", 1)
        local_m = local[:1] + "***"
        if strength == "strong":
            tld = domain.rsplit(".", 1)[-1] if "." in domain else ""
            return f"{local_m}@***.{tld}" if tld else f"{local_m}@***"
        return f"{local_m}@{domain}"
    if entity in ("ARABIC_PERSON_NAME", "PERSON_NAME"):                 # first letter of every word
        return " ".join(w[:1] + "*" * (len(w) - 1) for w in v.split())
    return mask_alnum(v, 1, 1 if strength == "medium" else 0)


def _mask_spans(text: str, spans, strength: str) -> str:
    """spans = [(start, end, entity)], non-overlapping. Uses Presidio's AnonymizerEngine when available."""
    if not spans:
        return text
    if _ENGINE is not None:
        try:
            results = [RecognizerResult(entity_type=e, start=s, end=en, score=1.0) for s, en, e in spans]
            ops = {e: OperatorConfig("custom", {"lambda": (lambda x, _e=e: mask_value(x, _e, strength))})
                   for _, _, e in spans}
            return _ENGINE.anonymize(text=text, analyzer_results=results, operators=ops).text
        except Exception:
            pass
    out, last = [], 0
    for s, e, ent in sorted(spans):
        out += [text[last:s], mask_value(text[s:e], ent, strength)]
        last = e
    return "".join(out + [text[last:]])


def mask_text_inline(value: str, strength: str) -> str:
    """Find all Saudi pattern entities inside a free-text cell and mask just those parts."""
    t = normalize_digits(value)
    spans = []
    for ent in PATTERN_SPECS:
        spans += [(s, e, ent) for s, e in find_spans(ent, t)]
    spans.sort()
    clean, last_end = [], -1
    for s, e, ent in spans:                      # drop overlaps
        if s >= last_end:
            clean.append((s, e, ent))
            last_end = e
    return _mask_spans(value, clean, strength)


def apply_masking(series: pd.Series, entities, embedded: bool, strength: str) -> pd.Series:
    def f(v):
        if pd.isna(v) or str(v).strip() == "":
            return v
        if embedded:
            return mask_text_inline(str(v), strength)
        return mask_value(str(v), entities[0] if entities else "", strength)
    return series.map(f)


# =================================================================== SUPPRESSION
def apply_suppression(series: pd.Series) -> pd.Series:
    return series.map(lambda v: v if pd.isna(v) else REMOVED)


# =================================================================== HASHING
def apply_hashing(series: pd.Series, salt: str) -> pd.Series:
    """Salted SHA-256 (truncated). NOT advanced cryptography – just a one-way pseudonymous identifier."""
    return series.map(lambda v: v if pd.isna(v) else
                      "H_" + hashlib.sha256((salt + str(v)).encode("utf-8")).hexdigest()[:10])


# =================================================================== REPLACEMENT
PREFIX = {"ARABIC_PERSON_NAME": "Person", "PERSON_NAME": "Person", "SAUDI_NATIONAL_ID": "ID", "SAUDI_MOBILE": "Phone",
          "SAUDI_IBAN": "IBAN", "EMAIL_ADDRESS": "Email", "SAUDI_ADDRESS": "Address", "CUSTOMER_ID": "Customer"}


def _reformat_like(orig: str, compact: str) -> str:
    """Re-insert the spaces/dashes of `orig` into `compact` (so the fake looks like the original)."""
    out, k = [], 0
    for ch in orig:
        if ch.isalnum():
            out.append(compact[k] if k < len(compact) else "")
            k += 1
        else:
            out.append(ch)
    return "".join(out) + compact[k:]


def _fake(entity: str, orig: str, rng: random.Random, n: int) -> str:
    """FORMAT-PRESERVING fake value (Developer Testing profile)."""
    t = normalize_digits(orig)
    if entity == "SAUDI_NATIONAL_ID":
        return make_saudi_id(rng, t[:1] if t[:1] in "12" else "1")
    if entity == "SAUDI_MOBILE":
        digits = re.sub(r"\D", "", t)
        k = digits.find("5") + 1                                    # keep prefix up to and including the leading 5
        new = digits[:k] + "".join(str(rng.randint(0, 9)) for _ in range(len(digits) - k))
        return _reformat_like(t, new)
    if entity == "SAUDI_IBAN":
        compact = re.sub(r"\s", "", t).upper()
        return _reformat_like(t, make_iban(rng, compact[4:6] if len(compact) >= 6 else "80"))
    if entity == "EMAIL_ADDRESS":
        return f"user{n:03d}@example.com"
    if entity in ("ARABIC_PERSON_NAME", "PERSON_NAME"):
        ar = bool(re.search(r"[\u0600-\u06FF]", orig))
        first, fam = (FAKE_AR_FIRST, FAKE_AR_FAMILY) if ar else (FAKE_EN_FIRST, FAKE_EN_FAMILY)
        parts = [rng.choice(first)]
        for _ in range(max(0, len(orig.split()) - 2)):
            parts += ["بن" if ar else "bin", rng.choice(first)]
        return " ".join(parts + [rng.choice(fam)])
    return f"{PREFIX.get(entity, 'Value')}_{n:03d}"


def apply_replacement(series: pd.Series, entities, format_preserving: bool, salt: str) -> pd.Series:
    """Consistent pseudonyms: the same original value always maps to the same replacement inside the column."""
    entity = entities[0] if entities else ""
    mapping = {}
    prefix = PREFIX.get(entity, "Value")

    def f(v):
        if pd.isna(v) or str(v).strip() == "":
            return v
        key = str(v)
        if key not in mapping:
            n = len(mapping) + 1
            if format_preserving and entity in PREFIX:
                seed = int(hashlib.sha256((salt + key).encode()).hexdigest()[:12], 16)   # per-run salt => irreversible
                mapping[key] = _fake(entity, key, random.Random(seed), n)
            else:
                mapping[key] = f"{prefix}_{n:03d}"
        return mapping[key]
    return series.map(f)


# =================================================================== GENERALIZATION
_NICE = [1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000, 2500, 5000, 10000, 20000, 25000, 50000, 100000]


def to_number(v):
    try:
        return float(normalize_digits(str(v)).replace(",", "").strip())
    except ValueError:
        return None


def column_kind(series: pd.Series) -> str:
    """'numeric' | 'date' | 'text' (used by generalization and by the utility score)."""
    s = series.dropna().astype(str).str.strip()
    s = s[s != ""]
    if s.empty:
        return "text"
    if s.map(lambda v: to_number(v) is not None).mean() >= 0.9:
        return "numeric"
    if s.str.match(r"^\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}").mean() >= 0.9:
        return "date"
    return "text"


def choose_width(series: pd.Series, target_bins: int) -> float:
    nums = [x for x in series.map(to_number) if x is not None and not math.isnan(x)]
    rng = (max(nums) - min(nums)) or 1
    raw = rng / target_bins
    return min(_NICE, key=lambda w: abs(math.log(w / raw)))              # nearest "nice" width on a log scale


def _fmt(x):
    return f"{int(x):,}" if float(x).is_integer() else f"{x:,.1f}"


def generalize_numeric(series: pd.Series, width: float) -> pd.Series:
    """Age 23 -> '20–25'   Salary 8,700 -> '8,000–9,000'"""
    def f(v):
        x = to_number(v) if not pd.isna(v) else None
        if x is None:
            return v
        lo = math.floor(x / width) * width
        return f"{_fmt(lo)}–{_fmt(lo + width)}"
    return series.map(f)


def generalize_date(series: pd.Series, strong: bool) -> pd.Series:
    def f(v):
        m = re.search(r"(\d{4})", normalize_digits(str(v))) if not pd.isna(v) else None
        if not m:
            return v
        y = int(m.group(1))
        return f"{y // 10 * 10}s" if strong else str(y)
    return series.map(f)


def generalize_categorical(series: pd.Series, entity: str, min_group_frac: float) -> pd.Series:
    """City -> region (Saudi map). Anything else: rare categories are merged into 'Other'."""
    if entity == "CITY":
        regions = series.map(lambda v: v if pd.isna(v) else CITY_TO_REGION.get(normalize_ar(str(v))))
        if regions.notna().sum() >= 0.6 * series.notna().sum():
            return regions.where(regions.notna(), "Other")
    counts = series.value_counts()
    thr = max(2, math.ceil(min_group_frac * series.notna().sum()))
    keep = set(counts[counts >= thr].index)
    return series.map(lambda v: v if pd.isna(v) or v in keep else "Other")


def generalize_address(series: pd.Series) -> pd.Series:
    """Keep only the neighbourhood ('حي X') – remove street, building and postal details."""
    def f(v):
        if pd.isna(v):
            return v
        m = re.search(r"(حي\s+\S+(?:\s+\S+)?)(?=[،,])|(\S+(?:\s\S+)?\s+District)", str(v))
        return m.group(0).strip() if m else "[GENERALIZED ADDRESS]"
    return series.map(f)
