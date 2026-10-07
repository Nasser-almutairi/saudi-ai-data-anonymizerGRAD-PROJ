# -*- coding: utf-8 -*-
"""
PROTOTYPE RE-IDENTIFICATION RISK SCORE  (0-100, higher = more risk)

Transparent formula – NOT a formal legal or scientific risk certification:

  Risk = DIRECT part (max 55)  +  QUASI part (max 45)

  DIRECT part = 55 × weighted average "exposure" of the direct-identifier columns
      exposure: Keep 1.00 | Masking 0.10–0.80 (depends on how many characters stay visible) |
                Generalization 0.30 | Hashing 0.25 | Replacement 0.10 | Suppression 0.00
      weights : National ID 1.0, IBAN 1.0, Mobile 0.8, Email 0.8, Name 0.7, Address 0.6, Customer ID 0.5

  QUASI part  = 45 × average re-identification probability of the indirect identifiers.
      We assume an attacker who knows ANY 3 quasi-identifiers of a person (e.g. Age + City + Job).
      For every such combination, a record in an equivalence class of size k has probability 1/k of being
      re-identified (prosecutor model). Averaging over all records and all 3-column combinations gives the score.
      Generalization/suppression → bigger classes → lower probability.

Levels: LOW < 30 ≤ MEDIUM < 60 ≤ HIGH
"""
from itertools import combinations

import pandas as pd

from ..detection.saudi_recognizers import PATTERN_SPECS, find_spans
from ..detection.lexicon import normalize_digits

DIRECT_MAX, QUASI_MAX = 55, 45
ENTITY_WEIGHT = {"SAUDI_NATIONAL_ID": 1.0, "SAUDI_IBAN": 1.0, "SAUDI_MOBILE": 0.8, "EMAIL_ADDRESS": 0.8,
                 "ARABIC_PERSON_NAME": 0.7, "PERSON_NAME": 0.7, "SAUDI_ADDRESS": 0.6, "CUSTOMER_ID": 0.5}
METHOD_EXPOSURE = {"Keep": 1.0, "Hashing": 0.25, "Replacement": 0.10, "Suppression": 0.0, "Generalization": 0.30}


def level(score: float) -> str:
    return "LOW" if score < 30 else ("MEDIUM" if score < 60 else "HIGH")


def _visible_fraction(orig: pd.Series, anon: pd.Series) -> float:
    """Share of original characters still readable in place after masking."""
    fr = []
    for o, a in zip(orig.dropna().astype(str), anon.dropna().astype(str)):
        o2, a2 = normalize_digits(o), a
        if not o2:
            continue
        same = sum(1 for x, y in zip(o2, a2) if x == y)
        fr.append(min(1.0, same / len(o2)))
    return sum(fr) / len(fr) if fr else 0.0


def _residual_pii_ratio(orig: pd.Series, anon: pd.Series) -> float:
    """Free-text columns: how many of the original Saudi identifiers can STILL be detected in the output?"""
    def count(series):
        n = 0
        for v in series.dropna().astype(str):
            t = normalize_digits(v)
            n += sum(len(find_spans(e, t)) for e in PATTERN_SPECS)
        return n
    before = count(orig)
    return min(1.0, count(anon) / before) if before else 0.0


def _exposure(col, row, orig, anon, meta):
    m = row["Method"]
    if m == "Masking":
        if meta["embedded"].get(col):
            return 0.05 + 0.90 * _residual_pii_ratio(orig[col], anon[col])
        return 0.10 + 0.70 * _visible_fraction(orig[col], anon[col])
    return METHOD_EXPOSURE.get(m, 1.0)


def _quasi_risk(df: pd.DataFrame, cols):
    """Average prosecutor risk over all 3-column combinations; plus global k-anonymity statistics."""
    if not cols:
        return 0.0, None, None
    d = df[cols].fillna("∅").astype(str)
    combos = list(combinations(cols, min(3, len(cols))))
    risks = []
    for c in combos:
        size = d.groupby(list(c))[c[0]].transform("size")
        risks.append((1.0 / size).mean())
    full = d.groupby(cols)[cols[0]].transform("size")
    return sum(risks) / len(risks), int(full.min()), float((full == 1).mean())


def assess(orig: pd.DataFrame, anon: pd.DataFrame, config: pd.DataFrame, meta: dict) -> dict:
    """Compute before/after risk. `config` rows: Column, Category, Method (+ detected entities in meta)."""
    direct = config[config["Category"] == "Direct"]
    quasi = list(config.loc[config["Category"] == "Indirect", "Column"])

    wsum = dsum_after = 0.0
    rows = []
    for _, r in direct.iterrows():
        col = r["Column"]
        ent = (meta["entities"].get(col) or [""])[0]
        w = ENTITY_WEIGHT.get(ent, 0.6)
        e_after = _exposure(col, r, orig, anon, meta)
        wsum += w
        dsum_after += w * e_after
        rows.append({"Column": col, "Type": "Direct", "Method": r["Method"], "Exposure before": 1.0,
                     "Exposure after": round(e_after, 2)})
    direct_before = DIRECT_MAX if wsum else 0.0
    direct_after = DIRECT_MAX * dsum_after / wsum if wsum else 0.0

    qb, kb, ub = _quasi_risk(orig, quasi)
    qa, ka, ua = _quasi_risk(anon, quasi)
    quasi_before, quasi_after = QUASI_MAX * qb, QUASI_MAX * qa
    before, after = direct_before + quasi_before, direct_after + quasi_after

    remaining = [x for x in rows if x["Exposure after"] >= 0.5]
    reasons = []
    if wsum:
        reasons.append(f"Direct-identifier exposure fell from {direct_before:.0f} to {direct_after:.0f} "
                       f"(of {DIRECT_MAX}) after treating {len(rows)} direct-identifier column(s).")
    if quasi:
        reasons.append(f"Average re-identification probability from combinations of 3 quasi-identifiers "
                       f"({', '.join(quasi)}) fell from {qb:.2f} to {qa:.2f}; quasi part {quasi_before:.0f} → {quasi_after:.0f} "
                       f"(of {QUASI_MAX}).")
        reasons.append(f"Records that are unique on all quasi-identifiers together: {ub:.0%} → {ua:.0%}; "
                       f"smallest group size (k-anonymity): {kb} → {ka}.")
    else:
        reasons.append("No indirect identifiers were selected, so the quasi-identifier part is 0.")
    if remaining:
        reasons.append("Still highly exposed: " + ", ".join(x["Column"] for x in remaining) + ".")
    return {
        "before": round(before), "after": round(after), "level_before": level(before), "level_after": level(after),
        "direct_before": round(direct_before, 1), "direct_after": round(direct_after, 1),
        "quasi_before": round(quasi_before, 1), "quasi_after": round(quasi_after, 1),
        "avg_reid_before": round(qb, 3), "avg_reid_after": round(qa, 3),
        "k_before": kb, "k_after": ka, "unique_before": ub, "unique_after": ua,
        "quasi_columns": quasi, "direct_table": pd.DataFrame(rows), "remaining_direct": remaining, "reasons": reasons,
    }
