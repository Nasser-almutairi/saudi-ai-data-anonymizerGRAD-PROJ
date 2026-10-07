# -*- coding: utf-8 -*-
"""
Saudi AI-Assisted Data Anonymization System  –  Streamlit MVP
Run:  streamlit run app.py
"""
import io
import os

import altair as alt
import pandas as pd
import streamlit as st

from src.anonymization.pipeline import anonymize, build_config
from src.anonymization.profiles import METHODS, PROFILES, WHY
from src.detection.detector import (THRESHOLD, analyze_text, candidates, detect_dataframe, flagged, summarize)
from src.detection.saudi_recognizers import PRESIDIO_AVAILABLE
from src.reporting.report import DISCLAIMER, build_html, build_markdown, recommendations
from src.risk.risk import assess as assess_risk
from src.utility.utility import assess as assess_utility
from src.storage.state import save_state, load_state, clear_state
from ui.components import (animated_container, card, metric_card, pill, render_page_header, risk_badge, score_ring,
                           section_title, status_chips, stepper, verdict_banner)
from ui.navigation import PAGES, render_bottom_navigation
from ui.styles import inject_global_css

st.set_page_config(page_title="Saudi AI-Assisted Data Anonymization", page_icon="🛡️", layout="wide",
                   initial_sidebar_state="collapsed")
inject_global_css()

DEMO_PATH = os.path.join(os.path.dirname(__file__), "data", "sample_saudi_dataset.csv")
RISK_ICON = {"HIGH": "🔴 HIGH", "MEDIUM": "🟠 MEDIUM", "LOW": "🟢 LOW"}
GREEN, RED, AMBER = "#34D399", "#F87171", "#38BDF8"
MAX_ROWS = 20000
EYEBROW = {"Dashboard": "DATA PRIVACY WORKSPACE", "Upload Dataset": "STEP 1 · DATA INTAKE",
           "Sensitive Data Detection": "STEP 2 · DETECTION", "Configure Anonymization": "STEP 3 · CONFIGURATION",
           "Results": "STEP 4 · RESULTS", "Privacy Report": "STEP 5 · FINAL REPORT"}


# ------------------------------------------------------------------ helpers
def hero(title, sub):
    """Kept with the same name/signature so every page function stays unchanged."""
    render_page_header(EYEBROW.get(st.session_state.nav, "DATA PRIVACY WORKSPACE"), title, sub)
    df = st.session_state.get("df")
    status_chips(st.session_state.get("name") if df is not None else None,
                 len(df) if df is not None else None, df.shape[1] if df is not None else None, PRESIDIO_AVAILABLE)


def need_data():
    if "df" not in st.session_state:
        st.warning("No dataset loaded yet. Load the Saudi demo dataset or upload a CSV / Excel file.")
        c1, c2 = st.columns(2)
        if c1.button("📦 Load Saudi demo dataset", type="primary", key=f"demo_{st.session_state.nav}"):
            load_demo()
            st.rerun()
        if c2.button("Go to Upload page", key=f"up_{st.session_state.nav}"):
            goto("Upload Dataset")
        return False
    return True


def goto(page):
    st.session_state["goto"] = page
    st.rerun()


def next_button(label, page):
    st.divider()
    if st.button(label, type="primary", key=f"next_{page}"):
        goto(page)


def reset_analysis():
    for k in ("config", "config_profile", "result", "report_md"):
        st.session_state.pop(k, None)


def set_dataset(df, name):
    df = df.copy()
    if len(df) > MAX_ROWS:
        st.warning(f"Dataset truncated to the first {MAX_ROWS:,} rows for this prototype.")
        df = df.head(MAX_ROWS)
    st.session_state.df, st.session_state.name = df, name
    st.session_state.detections = detect_dataframe(df)
    reset_analysis()
    save_state(st.session_state)


def load_demo():
    set_dataset(pd.read_csv(DEMO_PATH, dtype=str, encoding="utf-8-sig"), "sample_saudi_dataset.csv (demo)")


