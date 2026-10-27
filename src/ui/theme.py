import streamlit as st


def get_shared_css(is_dark: bool) -> str:
    deploy_and_header_hider = """
/* Hide Streamlit Deploy button, top decoration, and options menu */
.stDeployButton,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
#MainMenu,
header [data-testid="stToolbar"],
header button[kind="header"],
.stApp header,
.stApp header > div,
.stApp header > div > div,
.stApp header button,
.stApp .stButton[kind="header"],
.stApp .stToolbar,
.stApp .stDeployButton {{
  display: none !important;
  visibility: hidden !important;
  opacity: 0 !important;
  height: 0 !important;
  width: 0 !important;
  pointer-events: none !important;
  position: absolute !important;
  left: -9999px !important;
}}

[data-testid="stHeader"] {{
  background: transparent !important;
  height: 0 !important;
  padding: 0 !important;
  margin: 0 !important;
  display: none !important;
}}

/* Force hide all header elements */
header {{
  display: none !important;
  height: 0 !important;
  padding: 0 !important;
  margin: 0 !important;
}}
"""
    if not is_dark:
        # Light Theme
        return f"""
<style>
{{deploy_and_header_hider}}

:root {{
  color-scheme: light !important;
  --bg: #f7f9fc;
  --surface: #ffffff;
  --surface-hover: #f8fafc;
  --sidebar: #ffffff;
  --text: #152238;
  --text-strong: #0a1120;
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
  --card-shadow: 0 4px 16px rgba(31,55,94,.045);
  --hero-bg: linear-gradient(135deg, #ffffff 0%, #f4f7fc 100%);
  --hero-shadow: 0 8px 30px rgba(35,65,130,.055);
  --ai-box-bg: linear-gradient(135deg, #ffffff 0%, #f0f4ff 100%);
  --active-model-bg: linear-gradient(135deg, #ffffff 0%, #f0fdf4 100%);
  --active-model-border: #bbf7d0;
  --input-border: #d7deea;
}}

html, body, [class*="css"], .stApp, [data-testid="stAppViewContainer"] {{
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif !important;
}}

[data-testid="stSidebar"] {{
  background: var(--sidebar) !important;
  border-right: 1px solid var(--border) !important;
  box-shadow: 6px 0 24px rgba(26,49,92,.035) !important;
}}
[data-testid="stSidebar"] * {{ color: var(--text) !important; }}
[data-testid="stSidebar"] .stCaptionContainer p {{ color: var(--muted) !important; }}
[data-testid="stSidebar"] [role="radiogroup"] label {{
  padding: .55rem .8rem !important;
  border-radius: 10px !important;
  transition: all .15s ease !important;
  margin-bottom: 2px !important;
}}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {{
  background: #f1f5fa !important;
}}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{
  background: var(--primary-soft) !important;
  color: var(--primary) !important;
  font-weight: 700 !important;
  box-shadow: inset 3px 0 0 var(--primary) !important;
}}

.block-container {{ max-width: 1420px !important; padding: 1.5rem 2.4rem 4rem !important; }}
h1, h2, h3, h4, h5, h6, p, label, span, div {{ color: var(--text); }}
h1 {{ font-size: 2.05rem !important; letter-spacing: -.035em !important; margin-bottom: .25rem !important; font-weight: 750 !important; }}
h2 {{ font-size: 1.38rem !important; letter-spacing: -.02em !important; font-weight: 700 !important; }}
h3 {{ font-size: 1.08rem !important; font-weight: 650 !important; }}
.stCaptionContainer p, [data-testid="stCaptionContainer"] p {{ color: var(--muted) !important; }}

[data-testid="stMetric"] {{
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 14px !important;
  padding: 1.05rem 1.2rem !important;
  box-shadow: var(--card-shadow) !important;
  transition: transform .15s ease, box-shadow .15s ease !important;
}}
[data-testid="stMetric"]:hover {{
  box-shadow: 0 6px 20px rgba(31,55,94,.08) !important;
}}
[data-testid="stMetricLabel"] p {{ color: var(--muted) !important; font-size: .82rem !important; font-weight: 650 !important; text-transform: uppercase !important; letter-spacing: 0.04em !important; }}
[data-testid="stMetricValue"] {{ color: var(--text) !important; font-size: 1.6rem !important; font-weight: 800 !important; }}

.stButton > button, .stDownloadButton > button {{
  min-height: 2.65rem !important;
  border-radius: 10px !important;
  border: 1px solid var(--border) !important;
  background: var(--surface) !important;
  color: var(--text) !important;
  font-weight: 650 !important;
  box-shadow: 0 2px 6px rgba(31,55,94,.04) !important;
  transition: all .15s ease-in-out !important;
}}
.stButton > button:hover, .stDownloadButton > button:hover {{
  border-color: #cbd5e1 !important;
  box-shadow: 0 4px 12px rgba(31,55,94,.08) !important;
  transform: translateY(-1px) !important;
}}
.stButton > button[kind="primary"],
[data-testid="stFormSubmitButton"] > button,
[data-testid="stFormSubmitButton"] button,
button[kind="primary"],
button[data-testid*="primary"] {{
  background: var(--primary) !important;
  background-color: var(--primary) !important;
  border-color: var(--primary) !important;
  color: #ffffff !important;
  box-shadow: 0 4px 14px rgba(49,87,213,.25) !important;
}}
.stButton > button[kind="primary"] *,
[data-testid="stFormSubmitButton"] > button *,
[data-testid="stFormSubmitButton"] button *,
button[kind="primary"] *,
button[data-testid*="primary"] * {{
  color: #ffffff !important;
  fill: #ffffff !important;
}}
.stButton > button[kind="primary"]:hover,
[data-testid="stFormSubmitButton"] > button:hover,
button[kind="primary"]:hover {{
  background: var(--primary-dark) !important;
  background-color: var(--primary-dark) !important;
  border-color: var(--primary-dark) !important;
  color: #ffffff !important;
  box-shadow: 0 6px 18px rgba(49,87,213,.35) !important;
}}

[data-baseweb="input"],
[data-baseweb="base-input"],
[data-testid="stTextInput"] > div > div,
[data-testid="stNumberInput"] > div > div,
[data-testid="stTextArea"] > div > div,
input, textarea, [data-baseweb="select"] > div {{
  background: var(--surface) !important;
  color: var(--text) !important;
  border: 1px solid #d1d5db !important;
  border-color: #d1d5db !important;
  border-radius: 10px !important;
}}
[data-baseweb="input"]:focus-within,
[data-baseweb="base-input"]:focus-within,
[data-testid="stTextInput"] > div > div:focus-within,
input:focus, textarea:focus, [data-baseweb="select"] > div:focus-within {{
  border-color: var(--primary) !important;
  box-shadow: 0 0 0 3px rgba(49,87,213,.15) !important;
}}
[data-baseweb="input"] button,
[data-baseweb="base-input"] button,
[data-testid="stTextInput"] button {{
  background: transparent !important;
  background-color: transparent !important;
  border: none !important;
  box-shadow: none !important;
  color: var(--muted) !important;
}}
input::placeholder, textarea::placeholder {{ color: #98a2b3 !important; }}

[data-testid="stFileUploaderDropzone"] {{
  background: var(--surface) !important;
  border: 1.5px dashed #b9c4d5 !important;
  border-radius: 14px !important;
  transition: border-color .15s ease, background-color .15s ease !important;
}}
[data-testid="stFileUploaderDropzone"]:hover {{
  border-color: var(--primary) !important;
  background-color: var(--primary-soft) !important;
}}

[data-testid="stDataFrame"], [data-testid="stTable"] {{
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  overflow: hidden !important;
  box-shadow: 0 2px 10px rgba(31,55,94,.03) !important;
}}

[data-testid="stExpander"] {{
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  box-shadow: 0 2px 8px rgba(31,55,94,.03) !important;
}}

[data-testid="stAlert"] {{ border-radius: 12px !important; border: 1px solid var(--border) !important; }}
[data-testid="stAlert"]:has([data-testid="stNotificationContentInfo"]) {{ background: #f1f6ff !important; border-left: 4px solid var(--primary) !important; }}
[data-testid="stAlert"]:has([data-testid="stNotificationContentWarning"]) {{ background: var(--warning-soft) !important; border-left: 4px solid var(--warning) !important; }}
[data-testid="stAlert"]:has([data-testid="stNotificationContentError"]) {{ background: var(--danger-soft) !important; border-left: 4px solid var(--danger) !important; }}
[data-testid="stAlert"]:has([data-testid="stNotificationContentSuccess"]) {{ background: var(--success-soft) !important; border-left: 4px solid var(--success) !important; }}
[data-testid="stAlert"] p {{ color: var(--text) !important; }}
hr {{ border-color: var(--border) !important; }}

/* Custom Design Components */
.app-hero, .hero {{
  background: var(--hero-bg);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 1.6rem 1.8rem;
  margin: 0 0 1.35rem;
  box-shadow: var(--hero-shadow);
}}
.app-kicker, .k {{ color: var(--primary); font-size: .75rem; font-weight: 800; letter-spacing: .09em; text-transform: uppercase; }}
.app-hero h1, .hero h1 {{ margin: .3rem 0 .35rem !important; }}
.app-hero p, .hero p {{ color: var(--muted) !important; margin: 0; max-width: 780px; font-size: 0.96rem; line-height: 1.5; }}

.badge {{
  display: inline-flex;
  align-items: center;
  font-size: 0.72rem;
  font-weight: 750;
  padding: 0.25rem 0.65rem;
  border-radius: 9999px;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}}
.badge-primary {{ background: var(--primary-soft); color: var(--primary); border: 1px solid rgba(49,87,213,.2); }}
.badge-success {{ background: var(--success-soft); color: var(--success); border: 1px solid rgba(22,121,79,.2); }}
.badge-warning {{ background: var(--warning-soft); color: var(--warning); border: 1px solid rgba(154,103,0,.2); }}
.badge-danger {{ background: var(--danger-soft); color: var(--danger); border: 1px solid rgba(194,59,59,.2); }}
.badge-neutral {{ background: #f1f5f9; color: var(--muted); border: 1px solid var(--border); }}

.ai-box {{
  background: var(--ai-box-bg);
  border: 1px solid #d0ddf7;
  border-left: 4px solid var(--primary);
  border-radius: 12px;
  padding: 1.2rem 1.35rem;
  margin: 0.75rem 0 1rem;
  box-shadow: 0 4px 18px rgba(49,87,213,.04);
}}

.rec-card {{
  display: flex;
  align-items: flex-start;
  gap: 0.85rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.75rem 1rem;
  margin-bottom: 0.5rem;
  box-shadow: 0 2px 6px rgba(15,23,42,.03);
}}
.rec-number {{
  background: var(--primary-soft);
  color: var(--primary);
  font-weight: 800;
  font-size: 0.78rem;
  min-width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}}

.active-model-card {{
  background: var(--active-model-bg);
  border: 1px solid var(--active-model-border);
  border-radius: 14px;
  padding: 1.25rem 1.4rem;
  margin: 0.5rem 0 1rem;
  box-shadow: 0 4px 16px rgba(22,121,79,.05);
}}



.user-chip {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 0.75rem 0.9rem;
  margin-bottom: 1rem;
  box-shadow: 0 2px 8px rgba(15,23,42,.04);
}}

.good {{ color: var(--success); font-weight: 700; }}
.warn {{ color: var(--warning); font-weight: 700; }}
.bad {{ color: var(--danger); font-weight: 700; }}
.section-label {{ color: var(--muted); font-size: .76rem; font-weight: 750; letter-spacing: .06em; text-transform: uppercase; margin-top: .9rem; }}

@media (max-width: 900px) {{ .block-container {{ padding: 1.35rem 1rem 3rem !important; }} }}
</style>
"""
    else:
        # Dark Theme
        return f"""
<style>
{{deploy_and_header_hider}}

:root {{
  color-scheme: dark !important;
  --bg: #0b0f19;
  --surface: #131b2e;
  --surface-hover: #1b263e;
  --sidebar: #0f172a;
  --text: #e2e8f0;
  --text-strong: #ffffff;
  --muted: #94a3b8;
  --border: #23314d;
  --primary: #4f78fe;
  --primary-dark: #3b63e2;
  --primary-soft: rgba(79, 120, 254, 0.16);
  --success: #10b981;
  --success-soft: rgba(16, 185, 129, 0.16);
  --warning: #f59e0b;
  --warning-soft: rgba(245, 158, 11, 0.16);
  --danger: #ef4444;
  --danger-soft: rgba(239, 68, 68, 0.16);
  --card-shadow: 0 4px 20px rgba(0,0,0,.35);
  --hero-bg: linear-gradient(135deg, #131b2e 0%, #0d1424 100%);
  --hero-shadow: 0 8px 32px rgba(0,0,0,.45);
  --ai-box-bg: linear-gradient(135deg, #141e34 0%, #0f172a 100%);
  --active-model-bg: linear-gradient(135deg, #112726 0%, #0d1e21 100%);
  --active-model-border: #134e4a;
  --input-border: #2c3e60;
}}

html, body, [class*="css"], .stApp, [data-testid="stAppViewContainer"] {{
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif !important;
}}

[data-testid="stSidebar"] {{
  background: var(--sidebar) !important;
  border-right: 1px solid var(--border) !important;
  box-shadow: 6px 0 24px rgba(0,0,0,.35) !important;
}}
[data-testid="stSidebar"] * {{ color: var(--text) !important; }}
[data-testid="stSidebar"] .stCaptionContainer p {{ color: var(--muted) !important; }}
[data-testid="stSidebar"] [role="radiogroup"] label {{
  padding: .55rem .8rem !important;
  border-radius: 10px !important;
  transition: all .15s ease !important;
  margin-bottom: 2px !important;
}}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {{
  background: #17243c !important;
}}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{
  background: var(--primary-soft) !important;
  color: var(--primary) !important;
  font-weight: 700 !important;
  box-shadow: inset 3px 0 0 var(--primary) !important;
}}

.block-container {{ max-width: 1420px !important; padding: 1.5rem 2.4rem 4rem !important; }}
h1, h2, h3, h4, h5, h6, p, label, span, div {{ color: var(--text); }}
h1 {{ font-size: 2.05rem !important; letter-spacing: -.035em !important; margin-bottom: .25rem !important; font-weight: 750 !important; color: var(--text-strong) !important; }}
h2 {{ font-size: 1.38rem !important; letter-spacing: -.02em !important; font-weight: 700 !important; color: var(--text-strong) !important; }}
h3 {{ font-size: 1.08rem !important; font-weight: 650 !important; color: var(--text-strong) !important; }}
.stCaptionContainer p, [data-testid="stCaptionContainer"] p {{ color: var(--muted) !important; }}

[data-testid="stMetric"] {{
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 14px !important;
  padding: 1.05rem 1.2rem !important;
  box-shadow: var(--card-shadow) !important;
  transition: transform .15s ease, box-shadow .15s ease !important;
}}
[data-testid="stMetric"]:hover {{
  box-shadow: 0 6px 24px rgba(0,0,0,.5) !important;
  border-color: #384c73 !important;
}}
[data-testid="stMetricLabel"] p {{ color: var(--muted) !important; font-size: .82rem !important; font-weight: 650 !important; text-transform: uppercase !important; letter-spacing: 0.04em !important; }}
[data-testid="stMetricValue"] {{ color: var(--text-strong) !important; font-size: 1.6rem !important; font-weight: 800 !important; }}

.stButton > button, .stDownloadButton > button {{
  min-height: 2.65rem !important;
  border-radius: 10px !important;
  border: 1px solid var(--border) !important;
  background: var(--surface) !important;
  color: var(--text) !important;
  font-weight: 650 !important;
  box-shadow: 0 2px 8px rgba(0,0,0,.25) !important;
  transition: all .15s ease-in-out !important;
}}
.stButton > button:hover, .stDownloadButton > button:hover {{
  border-color: #435b88 !important;
  background: var(--surface-hover) !important;
  box-shadow: 0 4px 14px rgba(0,0,0,.4) !important;
  transform: translateY(-1px) !important;
}}
.stButton > button[kind="primary"],
[data-testid="stFormSubmitButton"] > button,
[data-testid="stFormSubmitButton"] button,
button[kind="primary"],
button[data-testid*="primary"] {{
  background: var(--primary) !important;
  background-color: var(--primary) !important;
  border-color: var(--primary) !important;
  color: #ffffff !important;
  box-shadow: 0 4px 16px rgba(79, 120, 254, 0.4) !important;
}}
.stButton > button[kind="primary"] *,
[data-testid="stFormSubmitButton"] > button *,
[data-testid="stFormSubmitButton"] button *,
button[kind="primary"] *,
button[data-testid*="primary"] * {{
  color: #ffffff !important;
  fill: #ffffff !important;
}}
.stButton > button[kind="primary"]:hover,
[data-testid="stFormSubmitButton"] > button:hover,
button[kind="primary"]:hover {{
  background: var(--primary-dark) !important;
  background-color: var(--primary-dark) !important;
  border-color: var(--primary-dark) !important;
  color: #ffffff !important;
  box-shadow: 0 6px 20px rgba(79, 120, 254, 0.5) !important;
}}

[data-baseweb="input"],
[data-baseweb="base-input"],
[data-testid="stTextInput"] > div > div,
[data-testid="stNumberInput"] > div > div,
[data-testid="stTextArea"] > div > div,
input, textarea, [data-baseweb="select"] > div {{
  background: #0f1629 !important;
  color: var(--text-strong) !important;
  border: 1px solid #334155 !important;
  border-color: #334155 !important;
  border-radius: 10px !important;
}}
[data-baseweb="input"]:focus-within,
[data-baseweb="base-input"]:focus-within,
[data-testid="stTextInput"] > div > div:focus-within,
input:focus, textarea:focus, [data-baseweb="select"] > div:focus-within {{
  border-color: var(--primary) !important;
  box-shadow: 0 0 0 3px rgba(79, 120, 254, 0.25) !important;
}}
[data-baseweb="input"] button,
[data-baseweb="base-input"] button,
[data-testid="stTextInput"] button {{
  background: transparent !important;
  background-color: transparent !important;
  border: none !important;
  box-shadow: none !important;
  color: var(--muted) !important;
}}
input::placeholder, textarea::placeholder {{ color: #64748b !important; }}

[data-testid="stFileUploaderDropzone"] {{
  background: var(--surface) !important;
  border: 1.5px dashed #334466 !important;
  border-radius: 14px !important;
  transition: border-color .15s ease, background-color .15s ease !important;
}}
[data-testid="stFileUploaderDropzone"]:hover {{
  border-color: var(--primary) !important;
  background-color: var(--primary-soft) !important;
}}

[data-testid="stDataFrame"], [data-testid="stTable"] {{
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  overflow: hidden !important;
  box-shadow: 0 2px 12px rgba(0,0,0,.3) !important;
}}

[data-testid="stExpander"] {{
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  box-shadow: 0 2px 10px rgba(0,0,0,.25) !important;
}}

[data-testid="stAlert"] {{ border-radius: 12px !important; border: 1px solid var(--border) !important; }}
[data-testid="stAlert"]:has([data-testid="stNotificationContentInfo"]) {{ background: rgba(79, 120, 254, 0.12) !important; border-left: 4px solid var(--primary) !important; }}
[data-testid="stAlert"]:has([data-testid="stNotificationContentWarning"]) {{ background: var(--warning-soft) !important; border-left: 4px solid var(--warning) !important; }}
[data-testid="stAlert"]:has([data-testid="stNotificationContentError"]) {{ background: var(--danger-soft) !important; border-left: 4px solid var(--danger) !important; }}
[data-testid="stAlert"]:has([data-testid="stNotificationContentSuccess"]) {{ background: var(--success-soft) !important; border-left: 4px solid var(--success) !important; }}
[data-testid="stAlert"] p {{ color: var(--text) !important; }}
hr {{ border-color: var(--border) !important; }}

/* Custom Design Components - Dark */
.app-hero, .hero {{
  background: var(--hero-bg);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 1.6rem 1.8rem;
  margin: 0 0 1.35rem;
  box-shadow: var(--hero-shadow);
}}
.app-kicker, .k {{ color: var(--primary); font-size: .75rem; font-weight: 800; letter-spacing: .09em; text-transform: uppercase; }}
.app-hero h1, .hero h1 {{ margin: .3rem 0 .35rem !important; color: var(--text-strong) !important; }}
.app-hero p, .hero p {{ color: var(--muted) !important; margin: 0; max-width: 780px; font-size: 0.96rem; line-height: 1.5; }}

.badge {{
  display: inline-flex;
  align-items: center;
  font-size: 0.72rem;
  font-weight: 750;
  padding: 0.25rem 0.65rem;
  border-radius: 9999px;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}}
.badge-primary {{ background: var(--primary-soft); color: #82a0ff; border: 1px solid rgba(79, 120, 254, 0.35); }}
.badge-success {{ background: var(--success-soft); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.35); }}
.badge-warning {{ background: var(--warning-soft); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.35); }}
.badge-danger {{ background: var(--danger-soft); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.35); }}
.badge-neutral {{ background: #1e293b; color: var(--muted); border: 1px solid var(--border); }}

.ai-box {{
  background: var(--ai-box-bg);
  border: 1px solid #233554;
  border-left: 4px solid var(--primary);
  border-radius: 12px;
  padding: 1.2rem 1.35rem;
  margin: 0.75rem 0 1rem;
  box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}}

.rec-card {{
  display: flex;
  align-items: flex-start;
  gap: 0.85rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.75rem 1rem;
  margin-bottom: 0.5rem;
  box-shadow: 0 2px 6px rgba(0,0,0,.2);
}}
.rec-number {{
  background: var(--primary-soft);
  color: var(--primary);
  font-weight: 800;
  font-size: 0.78rem;
  min-width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}}

.active-model-card {{
  background: var(--active-model-bg);
  border: 1px solid var(--active-model-border);
  border-radius: 14px;
  padding: 1.25rem 1.4rem;
  margin: 0.5rem 0 1rem;
  box-shadow: 0 4px 18px rgba(0,0,0,.3);
}}



.user-chip {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 0.75rem 0.9rem;
  margin-bottom: 1rem;
  box-shadow: 0 2px 10px rgba(0,0,0,.3);
}}

.good {{ color: #34d399; font-weight: 700; }}
.warn {{ color: #fbbf24; font-weight: 700; }}
.bad {{ color: #f87171; font-weight: 700; }}
.section-label {{ color: var(--muted); font-size: .76rem; font-weight: 750; letter-spacing: .06em; text-transform: uppercase; margin-top: .9rem; }}

@media (max-width: 900px) {{ .block-container {{ padding: 1.35rem 1rem 3rem !important; }} }}
</style>
"""


def apply_light_theme() -> None:
    st.markdown(get_shared_css(is_dark=False), unsafe_allow_html=True)


def apply_dark_theme() -> None:
    st.markdown(get_shared_css(is_dark=True), unsafe_allow_html=True)


def apply_theme(is_dark: bool = False) -> None:
    st.markdown(get_shared_css(is_dark=is_dark), unsafe_allow_html=True)
