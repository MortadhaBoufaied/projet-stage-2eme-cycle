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
[data-testid="stToolbar"] { display: none !important; }

/* Sidebar */
[data-testid="stSidebar"] {
  background: var(--surface) !important;
  border-right: 1px solid var(--border) !important;
  width: 240px !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }
[data-testid="stSidebar"] [data-testid="stSidebarNav"] { padding-top: 0 !important; }
[data-testid="stSidebar"] .stButton > button {
  background: transparent !important;
  border: none !important;
  color: var(--text-muted) !important;
  text-align: left !important;
  padding: 0.5rem 1rem !important;
  border-radius: 8px !important;
  width: 100% !important;
  height: 40px !important;
  display: flex !important;
  align-items: center !important;
  gap: 0.6rem !important;
  font-size: 0.9rem !important;
  font-weight: 500 !important;
  transition: background 0.15s ease, color 0.15s ease !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background: var(--surface-2) !important;
  color: var(--text) !important;
}
[data-testid="stSidebar"] .stButton > button:focus {
  box-shadow: none !important;
  outline: none !important;
}

/* Sidebar expand/collapse chevron button -- covers all Streamlit versions */
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapsedControl"],
button[title="Open sidebar"],
button[title="Close sidebar"] {
  background: var(--surface-2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  color: var(--text) !important;
  width: 28px !important;
  height: 28px !important;
  padding: 0 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  position: relative !important;
  z-index: 999 !important;
  cursor: pointer !important;
  opacity: 1 !important;
  visibility: visible !important;
}
[data-testid="stSidebarCollapseButton"] svg,
[data-testid="stSidebarCollapsedControl"] svg,
button[title="Open sidebar"] svg,
button[title="Close sidebar"] svg {
  fill: var(--text) !important;
  width: 14px !important;
  height: 14px !important;
}
[data-testid="stSidebarCollapseButton"]:hover,
[data-testid="stSidebarCollapsedControl"]:hover,
button[title="Open sidebar"]:hover,
button[title="Close sidebar"]:hover {
  background: var(--accent) !important;
  border-color: var(--accent) !important;
}
[data-testid="stSidebarCollapseButton"]:hover svg,
[data-testid="stSidebarCollapsedControl"]:hover svg,
button[title="Open sidebar"]:hover svg,
button[title="Close sidebar"]:hover svg {
  fill: #fff !important;
}

/* Ensure the collapsed sidebar control container is visible and clickable */
[data-testid="stSidebarCollapsedControl"] {
  display: block !important;
  width: auto !important;
  height: auto !important;
  overflow: visible !important;
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
header[data-testid="stHeader"] { background: var(--bg) !important; }

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


def apply_light_theme() -> None:
    """Backward-compatible alias — calls dark theme."""
    apply_dark_theme()
