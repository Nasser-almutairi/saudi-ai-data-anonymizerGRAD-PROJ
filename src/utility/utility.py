# -*- coding: utf-8 -*-
"""
PROTOTYPE DATA UTILITY SCORE (0-100, higher = more useful). Original dataset = 100.

  Utility = 20% A + 20% B + 25% C + 15% D + 20% E

  A  Columns preserved        share of columns that are NOT suppressed
  B  Values preserved         share of cells that are not "[REMOVED]"
  C  Numeric precision        for numeric analytical columns: 1 - (bin width / value range) when generalized
  D  Data-type preservation   numeric stays numeric = 1; numeric -> range text ("20–25") = 0.5; destroyed = 0
  E  Distribution preserved   numeric: mean & std (from bin mid-points) vs. original;
                              categorical: number of distinct categories kept

C, D and E are measured on NON-direct columns only (direct identifiers are not what analysts need).
This is a general indicator – it does not represent every possible analytical or AI use case.
"""
import re

import pandas as pd

from ..anonymization.methods import REMOVED, column_kind, to_number


def _midpoint(v):
    if pd.isna(v):
        return None
    s = str(v).replace(",", "")
    m = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*[–-]\s*(-?\d+(?:\.\d+)?)\s*$", s)
    if m:
        return (float(m.group(1)) + float(m.group(2))) / 2
    return to_number(s)


def _numeric_dist(orig: pd.Series, anon: pd.Series) -> float:
    o = pd.Series([to_number(x) for x in orig.dropna()]).dropna()
    a = pd.Series([_midpoint(x) for x in anon]).dropna()
    if o.empty or a.empty or o.std() == 0:
        return 0.0 if a.empty else 1.0
    d_mean = min(1.0, abs(a.mean() - o.mean()) / o.std())
    d_std = min(1.0, abs(a.std() - o.std()) / o.std()) if len(a) > 1 else 1.0
    return 1 - 0.5 * (d_mean + d_std)


def assess(orig: pd.DataFrame, anon: pd.DataFrame, config: pd.DataFrame, meta: dict) -> dict:
    n_cols = len(orig.columns)
    methods = dict(zip(config["Column"], config["Method"]))
    cats = dict(zip(config["Column"], config["Category"]))

    A = sum(methods[c] != "Suppression" for c in orig.columns) / n_cols
    B = (anon.astype(str) != REMOVED).to_numpy().mean() if anon.size else 1.0

    rows, C, D, E = [], [], [], []
    for c in orig.columns:
        m, direct = methods[c], cats[c] == "Direct"
        kind = column_kind(orig[c])
        if direct:
            rows.append({"Column": c, "Method": m, "Role": "Direct identifier (excluded from C/D/E)",
                         "Numeric precision": None, "Type kept": None, "Distribution kept": None})
            continue
        # --- C numeric precision
        if kind == "numeric":
            if m == "Keep":
                c_ = 1.0
            elif m == "Generalization":
                nums = [x for x in orig[c].map(to_number) if x is not None]
                rng = (max(nums) - min(nums)) or 1
                c_ = max(0.0, 1 - meta["gen_width"].get(c, rng) / rng)
            elif m == "Suppression":
                c_ = 0.0
            else:
                c_ = 0.2 if m != "Masking" else 0.3
            C.append(c_)
        else:
            c_ = None
        # --- D type preservation
        d_ = {"Keep": 1.0, "Suppression": 0.0}.get(m)
        if d_ is None:
            if kind == "numeric":
                d_ = 0.5 if m == "Generalization" else 0.0
            else:
                d_ = 1.0
        D.append(d_)
        # --- E distribution preservation
        if m == "Keep":
            e_ = 1.0
        elif m == "Suppression":
            e_ = 0.0
        elif kind == "numeric":
            e_ = _numeric_dist(orig[c], anon[c]) if m == "Generalization" else 0.0
        elif m == "Generalization":
            e_ = min(1.0, anon[c].nunique() / max(orig[c].nunique(), 1))
        elif m in ("Hashing", "Replacement"):
            e_ = 0.8                                    # distinct-value counts and frequencies are preserved
        else:
            e_ = 0.3
        E.append(e_)
        rows.append({"Column": c, "Method": m, "Role": "Analytical", "Numeric precision": None if c_ is None else round(c_, 2),
                     "Type kept": round(d_, 2), "Distribution kept": round(e_, 2)})

    mean = lambda xs: sum(xs) / len(xs) if xs else 1.0
    Cm, Dm, Em = mean(C), mean(D), mean(E)
    score = 100 * (0.20 * A + 0.20 * B + 0.25 * Cm + 0.15 * Dm + 0.20 * Em)
    comp = pd.DataFrame([
        {"Factor": "A  Columns preserved", "Weight": "20%", "Value": f"{A:.0%}"},
        {"Factor": "B  Values not suppressed", "Weight": "20%", "Value": f"{B:.0%}"},
        {"Factor": "C  Numeric precision kept", "Weight": "25%", "Value": f"{Cm:.0%}"},
        {"Factor": "D  Data types preserved", "Weight": "15%", "Value": f"{Dm:.0%}"},
        {"Factor": "E  Distributions preserved", "Weight": "20%", "Value": f"{Em:.0%}"},
    ])
    return {"before": 100, "after": round(score), "components": comp, "columns": pd.DataFrame(rows),
            "A": A, "B": B, "C": Cm, "D": Dm, "E": Em}
