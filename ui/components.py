# -*- coding: utf-8 -*-
"""Reusable UI components. They only render HTML/containers – no backend logic lives here."""
import html

import streamlit as st

_TONE_BY_LEVEL = {"HIGH": "bad", "MEDIUM": "warn", "LOW": "good"}


def _e(x):
    return html.escape(str(x))


def render_page_header(eyebrow: str, title: str, description: str = ""):
    st.markdown(
        f"<div class='ph'><div class='ph-eyebrow'>{_e(eyebrow)}</div><div class='ph-title'>{_e(title)}</div>"
        f"<p class='ph-desc'>{_e(description)}</p></div>", unsafe_allow_html=True)


def status_chips(dataset_name=None, rows=None, cols=None, presidio=True):
    ds = (f"<span class='chip'><span class='dot on'></span>Dataset <b>{_e(dataset_name)}</b> · {rows:,} × {cols}</span>"
          if dataset_name else "<span class='chip'><span class='dot'></span>No dataset loaded</span>")
    pr = f"<span class='chip'><span class='dot {'on' if presidio else ''}'></span>Presidio <b>{'active' if presidio else 'fallback'}</b></span>"
    st.markdown(f"<div class='chips'>{ds}{pr}<span class='chip'>Fake demo data · prototype scores</span></div>", unsafe_allow_html=True)


def metric_card(label, value, delta=None, tone="neutral", index=0, raw=False):
    """tone: neutral | good | bad | warn | accent. `raw=True` lets `value` be trusted HTML."""
    v = value if raw else _e(value)
    d = f"<div class='md {tone if tone in ('good', 'bad', 'warn') else ''}'>{_e(delta)}</div>" if delta else ""
    st.markdown(
        f"<div class='mcard {tone}' style='--i:{index}'>"
        f"<div class='ml'>{_e(label)}</div>"
        f"<div class='mv'>{v}</div>{d}</div>",
        unsafe_allow_html=True
    )


def risk_badge(level: str, large=False) -> str:
    """Returns HTML for LOW / MEDIUM / HIGH badges."""
    lv = str(level).upper()
    return f"<span class='badge badge-{lv.lower()} {'lg' if large else ''}'><i></i>{_e(lv)}</span>"


def pill(text, tone="neutral") -> str:
    return f"<span class='pill {tone}'>{_e(text)}</span>"


def section_title(title, sub=None):
    s = f"<div class='ss'>{_e(sub)}</div>" if sub else ""
    st.markdown(
        f"<div class='sec'><div class='st'>{_e(title)}</div>{s}</div>",
        unsafe_allow_html=True
    )


def verdict_banner(html_text, tone="good"):
    """html_text may contain <b> tags. tone: good | warn | bad"""
    st.markdown(
        f"<div class='verdict {'' if tone == 'good' else tone}'>{html_text}</div>",
        unsafe_allow_html=True
    )


def score_ring(value, label, tone, caption="", badge_html=""):
    """Animated circular score (value 0-100)."""
    st.markdown(
        f"<div class='ringwrap'>"
        f"<div class='ring {tone}' style='--p:{max(0, min(100, int(value)))}'>"
        f"<span>{int(value)}</span></div>"
        f"<div class='ringtxt'><div class='rl'>{_e(label)}</div>"
        f"{badge_html}<div class='rs'>{_e(caption)}</div></div></div>",
        unsafe_allow_html=True
    )


def stepper(steps):
    st.markdown(
        "<div class='steps'>" +
        "".join(
            f"<div class='step'><b>STEP {i + 1}</b>{_e(s)}</div>"
            for i, s in enumerate(steps)
        ) +
        "</div>",
        unsafe_allow_html=True
    )


def card(key: str):
    """Styled bordered container."""
    return st.container(border=True, key=f"card_{key}")


def animated_container(epoch: int, direction: int = 1):
    """Restarts the entrance animation whenever the page changes."""
    return st.container(
        key=f"page_{epoch % 2}_{'fwd' if direction >= 0 else 'back'}"
    )