def read_upload(file, sheet=None):
    """Everything is read as TEXT so leading zeros (05xxxxxxxx) and long IDs are never altered."""
    if file.name.lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(file, dtype=str, sheet_name=sheet or 0)
    raw = file.getvalue()
    for enc in ("utf-8-sig", "utf-8", "cp1256", "latin-1"):          # cp1256 = Arabic Windows CSVs
        try:
            return pd.read_csv(io.BytesIO(raw), dtype=str, encoding=enc)
        except UnicodeDecodeError:
            continue
    raise ValueError("Could not decode the CSV file.")


def csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8-sig")            # BOM so Excel shows Arabic correctly


def xlsx_bytes(df):
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    return buf.getvalue()


def before_after_chart(title, before, after, lower_is_better):
    good, bad = GREEN, RED
    colors = [bad if lower_is_better else GREEN, good if lower_is_better else AMBER]
    d = pd.DataFrame({"Stage": ["Before", "After"], "Score": [before, after]})
    base = alt.Chart(d, title=title).encode(
        x=alt.X("Stage:N", sort=["Before", "After"], axis=alt.Axis(labelAngle=0, title=None)))
    bars = base.mark_bar(size=70, cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
        y=alt.Y("Score:Q", scale=alt.Scale(domain=[0, 100]), title="Score (0–100)"),
        color=alt.Color("Stage:N", scale=alt.Scale(domain=["Before", "After"], range=colors), legend=None))
    text = base.mark_text(dy=-8, fontSize=16, fontWeight="bold", color="#E8EEF5").encode(y="Score:Q", text="Score:Q")
    return (bars + text).properties(height=240, background="transparent")
if "_saved_state_loaded" not in st.session_state:
            load_state(st.session_state)
            st.session_state["_saved_state_loaded"] = True

# ------------------------------------------------------------------ navigation
if "nav" not in st.session_state:
    st.session_state.nav = "Dashboard"
if "goto" in st.session_state:                                   # set BEFORE the radio widget is created
    st.session_state.nav = st.session_state.pop("goto")

render_bottom_navigation()                                       # floating pill (real st.radio, key="nav")
page = st.session_state.nav

# page-change bookkeeping -> drives the entrance animation (epoch) and its direction (forward/back)
if st.session_state.get("_prev_page") != page:
    prev = st.session_state.get("_prev_page")
    st.session_state["_direction"] = 1 if prev is None or PAGES.index(page) >= PAGES.index(prev) else -1
    st.session_state["_epoch"] = st.session_state.get("_epoch", 0) + 1
    st.session_state["_prev_page"] = page


