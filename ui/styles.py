# -*- coding: utf-8 -*-
"""Global CSS for the dark privacy-dashboard look. Uses data-testid and st-key-* hooks (stable across Streamlit versions)."""
import streamlit as st

_CSS = """
<style>
:root{
  --bg:#0A0E14; --bg2:#0E141C; --card:#111925; --card2:#162130;
  --border:rgba(255,255,255,.08); --border-hi:rgba(45,212,191,.38);
  --text:#E8EEF5; --muted:#8A98A8;
  --accent:#2DD4BF; --accent2:#38BDF8;
  --good:#34D399; --warn:#FBBF24; --bad:#F87171;
  --ease:cubic-bezier(.22,.8,.3,1); --nav-w:118px;
}
html,body,[data-testid="stApp"]{font-family:Inter,"Segoe UI",Tahoma,system-ui,-apple-system,sans-serif}
[data-testid="stApp"]{
  background:
    radial-gradient(1100px 560px at 12% -8%, rgba(45,212,191,.10), transparent 60%),
    radial-gradient(900px 520px at 100% 0%, rgba(56,189,248,.08), transparent 55%),
    linear-gradient(180deg,var(--bg) 0%,var(--bg2) 100%);
}
[data-testid="stHeader"]{background:transparent}
[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"],[data-testid="stDecoration"],footer{display:none!important}
[data-testid="stElementContainer"]:has(style){display:none}
[data-testid="stMain"]{overflow-x:hidden}
[data-testid="stMainBlockContainer"],.block-container{max-width:1180px;padding-top:2.2rem;padding-bottom:9rem}

/* ---------- page entrance ---------- */
@keyframes pageInA{from{opacity:0;transform:translate3d(var(--enter-x,18px),10px,0) scale(.992)}to{opacity:1;transform:none}}
@keyframes pageInB{from{opacity:0;transform:translate3d(var(--enter-x,18px),10px,0) scale(.992)}to{opacity:1;transform:none}}
[class*="st-key-page_"]{--enter-x:18px}
[class*="st-key-page_"][class*="_back"]{--enter-x:-18px}
[class*="st-key-page_0_"]{animation:pageInA .38s var(--ease) backwards}
[class*="st-key-page_1_"]{animation:pageInB .38s var(--ease) backwards}
[data-stale="true"]{opacity:.6!important;transition:opacity .2s ease}
@keyframes rise{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}

/* ---------- page header ---------- */
.ph{margin:0 0 1.4rem}
.ph-eyebrow{font-size:.72rem;font-weight:700;letter-spacing:.18em;color:var(--accent);animation:rise .4s var(--ease) backwards}
.ph-title{font-size:2.15rem;font-weight:750;letter-spacing:-.02em;line-height:1.15;color:var(--text);margin:.25rem 0 .35rem;animation:rise .4s var(--ease) 40ms backwards}
.ph-desc{color:var(--muted);font-size:1rem;margin:0;max-width:760px;animation:rise .4s var(--ease) 80ms backwards}

.chips{display:flex;flex-wrap:wrap;gap:8px;margin:.9rem 0 1.3rem;animation:rise .4s var(--ease) 120ms backwards}
.chip{display:inline-flex;align-items:center;gap:7px;padding:5px 12px;border-radius:999px;font-size:.78rem;color:var(--muted);background:rgba(255,255,255,.04);border:1px solid var(--border)}
.chip b{color:var(--text);font-weight:600}

.dot{width:7px;height:7px;border-radius:50%;background:var(--muted);display:inline-block}
.dot.on{background:var(--good);box-shadow:0 0 8px var(--good)}

/* ---------- cards ---------- */
[class*="st-key-card_"]{
  background:linear-gradient(180deg,var(--card2),var(--card));
  border:1px solid var(--border)!important;
  border-radius:18px!important;
  padding:1.1rem 1.25rem!important;
  box-shadow:0 8px 28px rgba(0,0,0,.28);
  transition:transform .25s var(--ease),border-color .25s ease,box-shadow .25s ease;
}

[class*="st-key-card_"]:hover{
  border-color:rgba(255,255,255,.14)!important;
}

.mcard{
  position:relative;
  overflow:hidden;
  background:linear-gradient(180deg,var(--card2),var(--card));
  border:1px solid var(--border);
  border-radius:16px;
  padding:16px 18px;
  min-height:124px;
  box-shadow:0 8px 24px rgba(0,0,0,.25);
  animation:rise .45s var(--ease) calc(var(--i,0)*60ms) backwards;
  transition:transform .25s var(--ease),border-color .25s ease,box-shadow .25s ease;
}

.mcard::before{
  content:"";
  position:absolute;
  left:0;
  top:0;
  height:2px;
  width:100%;
  background:linear-gradient(90deg,var(--tone,var(--accent)),transparent);
}

.mcard:hover{
  transform:translateY(-2px);
  border-color:rgba(45,212,191,.35);
  box-shadow:0 14px 34px rgba(0,0,0,.4);
}

.mcard .ml{
  font-size:.74rem;
  font-weight:600;
  letter-spacing:.06em;
  text-transform:uppercase;
  color:var(--muted);
}

.mcard .mv{
  font-size:1.85rem;
  font-weight:750;
  letter-spacing:-.02em;
  color:var(--text);
  margin-top:6px;
  line-height:1.1;
}

.mcard .md{
  font-size:.8rem;
  margin-top:6px;
  color:var(--muted);
}

.mcard .md.good{color:var(--good)}
.mcard .md.bad{color:var(--bad)}
.mcard .md.warn{color:var(--warn)}

.mcard.good{--tone:var(--good)}
.mcard.bad{--tone:var(--bad)}
.mcard.warn{--tone:var(--warn)}
.mcard.accent{--tone:var(--accent2)}

.sec{margin:1.6rem 0 .7rem}
.sec .st{font-size:1.15rem;font-weight:700;color:var(--text)}
.sec .ss{font-size:.88rem;color:var(--muted);margin-top:2px}

.verdict{
  border:1px solid rgba(52,211,153,.35);
  background:linear-gradient(90deg,rgba(52,211,153,.12),rgba(52,211,153,.03));
  border-radius:14px;
  padding:14px 18px;
  margin:6px 0 16px;
  color:var(--text);
  animation:rise .45s var(--ease) backwards;
}

.verdict.warn{
  border-color:rgba(251,191,36,.4);
  background:linear-gradient(90deg,rgba(251,191,36,.12),rgba(251,191,36,.03));
}

.verdict.bad{
  border-color:rgba(248,113,113,.4);
  background:linear-gradient(90deg,rgba(248,113,113,.12),rgba(248,113,113,.03));
}

/* ---------- badges ---------- */
.badge{
  display:inline-flex;
  align-items:center;
  gap:7px;
  padding:4px 12px;
  border-radius:999px;
  font-size:.78rem;
  font-weight:750;
  letter-spacing:.08em;
  border:1px solid;
  transition:transform .2s ease,box-shadow .2s ease;
}

.badge i{
  width:7px;
  height:7px;
  border-radius:50%;
  background:currentColor;
  box-shadow:0 0 8px currentColor;
}

.badge:hover{transform:scale(1.04)}

.badge-high{
  color:var(--bad);
  background:rgba(248,113,113,.12);
  border-color:rgba(248,113,113,.4);
}

.badge-medium{
  color:var(--warn);
  background:rgba(251,191,36,.12);
  border-color:rgba(251,191,36,.4);
}

.badge-low{
  color:var(--good);
  background:rgba(52,211,153,.12);
  border-color:rgba(52,211,153,.4);
}

.badge.lg{
  font-size:.95rem;
  padding:7px 18px;
}

.pill{
  display:inline-block;
  padding:3px 11px;
  margin:0 6px 6px 0;
  border-radius:999px;
  font-size:.78rem;
  border:1px solid var(--border);
  background:rgba(255,255,255,.04);
  color:var(--text);
}

.pill.accent{
  color:var(--accent);
  border-color:rgba(45,212,191,.35);
  background:rgba(45,212,191,.08);
}

.pill.bad{
  color:var(--bad);
  border-color:rgba(248,113,113,.35);
}

.pill.warn{
  color:var(--warn);
  border-color:rgba(251,191,36,.35);
}

.pill.good{
  color:var(--good);
  border-color:rgba(52,211,153,.35);
}

/* ---------- score rings ---------- */
@property --p{
  syntax:"<number>";
  inherits:false;
  initial-value:0;
}

@keyframes ringFill{
  from{--p:0}
}

.ringwrap{
  display:flex;
  align-items:center;
  gap:20px;
}

.ring{
  --p:0;
  --c:var(--accent);
  width:132px;
  height:132px;
  border-radius:50%;
  flex:none;
  display:grid;
  place-items:center;
  position:relative;
  background:conic-gradient(var(--c) calc(var(--p)*1%),rgba(255,255,255,.07) 0);
  animation:ringFill 1.1s var(--ease) backwards;
}

.ring::before{
  content:"";
  position:absolute;
  inset:11px;
  border-radius:50%;
  background:var(--card);
}

.ring span{
  position:relative;
  font-size:2rem;
  font-weight:800;
  color:var(--text);
}

.ring.good{--c:var(--good)}
.ring.warn{--c:var(--warn)}
.ring.bad{--c:var(--bad)}

.ringtxt .rl{
  font-size:.74rem;
  font-weight:600;
  letter-spacing:.08em;
  text-transform:uppercase;
  color:var(--muted);
  margin-bottom:6px;
}

.ringtxt .rs{
  font-size:.85rem;
  color:var(--muted);
  margin-top:8px;
}

.rec{
  display:flex;
  gap:12px;
  padding:12px 14px;
  border:1px solid var(--border);
  border-radius:12px;
  background:rgba(255,255,255,.025);
  margin-bottom:8px;
  transition:border-color .2s ease,transform .2s ease;
  animation:rise .4s var(--ease) calc(var(--i,0)*50ms) backwards;
}

.rec:hover{
  border-color:var(--border-hi);
  transform:translateX(2px);
}

.rec .n{
  color:var(--accent);
  font-weight:800;
}

.steps{
  display:flex;
  gap:8px;
  flex-wrap:wrap;
  margin:.4rem 0 0;
}

.step{
  flex:1;
  min-width:120px;
  padding:10px 12px;
  border-radius:12px;
  border:1px solid var(--border);
  background:rgba(255,255,255,.03);
  font-size:.82rem;
  color:var(--muted);
  transition:border-color .2s,color .2s;
}

.step b{
  display:block;
  color:var(--accent);
  font-size:.72rem;
  letter-spacing:.12em;
}

.step:hover{
  border-color:var(--border-hi);
  color:var(--text);
}

/* ---------- buttons ---------- */
[data-testid="stButton"] button,
[data-testid="stDownloadButton"] button,
[data-testid="stFileUploader"] button{
  border-radius:12px;
  padding:.55rem 1.15rem;
  font-weight:600;
  letter-spacing:.01em;
  border:1px solid var(--border);
  background:rgba(255,255,255,.05);
  color:var(--text);
  transition:transform .2s ease,
             background-color .2s ease,
             border-color .2s ease,
             box-shadow .2s ease;
}

[data-testid="stButton"] button:hover,
[data-testid="stDownloadButton"] button:hover,
[data-testid="stFileUploader"] button:hover{
  transform:translateY(-1px);
  border-color:var(--border-hi);
  background:rgba(45,212,191,.09);
  box-shadow:0 8px 22px rgba(0,0,0,.35);
}

[data-testid="stButton"] button:active,
[data-testid="stDownloadButton"] button:active{
  transform:translateY(0) scale(.98);
  box-shadow:none;
}

[data-testid="stButton"] button[kind="primary"],
[data-testid="stBaseButton-primary"]{
  background:linear-gradient(135deg,#14B8A6,#0EA5E9)!important;
  border-color:transparent!important;
  color:#04121A!important;
  box-shadow:0 8px 24px rgba(20,184,166,.28);
}

[data-testid="stButton"] button[kind="primary"]:hover,
[data-testid="stBaseButton-primary"]:hover{
  filter:brightness(1.08);
  box-shadow:0 12px 30px rgba(20,184,166,.4);
}

[data-testid="stButton"] button p,
[data-testid="stDownloadButton"] button p{
  font-weight:600;
}

/* ---------- upload zone ---------- */
[data-testid="stFileUploaderDropzone"]{
  flex-direction:column;
  align-items:center;
  justify-content:center;
  gap:10px;
  min-height:230px;
  text-align:center;
  border:2px dashed rgba(45,212,191,.35);
  border-radius:22px;
  background:
    radial-gradient(500px 200px at 50% 0%,rgba(45,212,191,.09),transparent 70%),
    rgba(255,255,255,.02);
  transition:border-color .3s ease,
             background-color .3s ease,
             transform .3s var(--ease),
             box-shadow .3s ease;
}

[data-testid="stFileUploaderDropzone"]::before{
  content:"";
  width:64px;
  height:64px;
  border-radius:18px;
  background:rgba(45,212,191,.12)
  url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='30' height='30' viewBox='0 0 24 24' fill='none' stroke='%232DD4BF' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><path d='M12 16V4'/><path d='M7 9l5-5 5 5'/><path d='M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3'/></svg>")
  center/30px no-repeat;
  border:1px solid rgba(45,212,191,.3);
  transition:transform .3s var(--ease);
}

[data-testid="stFileUploaderDropzone"]:hover{
  border-color:var(--accent);
  background-color:rgba(45,212,191,.05);
  transform:scale(1.004);
  box-shadow:0 0 0 4px rgba(45,212,191,.07);
}

[data-testid="stFileUploaderDropzone"]:hover::before{
  transform:translateY(-3px);
}

[data-testid="stFileUploaderDropzone"]::after{
  content:"Drag & drop your file here, or";
  order:1;
  color:var(--text);
  font-weight:600;
  font-size:1rem;
  font-family:inherit;
}

[data-testid="stFileUploaderDropzone"]>span{order:2}

[data-testid="stFileUploaderDropzoneInstructions"]{
  order:3;
  align-items:center;
  text-align:center;
}

.upl-h{margin:0 0 .6rem}
.upl-h .t{font-size:1.1rem;font-weight:700}
.upl-h .s{color:var(--muted);font-size:.88rem}

/* ---------- tabs, expanders, tables, inputs ---------- */
[data-baseweb="tab-list"]{gap:6px}

button[data-baseweb="tab"]{
  border-radius:10px 10px 0 0;
  transition:background-color .2s ease,color .2s ease;
}

button[data-baseweb="tab"]:hover{
  background:rgba(45,212,191,.08);
}

[data-baseweb="tab-highlight"]{
  background:var(--accent)!important;
  height:2px!important;
  transition:all .3s var(--ease);
}

[data-testid="stExpander"] details{
  border:1px solid var(--border);
  border-radius:14px;
  background:rgba(255,255,255,.025);
  transition:border-color .2s ease,background-color .2s ease;
}

[data-testid="stExpander"] details:hover{
  border-color:rgba(255,255,255,.16);
}

[data-testid="stExpander"] summary{
  transition:background-color .2s ease;
}

[data-testid="stExpander"] summary:hover{
  background:rgba(255,255,255,.04);
}

[data-testid="stDataFrame"],
[data-testid="stDataEditor"]{
  border:1px solid var(--border);
  border-radius:14px;
  overflow:hidden;
}

[data-testid="stAlert"]{
  border-radius:14px;
}

div[data-baseweb="select"]>div,
[data-testid="stTextArea"] textarea{
  border-radius:12px;
  transition:border-color .2s ease,box-shadow .2s ease;
}

/* ---------- profile selector ---------- */
.st-key-profile_radio div[role="radiogroup"]{
  gap:10px;
  flex-wrap:wrap;
}

.st-key-profile_radio label[data-testid="stRadioOption"]{
  padding:10px 18px;
  border:1px solid var(--border);
  border-radius:14px;
  background:rgba(255,255,255,.03);
  cursor:pointer;
  transition:border-color .2s ease,
             background-color .2s ease,
             transform .2s ease;
}

.st-key-profile_radio label[data-testid="stRadioOption"]:hover{
  transform:translateY(-1px);
  border-color:var(--border-hi);
}

.st-key-profile_radio label[data-selected="true"]{
  border-color:var(--accent);
  background:rgba(45,212,191,.1);
}

.st-key-profile_radio label[data-testid="stRadioOption"]>div>div:first-child{
  display:none;
}

/* ---------- floating bottom navigation ---------- */
.st-key-bottom_nav{
  position:fixed;
  left:50%;
  bottom:20px;
  transform:translateX(-50%);
  z-index:1000;
  width:max-content;
  max-width:calc(100vw - 20px);
  padding:6px;
  border-radius:999px;
  background:rgba(15,22,32,.72);
  -webkit-backdrop-filter:blur(18px) saturate(150%);
  backdrop-filter:blur(18px) saturate(150%);
  border:1px solid rgba(255,255,255,.1);
  box-shadow:
    0 18px 50px rgba(0,0,0,.55),
    inset 0 1px 0 rgba(255,255,255,.06);
}

.st-key-bottom_nav [data-testid="stRadio"]{
  width:auto;
}

.st-key-bottom_nav div[role="radiogroup"]{
  position:relative;
  display:flex;
  flex-wrap:nowrap;
  gap:0;
  overflow-x:auto;
  scrollbar-width:none;
}

.st-key-bottom_nav div[role="radiogroup"]::-webkit-scrollbar{
  display:none;
}

.st-key-bottom_nav div[role="radiogroup"]::before{
  content:"";
  position:absolute;
  top:0;
  bottom:0;
  left:0;
  width:var(--nav-w);
  border-radius:999px;
  background:linear-gradient(
    135deg,
    rgba(45,212,191,.22),
    rgba(56,189,248,.16)
  );
  border:1px solid rgba(45,212,191,.45);
  box-shadow:0 0 22px rgba(45,212,191,.18);
  transition:transform .42s var(--ease);
  pointer-events:none;
}

.st-key-bottom_nav div[role="radiogroup"]:has(>div:nth-child(2)[data-selected="true"])::before{
  transform:translateX(calc(1*var(--nav-w)));
}

.st-key-bottom_nav div[role="radiogroup"]:has(>div:nth-child(3)[data-selected="true"])::before{
  transform:translateX(calc(2*var(--nav-w)));
}

.st-key-bottom_nav div[role="radiogroup"]:has(>div:nth-child(4)[data-selected="true"])::before{
  transform:translateX(calc(3*var(--nav-w)));
}

.st-key-bottom_nav div[role="radiogroup"]:has(>div:nth-child(5)[data-selected="true"])::before{
  transform:translateX(calc(4*var(--nav-w)));
}

.st-key-bottom_nav div[role="radiogroup"]:has(>div:nth-child(6)[data-selected="true"])::before{
  transform:translateX(calc(5*var(--nav-w)));
}

.st-key-bottom_nav div[role="radiogroup"]>div{
  position:relative;
  z-index:1;
  flex:0 0 var(--nav-w);
  width:var(--nav-w);
  margin:0;
  padding:0;
}

.st-key-bottom_nav label[data-testid="stRadioOption"]{
  display:flex;
  justify-content:center;
  width:100%;
  margin:0;
  padding:11px 0;
  border-radius:999px;
  cursor:pointer;
  transition:transform .2s ease;
}

.st-key-bottom_nav label[data-testid="stRadioOption"]>div{
  margin:0;
  padding:0;
}

.st-key-bottom_nav label[data-testid="stRadioOption"]>div>div:first-child{
  display:none;
}

.st-key-bottom_nav label p{
  margin:0;
  text-align:center;
  font-size:.8rem;
  font-weight:650;
  letter-spacing:.03em;
  color:var(--muted);
  white-space:nowrap;
  transition:color .25s ease,transform .25s ease;
}

.st-key-bottom_nav label:hover p{
  color:var(--text);
}

.st-key-bottom_nav label:hover{
  transform:translateY(-1px);
  background:rgba(255,255,255,.05);
}

.st-key-bottom_nav label[data-selected="true"] p{
  color:var(--accent);
  transform:scale(1.05);
}

@media (max-width:720px){
  :root{--nav-w:92px}

  .st-key-bottom_nav{
    bottom:12px;
  }

  .st-key-bottom_nav label p{
    font-size:.72rem;
  }

  .ph-title{
    font-size:1.65rem;
  }

  .ringwrap{
    flex-direction:column;
    align-items:flex-start;
  }
}

@media (prefers-reduced-motion:reduce){
  *{
    animation:none!important;
    transition:none!important;
  }
}
</style>
"""


def inject_global_css():
    """Call once per run, right after st.set_page_config()."""
    st.markdown(_CSS, unsafe_allow_html=True)