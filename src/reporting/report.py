# -*- coding: utf-8 -*-
"""Saudi Privacy Assessment Report (Markdown + printable HTML)."""
from datetime import datetime
from html import escape

from ..anonymization.profiles import PROFILES
from ..detection.detector import ENTITY_LABEL, flagged

DISCLAIMER = ("This prototype assists privacy assessment and data anonymization. It does not constitute legal advice "
              "or guarantee compliance with the Saudi Personal Data Protection Law (PDPL).")


def recommendations(risk, utility, config, profile_key):
    recs = []
    for x in risk["remaining_direct"]:
        recs.append(f"Column **{x['Column']}** is still strongly exposed (method: {x['Method']}). Use Suppression or Replacement.")
    kept_direct = config[(config["Category"] == "Direct") & (config["Method"] == "Keep")]["Column"].tolist()
    if kept_direct:
        recs.append("Direct identifiers left unchanged: " + ", ".join(kept_direct) + ".")
    if risk["k_after"] is not None and risk["k_after"] < 3:
        recs.append("Some records are still unique on the quasi-identifiers (k < 3). Consider wider generalization "
                    "or suppressing one of the quasi-identifiers" + ("." if profile_key == "external" else ", or the 'AI / External Company' profile."))
    if risk["after"] >= 60:
        recs.append("Prototype risk is still HIGH – do not share this dataset externally before further anonymization.")
    elif risk["after"] >= 30:
        recs.append("Prototype risk is MEDIUM – acceptable at most for trusted internal use; review before external sharing.")
    if utility["after"] < 70:
        recs.append("Data utility dropped noticeably. If the purpose allows it, keep low-risk columns or use narrower bins.")
    recs.append("Free-text columns may contain names or other details that this prototype cannot detect – review them manually.")
    recs.append("Have the sharing decision reviewed by your organisation's data-protection officer / legal team.")
    return recs


def build_markdown(name, orig, anon, detections, config, risk, utility, profile_key, meta) -> str:
    fl = flagged(detections)
    p = PROFILES[profile_key]
    ent_types = sorted({ENTITY_LABEL.get(d.entity, d.entity) for d in fl})
    direct_cols = sorted({d.column for d in fl if d.category == "Direct"})
    indirect_cols = sorted({d.column for d in fl if d.category == "Indirect"})
    changed = config[config["Method"] != "Keep"]
    L = [f"# Saudi Privacy Assessment Report", "",
         f"- **Dataset:** {name}", f"- **Date:** {datetime.now():%Y-%m-%d %H:%M}",
         f"- **Number of records:** {len(orig):,}  |  **Columns:** {orig.shape[1]}",
         f"- **Sharing purpose (profile):** {p['name']}", "",
         "## 1. Sensitive information detected", "",
         f"- **Sensitive fields:** {len({d.column for d in fl})}",
         f"- **Types of sensitive information:** {', '.join(ent_types) or 'none'}", "",
         "| Column | Entity | Category | Confidence | Risk | Why it was detected |", "|---|---|---|---|---|---|"]
    for d in sorted(fl, key=lambda d: (d.category, d.column)):
        L.append(f"| {d.column} | {d.label} | {d.category} | {d.confidence:.0%} | {d.risk} | {'; '.join(d.reasons)} |")
    L += ["", "## 2. Anonymization methods applied", "", "| Column | Category | Method |", "|---|---|---|"]
    for _, r in changed.iterrows():
        L.append(f"| {r['Column']} | {r['Category']} | {r['Method']} |")
    if changed.empty:
        L.append("| – | – | No changes applied |")
    L += ["", "## 3. Identifier status after anonymization", "",
          f"- **Direct identifiers detected:** {', '.join(direct_cols) or 'none'}",
          "- **Direct identifiers still strongly exposed:** " +
          (", ".join(x['Column'] for x in risk['remaining_direct']) or "none"),
          f"- **Potential indirect identifiers (quasi-identifiers):** {', '.join(indirect_cols) or 'none'}",
          "", "## 4. Prototype Re-identification Risk", "",
          f"- **Before:** {risk['before']} / 100 ({risk['level_before']})",
          f"- **After:** {risk['after']} / 100 ({risk['level_after']})", ""]
    L += [f"- {r}" for r in risk["reasons"]]
    L += ["", "## 5. Data Utility", "",
          f"- **Before:** 100 / 100  |  **After:** {utility['after']} / 100", "",
          "| Factor | Weight | Value |", "|---|---|---|"]
    L += [f"| {r['Factor']} | {r['Weight']} | {r['Value']} |" for _, r in utility["components"].iterrows()]
    L += ["", "## 6. Recommendations", ""]
    L += [f"- {r}" for r in recommendations(risk, utility, config, profile_key)]
    L += ["", "## Method notes", "",
          "- Detection: Microsoft Presidio pattern recognizers + Saudi validators (ID checksum, IBAN mod-97) + Arabic context rules.",
          "- The risk and utility scores are simple, transparent prototype indicators, not formal certifications, "
          "and do not represent every possible analytical use case.", "",
          f"> **Disclaimer:** {DISCLAIMER}", ""]
    return "\n".join(L)


_CSS = """body{font-family:Segoe UI,Tahoma,Arial,sans-serif;max-width:900px;margin:30px auto;padding:0 20px;color:#1f2933;line-height:1.55}
h1{color:#0b5d3b;border-bottom:3px solid #0b5d3b;padding-bottom:8px}h2{color:#0b5d3b;margin-top:28px}
table{border-collapse:collapse;width:100%;font-size:13px}th,td{border:1px solid #cfd8dc;padding:6px 8px;text-align:left;vertical-align:top}
th{background:#e8f3ee}blockquote{background:#fff7e6;border-left:4px solid #f0a500;margin:20px 0;padding:10px 16px}"""


def build_html(md_text: str) -> str:
    try:
        import markdown
        body = markdown.markdown(md_text, extensions=["tables"])
    except Exception:  # pragma: no cover
        body = f"<pre>{escape(md_text)}</pre>"
    return f"<!doctype html><html><head><meta charset='utf-8'><title>Saudi Privacy Assessment Report</title><style>{_CSS}</style></head><body>{body}</body></html>"
