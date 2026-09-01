import streamlit as st


def apply_light_theme() -> None:
    st.markdown(
        """
<style>
:root {
  color-scheme: light !important;
  --bg: #f7f9fc;
  --surface: #ffffff;
  --sidebar: #ffffff;
  --text: #152238;
  --muted: #667085;
  --border: #e4e9f1;
  --primary: #3157d5;
  --primary-dark: #2445b5;
  --primary-soft: #eef2ff;
  --success: #16794f;
  --success-soft: #edf9f3;
  --warning: #9a6700;
  --warning-soft: #fff8e6;
  --danger: #c23b3b;
  --danger-soft: #fff1f1;
}
html, body, [class*="css"], .stApp, [data-testid="stAppViewContainer"] {
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: Inter, "Segoe UI", Arial, sans-serif !important;
}
[data-testid="stHeader"] { background: rgba(247,249,252,.92) !important; }
[data-testid="stToolbar"] { color: var(--text) !important; }
[data-testid="stSidebar"] {
  background: var(--sidebar) !important;
  border-right: 1px solid var(--border) !important;
  box-shadow: 6px 0 24px rgba(26,49,92,.035) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }
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
.block-container { max-width: 1380px !important; padding: 2.2rem 2.4rem 4rem !important; }
h1, h2, h3, h4, h5, h6, p, label, span, div { color: var(--text); }
h1 { font-size: 2.05rem !important; letter-spacing: -.035em !important; margin-bottom: .25rem !important; }
h2 { font-size: 1.4rem !important; letter-spacing: -.02em !important; }
h3 { font-size: 1.08rem !important; }
.stCaptionContainer p, [data-testid="stCaptionContainer"] p { color: var(--muted) !important; }
[data-testid="stMetric"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 14px !important;
  padding: 1rem 1.1rem !important;
  box-shadow: 0 4px 16px rgba(31,55,94,.045) !important;
}
[data-testid="stMetricLabel"] p { color: var(--muted) !important; font-size: .82rem !important; font-weight: 650 !important; }
[data-testid="stMetricValue"] { color: var(--text) !important; font-size: 1.55rem !important; }
.stButton > button, .stDownloadButton > button {
  min-height: 2.7rem !important;
  border-radius: 10px !important;
  border: 1px solid var(--border) !important;
  background: var(--surface) !important;
  color: var(--text) !important;
  font-weight: 700 !important;
  box-shadow: 0 2px 6px rgba(31,55,94,.04) !important;
}
.stButton > button[kind="primary"] {
  background: var(--primary) !important;
  border-color: var(--primary) !important;
  color: white !important;
}
.stButton > button[kind="primary"] * { color: white !important; }
.stButton > button[kind="primary"]:hover { background: var(--primary-dark) !important; }
input, textarea, [data-baseweb="select"] > div {
  background: var(--surface) !important;
  color: var(--text) !important;
  border-color: #d7deea !important;
  border-radius: 10px !important;
}
input::placeholder, textarea::placeholder { color: #98a2b3 !important; }
[data-testid="stFileUploaderDropzone"] {
  background: var(--surface) !important;
  border: 1.5px dashed #b9c4d5 !important;
  border-radius: 14px !important;
}
[data-testid="stDataFrame"], [data-testid="stTable"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  overflow: hidden !important;
}
[data-testid="stExpander"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
}
[data-testid="stAlert"] { border-radius: 12px !important; border: 1px solid var(--border) !important; }
[data-testid="stAlert"]:has([data-testid="stNotificationContentInfo"]) { background: #f1f6ff !important; }
[data-testid="stAlert"]:has([data-testid="stNotificationContentWarning"]) { background: var(--warning-soft) !important; }
[data-testid="stAlert"] p { color: var(--text) !important; }
[data-testid="stStatusWidget"] { background: var(--surface) !important; border-color: var(--border) !important; }
hr { border-color: var(--border) !important; }
.app-hero {
  background: linear-gradient(135deg, #ffffff 0%, #f2f5ff 100%);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 1.55rem 1.65rem;
  margin: 0 0 1.25rem;
  box-shadow: 0 8px 30px rgba(35,65,130,.055);
}
.app-kicker { color: var(--primary); font-size: .74rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
.app-hero h1 { margin: .3rem 0 .35rem !important; }
.app-hero p { color: var(--muted) !important; margin: 0; max-width: 760px; }
.section-label { color: var(--muted); font-size: .76rem; font-weight: 750; letter-spacing: .06em; text-transform: uppercase; margin-top: .9rem; }
@media (max-width: 900px) { .block-container { padding: 1.35rem 1rem 3rem !important; } }
</style>
""",
        unsafe_allow_html=True,
    )
