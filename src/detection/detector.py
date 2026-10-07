# -*- coding: utf-8 -*-
"""
Context-aware sensitive-data detection for a whole DataFrame.

Every detection is EXPLAINABLE: entity, column, confidence, risk level and a list of human-readable reasons.

Confidence = pattern evidence + checksum evidence + context evidence (column name / words next to the value),
capped at 0.99. A random 10-digit number therefore stays below the 0.5 reporting threshold, while the same number
in a column called "رقم الهوية" (or next to the phrase "رقم الهوية:" in free text) is reported with high confidence.
"""
import random
import re
from dataclasses import dataclass, field, asdict
from typing import List

import pandas as pd

from .lexicon import (ADDRESS_KEYWORDS, SAUDI_CITIES, column_hint, context_near, name_score, normalize_ar,
                      normalize_digits)
from .saudi_recognizers import PATTERN_SPECS, PRESIDIO_AVAILABLE, find_spans

THRESHOLD = 0.50          # minimum confidence to FLAG a column
HINT_WEIGHT = 0.35        # column-name evidence for pattern entities
CONTEXT_WEIGHT = 0.35     # evidence from words next to a value inside free text

ENGINE_PRESIDIO = "Presidio PatternRecognizer + Saudi validator + context"
ENGINE_CUSTOM = "Custom Saudi/Arabic rules (lexicon + column context)"

# category + base risk for non-pattern entities
ENTITY_INFO = {
    "SAUDI_NATIONAL_ID": ("Direct", "HIGH"), "SAUDI_MOBILE": ("Direct", "HIGH"), "SAUDI_IBAN": ("Direct", "HIGH"),
    "EMAIL_ADDRESS": ("Direct", "HIGH"), "ARABIC_PERSON_NAME": ("Direct", "HIGH"), "PERSON_NAME": ("Direct", "HIGH"),
    "SAUDI_ADDRESS": ("Direct", "HIGH"), "CUSTOMER_ID": ("Direct", "MEDIUM"),
    "AGE": ("Indirect", "MEDIUM"), "DATE_OF_BIRTH": ("Indirect", "HIGH"), "CITY": ("Indirect", "LOW"),
    "DISTRICT": ("Indirect", "MEDIUM"), "GENDER": ("Indirect", "LOW"), "JOB_TITLE": ("Indirect", "MEDIUM"),
    "SALARY": ("Indirect", "MEDIUM"), "NATIONALITY": ("Indirect", "MEDIUM"),
}
ENTITY_LABEL = {
    "SAUDI_NATIONAL_ID": "Saudi National ID / Iqama", "SAUDI_MOBILE": "Saudi Mobile Number", "SAUDI_IBAN": "Saudi IBAN",
    "EMAIL_ADDRESS": "Email Address", "ARABIC_PERSON_NAME": "Arabic Personal Name", "PERSON_NAME": "Personal Name",
    "SAUDI_ADDRESS": "Arabic / Saudi Address", "CUSTOMER_ID": "Customer / Account Identifier", "AGE": "Age",
    "DATE_OF_BIRTH": "Date of Birth", "CITY": "City", "DISTRICT": "District / Neighbourhood", "GENDER": "Gender",
    "JOB_TITLE": "Job Title", "SALARY": "Salary / Income", "NATIONALITY": "Nationality",
}


@dataclass
class Detection:
    column: str
    entity: str
    category: str                 # "Direct" | "Indirect"
    confidence: float             # 0..1
    risk: str                     # HIGH | MEDIUM | LOW
    reasons: List[str] = field(default_factory=list)
    engine: str = ENGINE_CUSTOM
    embedded: bool = False        # True when the entity sits inside free text rather than being the whole cell
    flagged: bool = True          # False = below threshold (kept as a "candidate" for explainability)
    samples: List[str] = field(default_factory=list)

    @property
    def label(self):
        return ENTITY_LABEL.get(self.entity, self.entity)

    def to_dict(self):
        d = asdict(self)
        d["label"] = self.label
        return d


