# -*- coding: utf-8 -*-
"""Applies the per-column configuration chosen by the user and returns the anonymized DataFrame."""
import secrets

import pandas as pd

from ..detection.detector import ENTITY_INFO, flagged
from . import methods as M
from .profiles import PROFILES, METHODS, recommend


def build_config(df: pd.DataFrame, detections, profile_key: str) -> pd.DataFrame:
    """One row per column: detected entity, category and the RECOMMENDED method (user can change it)."""
    rows = []
    fl = flagged(detections)
    for col in df.columns:
        ds = sorted([d for d in fl if d.column == col],
                    key=lambda d: (d.category != "Direct", ENTITY_INFO[d.entity][1] != "HIGH", -d.confidence))
        entities = [d.entity for d in ds]
        embedded = any(d.embedded for d in ds)
        rec = recommend(entities, embedded, profile_key)
        rows.append({
            "Column": col,
            "Detected": ", ".join(entities) if entities else "—",
            "Confidence": max((d.confidence for d in ds), default=None),
            "Category": ds[0].category if ds else "Non-sensitive",
            "Recommended": rec,
            "Method": rec,
        })
    return pd.DataFrame(rows)


def _col_info(col, detections):
    ds = [d for d in flagged(detections) if d.column == col]
    ds.sort(key=lambda d: (d.category != "Direct", -d.confidence))
    return [d.entity for d in ds], any(d.embedded for d in ds)


def anonymize(df: pd.DataFrame, config: pd.DataFrame, detections, profile_key: str):
    """Returns (anonymized_df, meta). `meta` keeps what the risk/utility modules need (bin widths, etc.)."""
    p = PROFILES[profile_key]
    salt = secrets.token_hex(8)                    # random per-run salt → hashes/fakes cannot be reproduced later
    out = df.copy()
    meta = {"gen_width": {}, "profile": profile_key, "entities": {}, "embedded": {}}
    for _, row in config.iterrows():
        col, method = row["Column"], row["Method"]
        entities, embedded = _col_info(col, detections)
        meta["entities"][col], meta["embedded"][col] = entities, embedded
        entity = entities[0] if entities else ""
        s = df[col]
        if method == "Keep":
            continue
        elif method == "Masking":
            out[col] = M.apply_masking(s, entities, embedded, p["strength"])
        elif method == "Suppression":
            out[col] = M.apply_suppression(s)
        elif method == "Hashing":
            out[col] = M.apply_hashing(s, salt)
        elif method == "Replacement":
            out[col] = M.apply_replacement(s, entities, p["format_preserving"], salt)
        elif method == "Generalization":
            kind = M.column_kind(s)
            if kind == "numeric":
                w = M.choose_width(s, p["target_bins"])
                meta["gen_width"][col] = w
                out[col] = M.generalize_numeric(s, w)
            elif kind == "date" or entity == "DATE_OF_BIRTH":
                out[col] = M.generalize_date(s, p["strength"] == "strong")
            elif entity == "SAUDI_ADDRESS":
                out[col] = M.generalize_address(s)
            else:
                out[col] = M.generalize_categorical(s, entity, p["min_group_frac"])
    return out, meta