# ================================================================== PAGE 1 – DASHBOARD
def page_dashboard():
    hero("Dashboard", "Monitor dataset privacy, anonymization status and re-identification risk.")
    if "df" in st.session_state:
        s = summarize(st.session_state.df, st.session_state.detections)
        specs = [("Total records", "records", "neutral"), ("Total columns", "columns", "neutral"),
                 ("Sensitive fields", "sensitive_fields", "accent"), ("Direct identifiers", "direct", "warn"),
                 ("Indirect identifiers", "indirect", "accent"), ("High-risk fields", "high_risk", "bad")]
        for i, (col, (lab, key, tone)) in enumerate(zip(st.columns(6), specs)):
            with col:
                metric_card(lab, f"{s[key]:,}", tone=tone, index=i)
        fl = flagged(st.session_state.detections)
        if fl:
            section_title("Detected sensitive data", "Number of columns per entity type, coloured by risk level")
            left, right = st.columns([3, 2])
            with left, card("chart"):
                d = pd.DataFrame([{"Entity": x.label, "Risk": x.risk, "Columns": 1} for x in fl])
                d = d.groupby(["Entity", "Risk"], as_index=False).sum()
                ch = alt.Chart(d).mark_bar(cornerRadiusEnd=5).encode(
                    y=alt.Y("Entity:N", sort="-x", title=None, axis=alt.Axis(labelLimit=260)),
                    x=alt.X("Columns:Q", title="Number of columns", axis=alt.Axis(tickMinStep=1)),
                    color=alt.Color("Risk:N", scale=alt.Scale(domain=["HIGH", "MEDIUM", "LOW"], range=["#F87171", "#FBBF24", "#34D399"])),
                    tooltip=["Entity", "Risk", "Columns"]).properties(height=330, background="transparent")
                st.altair_chart(ch, use_container_width=True)
            with right, card("status"):
                st.markdown("**Workspace status**")
                st.markdown(f"Dataset &nbsp; `{st.session_state.name}`")
                st.markdown("Detection &nbsp; ✅ done")
                st.markdown("Anonymization &nbsp; " + ("✅ done" if "result" in st.session_state else "⏳ not run yet"))
                if "result" in st.session_state:
                    r, u = st.session_state.result["risk"], st.session_state.result["utility"]
                    st.markdown(f"Risk &nbsp; **{r['before']} → {r['after']}** &nbsp; " + risk_badge(r["level_after"]), unsafe_allow_html=True)
                    st.markdown(f"Utility &nbsp; **100 → {u['after']}**")
    else:
        with card("start"):
            st.markdown("**Start the 3–5 minute demo** by loading the built-in Saudi dataset (fake data only).")
            if st.button("📦 Load Saudi demo dataset", type="primary"):
                load_demo()
                goto("Sensitive Data Detection")

    section_title("What makes this project different")
    a, b = st.columns(2)
    with a, card("foundation"):
        st.markdown("#### 🧱 Foundation: Microsoft Presidio")
        st.markdown("General-purpose privacy toolkit:\n- Pattern **recognizers** (regex-based detection)\n"
                    "- **Anonymizer** engine with operators (mask, replace, hash …)\n"
                    "- Built for English / Western data formats")
    with b, card("contribution"):
        st.markdown("#### 🇸🇦 Our contribution")
        st.markdown("1. **Saudi-specific PII detection** (ID/Iqama with checksum, mobile, IBAN with mod-97)\n"
                    "2. **Arabic contextual detection** (“رقم الهوية”, “الجوال”, Arabic digits)\n"
                    "3. **Custom Saudi recognizers** built on Presidio\n"
                    "4. **Direct vs. indirect** identifier classification\n"
                    "5. **Purpose-based profiles** (AI / Developer / Internal)\n"
                    "6. **Prototype re-identification risk** score\n"
                    "7. **Data Utility** score → privacy–utility trade-off\n"
                    "8. **Saudi Privacy Assessment Report**")
    st.caption("We do not claim each idea is new – the contribution is integrating and adapting them into a Saudi / Arabic-focused workflow.")
    section_title("Workflow")
    stepper(["Upload", "Detect", "Configure", "Anonymize", "Compare", "Report"])
    st.divider()

if st.button("🗑️ Reset saved session", key="reset_saved_session"):
    clear_state()

    for key in list(st.session_state.keys()):
        del st.session_state[key]

    st.rerun()
   # with st.expander("📘 Key terms"):
      #  st.markdown(
           # "- **PII** – information that can identify a person.\n- **Anonymization** – irreversibly reducing the ability to identify a real individual.\n"
           # "- **Direct identifier** – identifies a person on its own (name, ID, phone, e-mail, IBAN).\n"
          #  "- **Indirect identifier / quasi-identifier** – identifies someone only when combined (age, city, job, salary).\n"
         #   "- **Re-identification risk** – estimated chance of identifying someone again after anonymization.\n"
          #  "- **Data utility** – how useful the data stays for analytics / AI.\n"
          #  "- **Privacy–utility trade-off** – more protection usually means less detail.")


