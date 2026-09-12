from __future__ import annotations
import streamlit as st


def apply_dark_theme() -> None:
    """Inject the dark-minimal CSS for Finance Decision Studio."""
    st.markdown(
        """
<style>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap");
@import url("https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css");

:root {
  --bg: #0a0a0a;
  --surface: #141414;
  --surface-2: #1c1c1c;
  --border: #262626;
  --text: #fafafa;
  --text-muted: #737373;
  --accent: #3b82f6;
  --accent-hover: #2563eb;
  --success: #22c55e;
  --danger: #ef4444;
  --warning: #f59e0b;
}

html, body, [class*="css"], .stApp, [data-testid="stAppViewContainer"] {
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: Inter, "Segoe UI", Arial, sans-serif !important;
}

[data-testid="stHeader"] { background: var(--bg) !important; border-bottom: 1px solid var(--border) !important; }

/* Sidebar -- colors only, zero layout overrides */
[data-testid="stSidebar"] {
  background: var(--surface) !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] .stButton > button {
  background: transparent !important;
  border: none !important;
  color: var(--text-muted) !important;
  text-align: left !important;
  border-radius: 8px !important;
  transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background: var(--surface-2) !important;
  color: var(--text) !important;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"],
[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"] {
  background: var(--surface-2) !important;
  color: #ffffff !important;
  border-left: 3px solid var(--accent) !important;
  border-radius: 4px 8px 8px 4px !important;
  font-weight: 600 !important;
}

/* Content area */
.block-container {
  max-width: 1400px !important;
  padding: 0 2rem 4rem !important;
}

/* Headings */
h1 { font-size: 1.5rem !important; font-weight: 600 !important; letter-spacing: -0.02em !important; color: var(--text) !important; }
h2 { font-size: 1.2rem !important; font-weight: 600 !important; color: var(--text) !important; }
h3 { font-size: 1rem !important; font-weight: 600 !important; color: var(--text) !important; }

/* Text */
p, span, label, .stCaptionContainer p, [data-testid="stCaptionContainer"] p, .stMarkdown p {
  color: var(--text) !important;
}

/* Inputs */
.stTextInput input, .stTextArea textarea, .stNumberInput input {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  color: var(--text) !important;
  min-height: 40px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 1px var(--accent) !important;
}
.stTextInput label, .stTextArea label, .stSelectbox label, .stSlider label, .stNumberInput label, .stFileUploader label {
  color: var(--text) !important;
  font-weight: 600 !important;
  font-size: 0.85rem !important;
}

/* Selectbox */
.stSelectbox [data-baseweb="select"] {
  background: var(--surface) !important;
  border-color: var(--border) !important;
  border-radius: 8px !important;
}
.stSelectbox [data-baseweb="select"] span { color: var(--text) !important; }

/* Buttons */
.stButton > button, .stDownloadButton > button {
  min-height: 40px !important;
  border-radius: 8px !important;
  border: 1px solid var(--border) !important;
  background: var(--surface) !important;
  color: var(--text) !important;
  font-weight: 500 !important;
  box-shadow: none !important;
  transition: background 0.15s ease, border-color 0.15s ease !important;
}
.stButton > button:hover {
  background: var(--surface-2) !important;
  border-color: var(--text-muted) !important;
}
.stButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"] {
  background: var(--accent) !important;
  border-color: var(--accent) !important;
  color: #ffffff !important;
}
.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="stBaseButton-primary"]:hover {
  background: var(--accent-hover) !important;
  border-color: var(--accent-hover) !important;
}
button[kind="primaryFormSubmit"] {
  background: var(--accent) !important;
  border-color: var(--accent) !important;
  color: #ffffff !important;
}
button[kind="primaryFormSubmit"]:hover {
  background: var(--accent-hover) !important;
  border-color: var(--accent-hover) !important;
}

/* Forms */
[data-testid="stForm"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  padding: 1.5rem !important;
}

/* Metrics */
[data-testid="stMetric"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  padding: 1rem !important;
}
[data-testid="stMetricLabel"] p {
  color: var(--text-muted) !important;
  font-size: 0.75rem !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
  font-weight: 600 !important;
}
[data-testid="stMetricValue"] {
  color: var(--text) !important;
  font-size: 1.5rem !important;
  font-weight: 600 !important;
}

/* DataFrames and tables */
[data-testid="stDataFrame"], [data-testid="stTable"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  overflow: hidden !important;
}

/* Expanders */
[data-testid="stExpander"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
}

/* Alerts */
div[data-testid="stAlert"] {
  background: var(--surface) !important;
  border-radius: 8px !important;
  border: none !important;
  border-left: 4px solid var(--border) !important;
  padding: 0.75rem 1rem !important;
}
div[data-testid="stAlert"] p { color: var(--text) !important; }
div[data-testid="stAlert"]:has([data-testid="stAlertContentError"]) { border-left-color: var(--danger) !important; }
div[data-testid="stAlert"]:has([data-testid="stAlertContentError"]) p { color: var(--danger) !important; }
div[data-testid="stAlert"]:has([data-testid="stAlertContentSuccess"]) { border-left-color: var(--success) !important; }
div[data-testid="stAlert"]:has([data-testid="stAlertContentSuccess"]) p { color: var(--success) !important; }
div[data-testid="stAlert"]:has([data-testid="stAlertContentWarning"]) { border-left-color: var(--warning) !important; }
div[data-testid="stAlert"]:has([data-testid="stAlertContentWarning"]) p { color: var(--warning) !important; }
div[data-testid="stAlert"]:has([data-testid="stAlertContentInfo"]) { border-left-color: var(--accent) !important; }

/* Status widget */
[data-testid="stStatusWidget"] {
  background: var(--surface) !important;
  border-color: var(--border) !important;
}

/* Progress bar */
[data-testid="stProgress"] > div > div > div {
  background: var(--accent) !important;
}

/* File uploader */
[data-testid="stFileUploaderDropzone"] {
  background: var(--surface) !important;
  border: 1px dashed var(--border) !important;
  border-radius: 8px !important;
}
[data-testid="stFileUploaderDropzone"] button {
  background: var(--surface-2) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
}

/* Dividers */
hr { border-color: var(--border) !important; }

/* Slider */
.stSlider [data-baseweb="slider"] { background: var(--border) !important; }
.stSlider [data-baseweb="thumb"] { background: var(--accent) !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
  background: var(--surface) !important;
  border-color: var(--border) !important;
}
.stTabs [data-baseweb="tab"] { color: var(--text-muted) !important; border-color: transparent !important; }
.stTabs [aria-selected="true"] { color: var(--text) !important; border-color: var(--accent) !important; }

/* Expander toggle */
[data-testid="stExpander"] summary { color: var(--text) !important; }

/* Remove Streamlit branding */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header[data-testid="stHeader"] {
  background: var(--bg) !important;
}

/* Status banners used by status_banner() */
.status-success { background: var(--surface); border-left: 4px solid var(--success); color: var(--success); border-radius: 8px; padding: 0.75rem 1rem; margin: 0.5rem 0; }
.status-warning { background: var(--surface); border-left: 4px solid var(--warning); color: var(--warning); border-radius: 8px; padding: 0.75rem 1rem; margin: 0.5rem 0; }
.status-error   { background: var(--surface); border-left: 4px solid var(--danger);  color: var(--danger);  border-radius: 8px; padding: 0.75rem 1rem; margin: 0.5rem 0; }
.status-info    { background: var(--surface); border-left: 4px solid var(--accent);  color: var(--accent);  border-radius: 8px; padding: 0.75rem 1rem; margin: 0.5rem 0; }

/* Custom utility classes */
.page-header { margin-bottom: 1.5rem; }
.page-header h1 { margin-bottom: 0.3rem !important; }
.page-header .lead { color: var(--text-muted) !important; font-size: 0.95rem !important; max-width: 720px; margin-top: 0.3rem !important; }

.section-head { display: flex; justify-content: space-between; align-items: end; margin: 1.5rem 0 0.75rem; }
.section-head h2 { margin: 0 !important; }
.section-head small { color: var(--text-muted) !important; }

.login-panel { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 3rem; text-align: center; }

.sidebar-logo { padding: 1rem 1rem 0.5rem; margin-bottom: 0.5rem; }
.sidebar-logo i { font-size: 1.5rem; color: var(--accent); }
.sidebar-logo p { font-size: 0.8rem; font-weight: 600; color: var(--text-muted); letter-spacing: 0.04em; text-transform: uppercase; margin-top: 0.3rem; }

.sidebar-divider { border-top: 1px solid var(--border); margin: 0.5rem 1rem; }

@media (max-width: 900px) {
  .block-container { padding: 0 1rem 2rem; }
}
</style>
""",
        unsafe_allow_html=True,
    )
    st.markdown(_EXTRA_NAV_CSS, unsafe_allow_html=True)


