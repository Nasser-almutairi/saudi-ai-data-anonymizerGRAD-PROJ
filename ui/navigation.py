# -*- coding: utf-8 -*-
"""Floating bottom navigation. It is a REAL st.radio (key='nav'), so Streamlit session state keeps working."""
import streamlit as st

NAV_ITEMS = [
    ("Upload Dataset", "Upload"),
    ("Dashboard", "Dashboard"),
    ("Sensitive Data Detection", "Detection"),
    ("Configure Anonymization", "Configure"),
    ("Results", "Results"),
    ("Privacy Report", "Privacy Report"),
]

PAGES = [p for p, _ in NAV_ITEMS]
_SHORT = dict(NAV_ITEMS)


def render_bottom_navigation():
    """Must be called AFTER app.py has applied any pending st.session_state['goto'] to st.session_state['nav']."""
    with st.container(key="bottom_nav"):
        st.radio(
            "Navigation",
            PAGES,
            key="nav",
            horizontal=True,
            label_visibility="collapsed",
            format_func=lambda p: _SHORT[p]
        )