# ================================================================== PAGE 2 – UPLOAD
def page_upload():
    hero("Upload Dataset", "CSV or Excel (.xlsx). Arabic (UTF-8) values are supported. Prototype limit: a few thousand rows.")
    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown("<div class='upl-h'><div class='t'>Drag & drop your dataset</div>"
                    "<div class='s'>Supported files: <b>CSV</b> · <b>XLSX</b> · <b>XLS</b> — Arabic text and leading zeros are preserved</div></div>",
                    unsafe_allow_html=True)
        up = st.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx", "xls"], label_visibility="collapsed")
        if up is not None and st.session_state.get("uploaded_id") != (up.name, up.size):
            sheet = None
            if up.name.lower().endswith((".xlsx", ".xls")):
                names = pd.ExcelFile(up).sheet_names
                sheet = st.selectbox("Sheet", names) if len(names) > 1 else names[0]
            try:
                set_dataset(read_upload(up, sheet), up.name)
                st.session_state.uploaded_id = (up.name, up.size)
                st.rerun()
            except Exception as e:
                st.error(f"Could not read the file: {e}")
    with c2, card("demo"):
        st.markdown("**No file? Use the built-in dataset**")
        st.caption("48 fake Saudi-style customer records with Arabic names, IDs, mobiles, IBANs, notes …")
        if st.button("📦 Load Saudi demo dataset", type="primary"):
            load_demo()
            st.session_state.pop("uploaded_id", None)
            st.rerun()
    if "df" in st.session_state:
        df = st.session_state.df
        st.success(f"Loaded **{st.session_state.name}** – {len(df):,} records, {df.shape[1]} columns.")
        section_title("Dataset preview")
        st.dataframe(df.head(25), use_container_width=True, hide_index=True)
        next_button("Next → Detect sensitive data", "Sensitive Data Detection")


# ================================================================== PAGE 3 – DETECTION
def page_detection():
    hero("Sensitive Data Detection", "Presidio recognizers + Saudi validators + Arabic context → every finding comes with a reason.")
    if not need_data():
        return
    df, dets = st.session_state.df, st.session_state.detections
    s = summarize(df, dets)
    for i, (col, (lab, key, tone)) in enumerate(zip(st.columns(4), [
            ("Sensitive fields", "sensitive_fields", "accent"), ("Direct identifiers", "direct", "warn"),
            ("Indirect (suggested)", "indirect", "accent"), ("High-risk fields", "high_risk", "bad")])):
        with col:
            metric_card(lab, s[key], tone=tone, index=i)

    def table(items):
        return pd.DataFrame([{
            "Column": d.column, "Entity": d.label, "Confidence": d.confidence, "Risk": RISK_ICON[d.risk],
            "Found": "inside free text" if d.embedded else "whole value",
            "Why (explanation)": "  •  ".join(d.reasons), "Engine": d.engine} for d in items])

    cfg = {"Confidence": st.column_config.ProgressColumn("Confidence", min_value=0, max_value=1, format="percent"),
           "Why (explanation)": st.column_config.TextColumn(width="large")}
    section_title("Findings")
    t1, t2, t3, t4 = st.tabs(["🔴 Direct identifiers", "🟡 Indirect identifiers (suggested)", "⚪ Below threshold", "🧪 Try the detector"])
    fl = flagged(dets)
    with t1:
        d = [x for x in fl if x.category == "Direct"]
        st.caption("Data that can identify a person on its own.")
        st.dataframe(table(d), use_container_width=True, hide_index=True, column_config=cfg)
    with t2:
        d = [x for x in fl if x.category == "Indirect"]
        st.caption("Suggested from column names / values. They identify people only when combined – you confirm them on the next page.")
        st.dataframe(table(d), use_container_width=True, hide_index=True, column_config=cfg)
    with t3:
        cand = candidates(dets)
        st.caption(f"Candidates with confidence below {THRESHOLD:.0%} are NOT flagged. "
                   "Example: a 10-digit number without ID context or checksum is not treated as a Saudi ID.")
        if cand:
            st.dataframe(table(cand), use_container_width=True, hide_index=True, column_config=cfg)
        else:
            st.write("No low-confidence candidates.")
    with t4:
        st.caption("Type any text (Arabic digits work too) and compare the confidence with and without context.")
        txt = st.text_area("Text", "رقم الهوية: 1000000008  |  جوال العميل 0551234567  |  Random number: 1234567890", height=80)
        rows = analyze_text(txt)
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True) if rows else st.write("Nothing detected.")

    section_title("Explain a detection")
    if fl:
        pick = st.selectbox("Choose a finding", [f"{d.column} → {d.entity}" for d in fl])
        d = next(x for x in fl if f"{x.column} → {x.entity}" == pick)
        with card("explain"):
            st.markdown(f"**Entity:** {d.label} (`{d.entity}`) &nbsp; · &nbsp; **Column:** `{d.column}` &nbsp; · &nbsp; "
                        f"**Confidence:** {d.confidence:.0%} &nbsp; · &nbsp; **Category:** {d.category} identifier &nbsp; " + risk_badge(d.risk),
                        unsafe_allow_html=True)
            st.markdown("**Reason:**\n" + "\n".join(f"- {r}" for r in d.reasons))
            st.caption("Sample values: " + " | ".join(d.samples))
    next_button("Next → Configure anonymization", "Configure Anonymization")