def risk_level(base: str, conf: float) -> str:
    """Base entity risk, lowered one step when confidence is below 0.70."""
    levels = ["LOW", "MEDIUM", "HIGH"]
    i = levels.index(base)
    if conf < 0.70:
        i = max(0, i - 1)
    return levels[i]


def _make(col, entity, conf, reasons, engine, samples, embedded=False):
    conf = round(min(conf, 0.99), 2)
    cat, base = ENTITY_INFO[entity]
    return Detection(col, entity, cat, conf, risk_level(base, conf), reasons, engine, embedded,
                     conf >= THRESHOLD, samples)


def _pct(a, b):
    return f"{a}/{b} values ({round(100 * a / max(b, 1))}%)"


# ------------------------------------------------------------------ pattern-based entities (Presidio)
def _detect_pattern(col, values, spec):
    n = len(values)
    hits = valid = full = ctx_hits = 0
    ctx_kw = None
    samples = []
    for v in values:
        t = normalize_digits(v)
        spans = find_spans(spec.entity, t)
        if not spans:
            continue
        hits += 1
        s, e = spans[0]
        if len(samples) < 3:
            samples.append(v[:60])
        if spec.validator is None or any(spec.validator(t[a:b]) for a, b in spans):
            valid += 1
        if (e - s) >= 0.8 * len(t.strip()):
            full += 1
        kw = context_near(t, s, e, spec.entity)
        if kw:
            ctx_hits += 1
            ctx_kw = ctx_kw or kw
    hint = column_hint(col, spec.entity)
    if hits == 0 and not hint:
        return None

    reasons, conf = [], 0.0
    embedded = hits > 0 and (full / hits) < 0.5
    if hits == 0:
        conf = 0.30
        reasons.append(f"Column name contains '{hint}' but no value matches the {spec.label} pattern")
    else:
        # For free-text columns a single hit is weak, three or more hits are full evidence.
        rate = min(1.0, hits / 3) if embedded else hits / n
        vrate = (valid / hits) if embedded else valid / n
        conf += spec.pattern_weight * rate
        where = "inside free text" if embedded else "in the whole cell"
        reasons.append(f"Matches {spec.label} pattern {where} in {_pct(hits, n)}")
        if spec.validator is not None:
            conf += spec.validation_weight * vrate
            if valid:
                reasons.append(f"Passes the {spec.label} checksum in {_pct(valid, hits)}")
            else:
                reasons.append(f"Pattern matches but the checksum FAILS ({spec.label}) → probably not a real identifier")
        if not embedded and full / max(hits, 1) >= 0.8:
            conf += 0.02
        if hint:
            conf += HINT_WEIGHT
            reasons.append(f"Column name contains '{hint}'")
        if ctx_hits:
            conf += CONTEXT_WEIGHT * (ctx_hits / hits)
            reasons.append(f"Context phrase '{ctx_kw}' found next to the value in {_pct(ctx_hits, hits)}")
        if not hint and not ctx_hits:
            reasons.append("No supporting context (column name / nearby words) → confidence stays limited")
    return _make(col, spec.entity, conf, reasons, ENGINE_PRESIDIO if PRESIDIO_AVAILABLE else ENGINE_CUSTOM,
                 samples, embedded)


