from __future__ import annotations
import streamlit as st


def apply_light_theme() -> None:
    """Inject the full light-theme CSS for Finance Decision Studio."""
    st.markdown(
        """
<style>
:root {
  --bg: #f2f4f6;
  --panel: #fbfcfd;
  --sidebar: #e6eaee;
  --ink: #17212b;
  --muted: #667381;
  --line: #d3d9df;
  --brand: #315c6d;
  --brand2: #4f7f82;
  --good: #267054;
  --warn: #9a6818;
  --danger: #a84646;
  --primary: #315c6d;
  --primary-dark: #274b59;
  --primary-soft: #eef2ff;
  --surface: #ffffff;
  --success-soft: #edf9f3;
  --warning-soft: #fff8e6;
  --danger-soft: #fff1f1;
}
html, body, [class*="css"], .stApp, [data-testid="stAppViewContainer"] {
  background: var(--bg) !important;
  color: var(--ink) !important;
  font-family: Inter, "Segoe UI", Arial, sans-serif !important;
}
[data-testid="stHeader"] { background: rgba(242,244,246,.94) !important; border-bottom: 1px solid var(--line); }
[data-testid="stToolbar"] { color: var(--ink) !important; }
[data-testid="stSidebar"] {
  background: var(--sidebar) !important;
  border-right: 1px solid #cbd2d9 !important;
  box-shadow: 6px 0 24px rgba(26,49,92,.035) !important;
}
[data-testid="stSidebar"] * { color: var(--ink) !important; }
[data-testid="stSidebar"] .stCaptionContainer p { color: var(--muted) !important; }
[data-testid="stSidebar"] [role="radiogroup"] label {
  padding: .48rem .65rem !important;
  border-radius: 9px !important;
  transition: background .15s ease !important;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: #f3f6fb !important; }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
  background: var(--primary-soft) !important;
  color: var(--primary) !important;
  font-weight: 700 !important;
}
[data-testid="stSidebar"] .stButton > button {
  background: #1d2b35 !important;
  border: 1px solid #1d2b35 !important;
  color: #ffffff !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background: #10212d !important;
  border-color: #10212d !important;
  color: #ffffff !important;
}
.block-container { max-width: 1420px !important; padding: 2rem 2.25rem 4rem !important; }
h1 { font-size: 2rem !important; line-height: 1.16 !important; letter-spacing: -.035em !important; margin-bottom: .35rem !important; }
h2 { font-size: 1.35rem !important; letter-spacing: -.02em !important; }
h3 { font-size: 1.05rem !important; }
.stCaptionContainer p, [data-testid="stCaptionContainer"] p, .stMarkdown p { color: var(--muted) !important; }
[data-testid="stMetric"] {
  background: var(--panel) !important;
  border: 1px solid var(--line) !important;
  border-radius: 12px !important;
  padding: 1rem 1.1rem !important;
  box-shadow: 0 1px 2px rgba(23,33,43,.025) !important;
}
[data-testid="stMetricLabel"] p { color: var(--muted) !important; font-size: .74rem !important; text-transform: uppercase; letter-spacing: .055em; font-weight: 650 !important; }
[data-testid="stMetricValue"] { color: var(--ink) !important; font-size: 1.7rem !important; font-weight: 680 !important; }
.stButton > button, .stDownloadButton > button {
  min-height: 42px !important;
  border-radius: 9px !important;
  border: 1px solid #bcc6ce !important;
  background: var(--surface) !important;
  color: var(--ink) !important;
  font-weight: 650 !important;
  box-shadow: none !important;
}
.stButton > button[kind="primary"] {
  background: var(--primary) !important;
  border-color: var(--primary) !important;
  color: #fff !important;
}
.stButton > button[kind="primary"]:hover { background: var(--primary-dark) !important; border-color: var(--primary-dark) !important; color: #fff !important; }
.stTextInput input, .stTextArea textarea {
  background: #fbfcfd !important;
  border: 1px solid #bfc8d0 !important;
  border-radius: 9px !important;
  color: var(--ink) !important;
}
.stTextInput label, .stTextArea label, .stSelectbox label, .stSlider label, .stFileUploader label {
  font-weight: 700 !important;
}
[data-testid="stFileUploaderDropzone"] {
  background: var(--panel) !important;
  border: 1px dashed #aeb9c3 !important;
  border-radius: 12px !important;
  padding: 1rem !important;
}
[data-testid="stFileUploaderDropzone"] button { background: #e1e7eb !important; color: #263746 !important; border: 1px solid #bdc8d0 !important; }
[data-testid="stDataFrame"], [data-testid="stTable"] {
  background: var(--panel) !important;
  border: 1px solid var(--line) !important;
  border-radius: 10px !important;
  overflow: hidden !important;
}
[data-testid="stExpander"] { background: var(--panel) !important; border: 1px solid var(--line) !important; border-radius: 10px !important; }
div[data-testid="stAlert"] { border-radius: 10px !important; border-width: 1px !important; padding: .8rem 1rem !important; }
[data-testid="stAlert"] p { color: var(--ink) !important; }
[data-testid="stStatusWidget"] { background: var(--panel) !important; border-color: var(--line) !important; }
hr { border-color: var(--line) !important; }
.hero { background: linear-gradient(135deg, #fbfcfd, #e7edef); border: 1px solid var(--line); border-radius: 15px; padding: 1.45rem 1.6rem; margin-bottom: 1.25rem; }
.hero p { max-width: 760px; margin: .35rem 0 0; }
.kicker { color: var(--brand2); font-size: .72rem; letter-spacing: .09em; text-transform: uppercase; font-weight: 750; margin-bottom: .45rem; }
.section-head { display: flex; justify-content: space-between; align-items: end; margin: 1.6rem 0 .75rem; }
.section-head small { color: var(--muted); }
.rule-card { background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 1.15rem; margin-bottom: .8rem; }
[data-testid="stSidebar"] [role="radiogroup"] { padding: .12rem 0; }
.login-shell { max-width: 680px; margin: 5vh auto 1.25rem; background: #fff; border: 1px solid var(--line); border-radius: 18px; padding: 1.8rem 2rem; text-align: center; box-shadow: 0 12px 36px rgba(17,38,54,.08); }
.login-shell p { margin: .5rem 0 0 !important; }
.login-shell .kicker { color: var(--brand); }
button[kind="primaryFormSubmit"] { color: #ffffff !important; }
button[kind="primaryFormSubmit"]:hover { color: #ffffff !important; }
@media (max-width: 900px) { .block-container { padding: 1.2rem; } .hero { padding: 1.15rem; } }
/* ── Component library ── */
.page-header { margin-bottom: 1.5rem; }
.page-header h1 { margin-bottom: .4rem !important; }
.page-header .lead { color: var(--muted) !important; font-size: 1.05rem !important; max-width: 720px; margin-top: .3rem !important; }
.empty-state { text-align: center; padding: 2rem 1rem; }
.empty-icon { font-size: 3rem; margin-bottom: .75rem; }
.empty-state h3 { color: var(--ink) !important; margin-bottom: .3rem !important; }
.empty-state p { color: var(--muted) !important; }
.status-success { background: var(--success-soft) !important; border: 1px solid var(--good) !important; border-radius: 10px !important; padding: .8rem 1rem !important; color: var(--good) !important; font-weight: 600; margin-bottom: 1rem; }
.status-warning { background: var(--warning-soft) !important; border: 1px solid var(--warn) !important; border-radius: 10px !important; padding: .8rem 1rem !important; color: var(--warn) !important; font-weight: 600; margin-bottom: 1rem; }
.status-error { background: var(--danger-soft) !important; border: 1px solid var(--danger) !important; border-radius: 10px !important; padding: .8rem 1rem !important; color: var(--danger) !important; font-weight: 600; margin-bottom: 1rem; }
.status-info { background: var(--primary-soft) !important; border: 1px solid var(--primary) !important; border-radius: 10px !important; padding: .8rem 1rem !important; color: var(--primary) !important; font-weight: 600; margin-bottom: 1rem; }
.data-table { border-radius: 10px !important; overflow: hidden; }
.section-head { display: flex; justify-content: space-between; align-items: end; margin: 1.6rem 0 .75rem; }
.section-head h2 { margin: 0 !important; }
.metric-card { background: var(--panel) !important; border: 1px solid var(--line) !important; border-radius: 12px !important; padding: 1rem 1.1rem !important; }
</style>""",
        unsafe_allow_html=True,
    )


def apply_dark_theme() -> None:
    """Optional dark-theme override. Not currently wired but available for future toggle."""
    st.markdown(
        """
<style>
:root { --bg: #0f172a; --panel: #1e293b; --sidebar: #1e293b; --ink: #e2e8f0; --muted: #94a3b8; --line: #334155; --brand: #60a5fa; --brand-dark: #3b82f6; --brand-soft: #1e3a5f; }
html, body, [class*="css"], .stApp, [data-testid="stAppViewContainer"] { background: var(--bg) !important; color: var(--ink) !important; }
[data-testid="stSidebar"] { background: var(--sidebar) !important; }
[data-testid="stMetric"] { background: var(--panel) !important; border-color: var(--line) !important; }
.stButton > button { background: var(--panel) !important; border-color: var(--line) !important; color: var(--ink) !important; }
.stButton > button[kind="primary"] { background: var(--brand) !important; border-color: var(--brand) !important; color: #fff !important; }
</style>""",
        unsafe_allow_html=True,
    )