# ================================================================== PAGE 4 – CONFIGURE
def page_configure():
    hero("Configure Anonymization", "Choose WHY the data will be shared, review the recommended techniques and change them if needed.")
    if not need_data():
        return
    df, dets = st.session_state.df, st.session_state.detections
    keys = list(PROFILES)
    cur = st.session_state.get("profile", "external")
    profile = st.radio("Purpose profile – why will this dataset be shared?", keys, index=keys.index(cur),
                       format_func=lambda k: PROFILES[k]["name"], horizontal=True, key="profile_radio")
    st.info(PROFILES[profile]["description"])
    if st.session_state.get("config_profile") != profile or "config" not in st.session_state:
        st.session_state.config = build_config(df, dets, profile)
        st.session_state.config_profile = profile
        st.session_state.profile = profile
        st.session_state.pop("result", None)

    base = st.session_state.config.copy()
    show = base.copy()
    show["Confidence"] = show["Confidence"].map(lambda x: "" if pd.isna(x) else f"{x:.0%}")
    section_title("Recommended technique per column",
                  "Change Method or Category if you disagree (e.g. confirm / remove suggested indirect identifiers).")
    edited = st.data_editor(
        show, key=f"editor_{profile}_{st.session_state.name}", use_container_width=True, hide_index=True,
        disabled=["Column", "Detected", "Confidence", "Recommended"],
        column_config={
            "Category": st.column_config.SelectboxColumn("Category", options=["Direct", "Indirect", "Non-sensitive"], required=True),
            "Method": st.column_config.SelectboxColumn("Method (editable)", options=METHODS, required=True),
        }, height=min(80 + 36 * len(show), 700))
    cfg = base.copy()
    cfg["Category"], cfg["Method"] = edited["Category"].values, edited["Method"].values

    #with st.expander("What do the techniques do?"):
       # for m, w in WHY.items():
          #  st.markdown(f"- **{m}** – {w}")
      #  st.caption("Examples: Masking 0551234567 → 055****567 · Suppression → [REMOVED] · Replacement → Person_001 · "
                  # "Generalization 23 → 20–25, 8,700 → 8,000–9,000 · Hashing → H_3fa9…")

    if st.button("🚀 Anonymize", type="primary"):
        with st.spinner("Applying anonymization and computing scores…"):
            meta_dets = dets
            anon, meta = anonymize(df, cfg, meta_dets, profile)
            risk = assess_risk(df, anon, cfg, meta)
            util = assess_utility(df, anon, cfg, meta)

        st.session_state.result = {
            "anon": anon,
            "meta": meta,
            "risk": risk,
            "utility": util,
            "config": cfg,
            "profile": profile
        }

        st.session_state.pop("report_md", None)

        save_state(st.session_state)

        goto("Results")