# ------------------------------------------------------------------ names, addresses, ids (custom rules)
def _detect_name(col, values):
    n = len(values)
    shape = lex = arabic = 0
    samples = []
    for v in values:
        ok, hit, is_ar = name_score(v)
        if ok:
            shape += 1
            lex += hit
            arabic += is_ar
            if len(samples) < 3:
                samples.append(v)
    hint = column_hint(col, "PERSON_NAME")
    if shape == 0 and not hint:
        return None
    reasons, conf = [], 0.0
    if shape:
        conf += 0.35 * shape / n
        reasons.append(f"{_pct(shape, n)} look like personal names (2–5 alphabetic words)")
    if lex:
        conf += 0.15 * lex / n
        reasons.append(f"Saudi/Arabic name lexicon or particle (بن / آل / bin / Al) found in {_pct(lex, n)}")
    if hint:
        conf += 0.40
        reasons.append(f"Column name contains '{hint}'")
    elif conf < THRESHOLD:
        reasons.append("No 'name' column context → treated as a weak candidate")
    entity = "ARABIC_PERSON_NAME" if shape and arabic / shape >= 0.5 else "PERSON_NAME"
    if entity == "PERSON_NAME" and not shape:
        entity = "ARABIC_PERSON_NAME" if re.search(r"[\u0600-\u06FF]", col) else "PERSON_NAME"
    return _make(col, entity, conf, reasons, ENGINE_CUSTOM, samples)


def _detect_address(col, values):
    n = len(values)
    hint = column_hint(col, "SAUDI_ADDRESS")
    if column_hint(col, "DISTRICT") and not hint:
        return None                                   # a district column is an indirect identifier, not an address
    kw_hits, found, samples = 0, set(), []
    for v in values:
        low = normalize_ar(v)
        ks = [k for k in ADDRESS_KEYWORDS if re.search(r"(?<!\w)" + re.escape(normalize_ar(k)), low)]
        if ks and len(v) >= 10:
            kw_hits += 1
            found.update(ks[:2])
            if len(samples) < 3:
                samples.append(v)
    if kw_hits == 0 and not hint:
        return None
    reasons, conf = [], 0.0
    if kw_hits:
        conf += 0.5 * kw_hits / n
        reasons.append(f"Address keywords ({', '.join(sorted(found)[:4])}) found in {_pct(kw_hits, n)}")
    if hint:
        conf += 0.40
        reasons.append(f"Column name contains '{hint}'")
    return _make(col, "SAUDI_ADDRESS", conf, reasons, ENGINE_CUSTOM, samples)


def _detect_customer_id(col, values):
    hint = column_hint(col, "CUSTOMER_ID")
    if not hint:
        return None
    uniq = len(set(values)) / len(values)
    reasons = [f"Column name contains '{hint}'", f"{round(100 * uniq)}% of values are unique (behaves like an identifier)"]
    return _make(col, "CUSTOMER_ID", 0.65 + 0.25 * uniq, reasons, ENGINE_CUSTOM, values[:3])


# ------------------------------------------------------------------ indirect identifiers (quasi-identifiers)
def _num_ratio(values, lo=None, hi=None):
    ok = 0
    for v in values:
        try:
            x = float(normalize_digits(v).replace(",", ""))
            ok += (lo is None or lo <= x <= hi)
        except ValueError:
            pass
    return ok / len(values)


def _detect_quasi(col, values):
    out = []
    n = len(values)
    uniq = len(set(values))

    def add(entity, hint, check_rate, check_text):
        conf = 0.0
        reasons = []
        if hint:
            conf += 0.70
            reasons.append(f"Column name contains '{hint}'")
        if check_rate is not None:
            conf += 0.25 * check_rate if hint else 0.60 * check_rate
            if check_rate > 0:
                reasons.append(check_text(check_rate))
        if conf > 0:
            reasons.append("Indirect identifier: risky when COMBINED with other fields (suggested – please confirm)")
            out.append(_make(col, entity, conf, reasons, ENGINE_CUSTOM, values[:3]))

    h = column_hint(col, "AGE")
    if h:
        add("AGE", h, _num_ratio(values, 0, 120), lambda r: f"{round(100 * r)}% of values are plausible ages (0–120)")
    h = column_hint(col, "SALARY")
    if h:
        add("SALARY", h, _num_ratio(values), lambda r: f"{round(100 * r)}% of values are numeric amounts")
    h = column_hint(col, "DATE_OF_BIRTH")
    if h:
        dr = sum(bool(re.match(r"^\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}", normalize_digits(v))) for v in values) / n
        add("DATE_OF_BIRTH", h, dr, lambda r: f"{round(100 * r)}% of values look like dates")
    h = column_hint(col, "CITY")
    cr = sum(normalize_ar(v) in SAUDI_CITIES for v in values) / n
    if h or cr >= 0.8:
        add("CITY", h, cr, lambda r: f"{round(100 * r)}% of values are known Saudi cities")
    h = column_hint(col, "DISTRICT")
    if h:
        add("DISTRICT", h, None, None)
    h = column_hint(col, "GENDER")
    if h:
        add("GENDER", h, 1.0 if uniq <= 4 else 0.0, lambda r: f"Only {uniq} distinct values (typical for gender)")
    h = column_hint(col, "JOB_TITLE")
    if h:
        add("JOB_TITLE", h, None, None)
    h = column_hint(col, "NATIONALITY")
    if h:
        add("NATIONALITY", h, None, None)
    return out