def apply_light_theme() -> None:
    """Backward-compatible alias — calls dark theme."""
    apply_dark_theme()

# --- Sidebar / navigation UX ------------------------------------------------
# Keep Streamlit responsible for layout; only style the navigation hierarchy.
_EXTRA_NAV_CSS = """
<style>
[data-testid="stSidebar"] > div:first-child {
  padding-top: 1rem !important;
}
[data-testid="stSidebar"] .block-container {
  padding: 0.75rem 0.9rem 1rem !important;
}
.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  padding: 0.25rem 0.35rem 1rem;
}
.sidebar-brand-mark {
  width: 34px;
  height: 34px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent);
  color: #fff;
  font-weight: 800;
  font-size: 0.95rem;
}
.sidebar-brand-name {
  color: var(--text) !important;
  font-size: 0.92rem;
  font-weight: 700;
  line-height: 1.1;
}
.sidebar-brand-subtitle {
  color: var(--text-muted) !important;
  font-size: 0.65rem;
  margin-top: 0.18rem;
  line-height: 1.2;
}
.sidebar-workspace {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.7rem 0.75rem;
  margin: 0.15rem 0 1rem;
}
.sidebar-workspace strong,
.sidebar-workspace span {
  display: block;
}
.sidebar-workspace strong {
  color: var(--text) !important;
  font-size: 0.8rem;
  margin: 0.12rem 0;
}
.sidebar-workspace span:last-child {
  color: var(--text-muted) !important;
  font-size: 0.72rem;
}
.sidebar-workspace-label,
.sidebar-section-label {
  color: var(--text-muted) !important;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-weight: 700;
  font-size: 0.62rem;
}
.sidebar-section-label {
  padding: 0.55rem 0.35rem 0.35rem;
}
[data-testid="stSidebar"] .stButton {
  margin-bottom: 0.14rem !important;
}
[data-testid="stSidebar"] .stButton > button {
  min-height: 38px !important;
  padding: 0.45rem 0.7rem !important;
  font-size: 0.82rem !important;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"],
[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"] {
  box-shadow: inset 3px 0 0 var(--accent) !important;
}
.sidebar-footer-divider {
  border-top: 1px solid var(--border);
  margin: 1rem 0 0.8rem;
}
.sidebar-user {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0 0.25rem 0.55rem;
}
.sidebar-user strong,
.sidebar-user span {
  display: block;
}
.sidebar-user strong {
  color: var(--text) !important;
  font-size: 0.76rem;
}
.sidebar-user span {
  color: var(--text-muted) !important;
  font-size: 0.67rem;
  margin-top: 0.1rem;
}
.sidebar-avatar,
.header-avatar {
  border-radius: 50%;
  background: var(--accent);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}
.sidebar-avatar {
  width: 30px;
  height: 30px;
  font-size: 0.72rem;
}
.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-height: 56px;
  padding: 0 0 0.9rem;
  margin-bottom: 1.45rem;
  border-bottom: 1px solid var(--border);
}
.app-breadcrumb {
  color: var(--text-muted) !important;
  font-size: 0.68rem;
  font-weight: 600;
  margin-bottom: 0.12rem;
}
.app-header h1 {
  margin: 0 !important;
  font-size: 1.18rem !important;
}
.header-user {
  display: flex;
  align-items: center;
  gap: 0.55rem;
}
.header-user-copy strong,
.header-user-copy span {
  display: block;
}
.header-user-copy strong {
  color: var(--text) !important;
  font-size: 0.75rem;
}
.header-user-copy span {
  color: var(--text-muted) !important;
  font-size: 0.65rem;
  margin-top: 0.08rem;
}
.header-avatar {
  width: 32px;
  height: 32px;
  font-size: 0.76rem;
}
@media (max-width: 760px) {
  .header-user-copy { display: none; }
  .app-breadcrumb { display: none; }
}
</style>
"""