# ================================================================== PAGE 5 – RESULTS
def page_results():
    hero("Results – Before vs. After", "Privacy risk should drop a lot while data utility stays reasonably high.")
    if not need_data():
        return
    if "result" not in st.session_state:
        st.warning("Run the anonymization first.")
        if st.button("Go to Configure Anonymization"):
            goto("Configure Anonymization")
        return
    R = st.session_state.result
    df, anon, risk, util = st.session_state.df, R["anon"], R["risk"], R["utility"]
    st.caption(f"Profile used: **{PROFILES[R['profile']]['name']}**")

    drop = risk["before"] - risk["after"]
    good = risk["after"] < 30 and util["after"] >= 70
    if drop >= 40 and util["after"] >= 70:
        txt = (f"✅ <b>Privacy improved significantly</b> (risk {risk['before']} → {risk['after']}) "
               f"while <b>Data Utility remained high</b> ({util['after']}%).")
    elif drop > 0:
        txt = (f"Privacy improved (risk {risk['before']} → {risk['after']}, now {risk['level_after']}) and Data Utility is {util['after']}%. "
               "Try the <b>AI / External Company</b> profile or stronger methods for a bigger drop.")
    else:
        txt = "Privacy risk did not decrease – choose stronger techniques."
    verdict_banner(txt, "good" if (good or drop >= 40) else "warn")

    rtone = {"LOW": "good", "MEDIUM": "warn", "HIGH": "bad"}[risk["level_after"]]
    m = st.columns(4)
    with m[0]:
        metric_card("Prototype Re-identification Risk", f"{risk['after']} / 100", f"{risk['after'] - risk['before']:+d} (was {risk['before']})", rtone, 0)
    with m[1]:
        metric_card("Risk level", f"{risk_badge(risk['level_before'])} → {risk_badge(risk['level_after'])}", tone="neutral", index=1, raw=True)
    with m[2]:
        metric_card("Data Utility", f"{util['after']} %", f"{util['after'] - 100:+d} (was 100)", "accent", 2)
    with m[3]:
        metric_card("Direct identifiers still strongly exposed", len(risk["remaining_direct"]),
                    tone="bad" if risk["remaining_direct"] else "good", index=3)
    section_title("Privacy vs. utility")
    c1, c2 = st.columns(2)
    with c1, card("riskchart"):
        st.altair_chart(before_after_chart("Privacy Risk (lower is better)", risk["before"], risk["after"], True), use_container_width=True)
    with c2, card("utilchart"):
        st.altair_chart(before_after_chart("Data Utility (higher is better)", util["before"], util["after"], False), use_container_width=True)

    with st.expander("Why did the score change?", expanded=True):
        for r in risk["reasons"]:
            st.markdown(f"- {r}")
        st.dataframe(risk["direct_table"], use_container_width=True, hide_index=True)
        st.caption("Prototype Re-identification Risk = 55 × direct-identifier exposure + 45 × average re-identification probability of "
                   "quasi-identifier combinations. It is a transparent indicator, not a formal legal or scientific risk certification.")
    with st.expander("How is Data Utility calculated?"):
        st.dataframe(util["components"], use_container_width=True, hide_index=True)
        st.dataframe(util["columns"], use_container_width=True, hide_index=True)
        st.caption("Utility = 20% A + 20% B + 25% C + 15% D + 20% E. It does not represent every possible analytical use case.")

    section_title("Original vs. Anonymized dataset")
    changed = [c for c in df.columns if not df[c].astype(str).equals(anon[c].astype(str))]
    only = st.checkbox("Show only columns that changed", value=True)
    cols = changed if only and changed else list(df.columns)
    n = st.slider("Rows to show", 5, min(50, len(df)), min(12, len(df))) if len(df) > 5 else len(df)
    a, b = st.columns(2)
    a.markdown("**🔓 Original**")
    a.dataframe(df[cols].head(n), use_container_width=True, hide_index=True)
    b.markdown("**🔒 Anonymized**")
    b.dataframe(anon[cols].head(n), use_container_width=True, hide_index=True)

    section_title("Download")
    d1, d2, _ = st.columns([1, 1, 2])
    stem = os.path.splitext(st.session_state.name.split(" (")[0])[0]
    d1.download_button("⬇️ Anonymized CSV", csv_bytes(anon), f"{stem}_anonymized.csv", "text/csv")
    d2.download_button("⬇️ Anonymized Excel", xlsx_bytes(anon), f"{stem}_anonymized.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    next_button("Next → Generate privacy report", "Privacy Report")


# ================================================================== PAGE 6 – REPORT
def page_report():
    hero("Saudi Privacy Assessment Report", "The final outcome: what was found, what was done and what remains.")
    if not need_data():
        return
    if "result" not in st.session_state:
        st.warning("Run the anonymization first.")
        if st.button("Go to Configure Anonymization"):
            goto("Configure Anonymization")
        return
    R = st.session_state.result
    risk, util, cfg = R["risk"], R["utility"], R["config"]
    tone = {"LOW": "good", "MEDIUM": "warn", "HIGH": "bad"}[risk["level_after"]]

    # --- outcome: two animated score rings -------------------------------------------------
    c1, c2 = st.columns(2)
    with c1, card("ring_risk"):
        score_ring(risk["after"], "Prototype Re-identification Risk", tone,
                   f"Before: {risk['before']} / 100 ({risk['level_before']})", risk_badge(risk["level_after"], large=True))
    with c2, card("ring_util"):
        score_ring(util["after"], "Data Utility", "good" if util["after"] >= 70 else "warn",
                   "Original dataset = 100 · higher is better")

    # --- detected info + techniques ----------------------------------------------------------
    left, right = st.columns(2)
    with left, card("detected"):
        st.markdown("**Detected sensitive information**")
        fl = flagged(st.session_state.detections)
        st.markdown("".join(pill(f"{d.column} · {d.label}", {"HIGH": "bad", "MEDIUM": "warn", "LOW": "good"}[d.risk]) for d in fl)
                    or "None", unsafe_allow_html=True)
    with right, card("techniques"):
        st.markdown("**Applied anonymization techniques**")
        ch = cfg[cfg["Method"] != "Keep"]
        st.markdown("".join(pill(f"{r['Column']} → {r['Method']}", "accent") for _, r in ch.iterrows()) or "None", unsafe_allow_html=True)

    # --- recommendations ---------------------------------------------------------------------
    section_title("Recommendations")
    recs = recommendations(risk, util, cfg, R["profile"])
    st.markdown("".join(f"<div class='rec' style='--i:{i}'><span class='n'>{i + 1:02d}</span><span>{r.replace('**', '')}</span></div>"
                        for i, r in enumerate(recs)), unsafe_allow_html=True)

    # --- export ------------------------------------------------------------------------------
    section_title("Export", "Generate the full report, then download it or the anonymized dataset.")
    if st.button("📝 Generate report", type="primary") or "report_md" in st.session_state:
        if "report_md" not in st.session_state:
            st.session_state.report_md = build_markdown(
                st.session_state.name, st.session_state.df, R["anon"], st.session_state.detections, R["config"],
                R["risk"], R["utility"], R["profile"], R["meta"])
            save_state(st.session_state)
        md = st.session_state.report_md
        d1, d2, d3, _ = st.columns([1.2, 1, 1, 1])
        d1.download_button("⬇️ Report (HTML – print to PDF)", build_html(md), "saudi_privacy_assessment_report.html", "text/html")
        d2.download_button("⬇️ Report (Markdown)", md, "saudi_privacy_assessment_report.md", "text/markdown")
        stem = os.path.splitext(st.session_state.name.split(" (")[0])[0]
        d3.download_button("⬇️ Anonymized CSV", csv_bytes(R["anon"]), f"{stem}_anonymized.csv", "text/csv")
        with card("fullreport"):
            st.markdown(md)
    else:
        st.info("Click **Generate report** to build the Saudi Privacy Assessment Report.")
    st.warning(DISCLAIMER)


PAGE_FUNCS = {"Dashboard": page_dashboard, "Upload Dataset": page_upload, "Sensitive Data Detection": page_detection,
              "Configure Anonymization": page_configure, "Results": page_results, "Privacy Report": page_report}
with animated_container(st.session_state["_epoch"], st.session_state["_direction"]):
    PAGE_FUNCS[page]()
    # 8 / oct / 2026