# ------------------------------------------------------------------ public API
def detect_dataframe(df: pd.DataFrame, max_sample: int = 300) -> List[Detection]:
    """Scan every column. Returns ALL candidate detections (flagged ones have confidence >= THRESHOLD)."""
    detections: List[Detection] = []
    for col in df.columns:
        s = df[col].dropna().astype(str).str.strip()
        s = s[s != ""]
        if s.empty:
            continue
        values = s.tolist() if len(s) <= max_sample else s.sample(max_sample, random_state=0).tolist()

        # 1) Presidio-based, regex entities (several can co-exist inside one free-text column)
        for spec in PATTERN_SPECS.values():
            d = _detect_pattern(col, values, spec)
            if d:
                detections.append(d)
        # 2) one "primary" non-pattern entity per column (best confidence wins)
        extra = [x for x in (_detect_name(col, values), _detect_address(col, values),
                             _detect_customer_id(col, values)) if x] + _detect_quasi(col, values)
        if extra:
            detections.append(max(extra, key=lambda d: (d.confidence, d.category == "Direct")))
    return detections


def flagged(detections):
    return [d for d in detections if d.flagged]


def candidates(detections):
    return [d for d in detections if not d.flagged and d.confidence >= 0.30]


def summarize(df, detections):
    f = flagged(detections)
    cols = {d.column for d in f}
    return {
        "records": len(df), "columns": df.shape[1],
        "sensitive_fields": len(cols),
        "direct": len({d.column for d in f if d.category == "Direct"}),
        "indirect": len({d.column for d in f if d.category == "Indirect"}),
        "high_risk": len({d.column for d in f if d.risk == "HIGH"}),
    }


def analyze_text(text: str):
    """Live 'try it yourself' detector for a single piece of free text (used on the detection page)."""
    t = normalize_digits(text)
    rows = []
    for spec in PATTERN_SPECS.values():
        for s, e in find_spans(spec.entity, t):
            frag = t[s:e]
            conf = spec.pattern_weight
            reasons = [f"Matches {spec.label} pattern"]
            if spec.validator:
                if spec.validator(frag):
                    conf += spec.validation_weight
                    reasons.append("Passes checksum")
                else:
                    reasons.append("Checksum FAILS")
            kw = context_near(t, s, e, spec.entity)
            if kw:
                conf += CONTEXT_WEIGHT
                reasons.append(f"Context phrase '{kw}' next to the value")
            else:
                reasons.append("No context phrase nearby")
            conf = round(min(conf + 0.02, 0.99), 2)
            cat, base = ENTITY_INFO[spec.entity]
            rows.append({"Text": text[s:e], "Entity": spec.entity, "Confidence": conf,
                         "Risk": risk_level(base, conf) if conf >= THRESHOLD else "— (not flagged)",
                         "Reason": " + ".join(reasons)})
    return rows
