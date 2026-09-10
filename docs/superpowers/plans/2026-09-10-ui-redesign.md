# UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the light-themed monolith with a dark minimal UI, icon sidebar, split login, and per-page file structure.

**Architecture:** Streamlit stays as the framework. `app.py` becomes an ~80-line router. Each page lives in `src/ui/pages/` with a single `render()` function. A dark CSS theme replaces the current light theme. Bootstrap Icons replace emojis in navigation.

**Tech Stack:** Streamlit >=1.39, Bootstrap Icons CDN, Python 3.14, existing backend services unchanged.

## Global Constraints

- Streamlit >=1.39 (from requirements.txt)
- Bootstrap Icons 1.11.3 via CDN
- No new Python dependencies
- No changes to `src/services/`, `src/agents/`, `src/config.py`
- CSS: no gradients, no shadows, no box-shadow — only 1px borders
- Border-radius: 8px everywhere
- Font: Inter (already used)

---

## Task 1: Dark Minimal Theme

**Files:**
- Modify: `.streamlit/config.toml`
- Rewrite: `src/ui/theme.py`

**Interfaces:**
- Produces: `apply_dark_theme()` function (called by app.py)

- [ ] **Step 1: Update Streamlit config to dark mode**

Replace `.streamlit/config.toml` entirely:

```toml
[theme]
base = "dark"
primaryColor = "#3b82f6"
backgroundColor = "#0a0a0a"
secondaryBackgroundColor = "#141414"
textColor = "#fafafa"
font = "sans serif"

[browser]
gatherUsageStats = false

[server]
headless = true
maxUploadSize = 200
```

- [ ] **Step 2: Rewrite theme.py with dark minimal CSS**

Replace `src/ui/theme.py` entirely:

```python
from __future__ import annotations
import streamlit as st


def apply_dark_theme() -> None:
    """Inject the dark-minimal CSS for Finance Decision Studio."""
    st.markdown(
        """
<style>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap");

/* Bootstrap Icons */
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

/* Alerts — muted left border style */
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
[data-testid="stHorizontalBlock"] hr { border-color: var(--border) !important; }

/* Slider */
.stSlider [data-baseweb="slider"] {
  background: var(--border) !important;
}
.stSlider [data-baseweb="thumb"] {
  background: var(--accent) !important;
}

/* Checkbox */
.stCheckbox label span { color: var(--text) !important; }

/* Radio */
.stRadio label span { color: var(--text) !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
  background: var(--surface) !important;
  border-color: var(--border) !important;
}
.stTabs [data-baseweb="tab"] {
  color: var(--text-muted) !important;
  border-color: transparent !important;
}
.stTabs [aria-selected="true"] {
  color: var(--text) !important;
  border-color: var(--accent) !important;
}

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
```

- [ ] **Step 3: Verify theme loads**

Run: `.venv/Scripts/streamlit run src/ui/app.py --server.headless true --server.port 8502`
Expected: App loads with dark background, no errors in terminal. (The login page will look broken — that's expected, we fix it in Task 3.)

- [ ] **Step 4: Commit**

```bash
git add .streamlit/config.toml src/ui/theme.py
git commit -m "feat: dark minimal theme with Bootstrap Icons CDN"
```

---

## Task 2: Sidebar Component

**Files:**
- Create: `src/ui/components/sidebar.py`

**Interfaces:**
- Consumes: `st.session_state["current_page"]` (string key)
- Produces: `render_sidebar() -> str` returns selected page key

- [ ] **Step 1: Create sidebar.py**

```python
from __future__ import annotations
import streamlit as st

PAGES = [
    ("dashboard", "bi-speedometer2", "Dashboard"),
    ("credit", "bi-graph-up-arrow", "Credit risk"),
    ("demand", "bi-graph-down-arrow", "Demand"),
    ("training", "bi-tools", "Training"),
    ("policies", "bi-journal-text", "Policies"),
    ("history", "bi-clock-history", "History"),
    ("help", "bi-question-circle", "Help"),
]

PAGE_TITLES = {key: label for key, _, label in PAGES}


def render_sidebar() -> str:
    """Render the icon sidebar and header bar. Returns the selected page key."""
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "dashboard"

    current = st.session_state["current_page"]

    with st.sidebar:
        # Logo area
        st.markdown(
            '<div class="sidebar-logo">'
            '<i class="bi bi-graph-up-arrow"></i>'
            '<p>FDS</p>'
            '</div>',
            unsafe_allow_html=True,
        )

        # Navigation buttons
        for key, icon, label in PAGES:
            is_active = key == current
            btn_label = f'<i class="bi {icon}"></i>  {label}'
            if st.button(
                btn_label,
                key=f"nav_{key}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state["current_page"] = key
                st.rerun()

        # Divider at bottom
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

        # Sign out
        from src.services.auth import current_user
        user = current_user() or "admin"
        st.caption(f"Signed in as {user}")
        if st.button("Sign out", key="sidebar_signout", use_container_width=True):
            from src.services.auth import sign_out
            sign_out()
            st.rerun()

    # Header bar
    title = PAGE_TITLES.get(current, "Finance Decision Studio")
    from src.services.auth import current_user
    user = current_user() or "admin"
    initial = user[0].upper()

    st.markdown(
        f"""
        <div style="display:flex; justify-content:space-between; align-items:center;
                    padding:0.6rem 0 1rem; border-bottom:1px solid var(--border); margin-bottom:1.5rem;">
            <h1 style="margin:0; font-size:1.4rem;">{title}</h1>
            <div style="display:flex; align-items:center; gap:0.75rem;">
                <div style="width:32px; height:32px; border-radius:50%; background:var(--accent);
                            color:#fff; display:flex; align-items:center; justify-content:center;
                            font-size:0.85rem; font-weight:600;">{initial}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    return current
```

- [ ] **Step 2: Verify sidebar renders**

Run the app. The sidebar should show 7 icon+label buttons. Clicking one should highlight it and change the header title. The header should show the page title and a user avatar circle.

- [ ] **Step 3: Commit**

```bash
git add src/ui/components/sidebar.py
git commit -m "feat: icon sidebar with Bootstrap Icons and header bar"
```

---

## Task 3: Login Page

**Files:**
- Create: `src/ui/login.py`

**Interfaces:**
- Consumes: `sign_in()`, `credentials_configured()`, `is_authenticated()` from `src/services/auth.py`
- Produces: `render_login()` function (called by app.py gate)

- [ ] **Step 1: Create login.py**

```python
from __future__ import annotations
import streamlit as st
from src.services.auth import credentials_configured, sign_in


def render_login() -> None:
    """Render the split-panel login page."""
    # Full-viewport dark background with centered split card
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] > .main {
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            min-height: 100vh !important;
            padding: 2rem !important;
        }
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="stHeader"] { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if not credentials_configured():
        st.error("Administrator credentials are missing. Add ADMIN_USERNAME and ADMIN_PASSWORD to the project .env file, then restart the app.")
        st.stop()

    # Center the login card
    left_spacer, center, right_spacer = st.columns([1, 1.6, 1])
    with center:
        # Split panel: left branding + right form
        panel_left, panel_right = st.columns([2, 3])

        with panel_left:
            st.markdown(
                """
                <div class="login-panel">
                    <i class="bi bi-graph-up-arrow" style="font-size:2rem; color:var(--accent); margin-bottom:1rem;"></i>
                    <h2 style="font-size:1.1rem; font-weight:600; color:var(--text); margin-bottom:0.5rem;">Finance Decision Studio</h2>
                    <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:0.3rem;">Governed credit risk and demand analysis</p>
                    <p style="font-size:0.8rem; color:var(--text-muted);">Built for teams that need human oversight.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with panel_right:
            st.markdown("<div style='padding: 1rem 0;'><h2 style='font-size:1.2rem; font-weight:600; color:var(--text);'>Welcome back</h2></div>", unsafe_allow_html=True)

            with st.form("login_form", clear_on_submit=False):
                username = st.text_input("Email or username", placeholder="admin@example.com", autocomplete="username")
                password = st.text_input("Password", type="password", autocomplete="current-password")
                submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)

            if submitted:
                if not username.strip() or not password:
                    st.error("Enter both your username and password.")
                else:
                    try:
                        auth_ok = sign_in(username, password)
                    except Exception as exc:
                        st.error(f"Login error: {exc}")
                    else:
                        if auth_ok:
                            st.rerun()
                        else:
                            st.error("The username or password is incorrect. Check your .env settings and try again.")

            st.caption("Session expires automatically after inactivity.")
```

- [ ] **Step 2: Verify login renders**

Run the app. You should see:
- Centered split card on dark background
- Left panel: icon + app name + tagline
- Right panel: "Welcome back" heading, username/password inputs, blue Sign in button
- Sidebar and header are hidden
- Entering wrong credentials shows red error text below the button
- Entering `admin` / `change-this-password` signs in and shows the main app

- [ ] **Step 3: Commit**

```bash
git add src/ui/login.py
git commit -m "feat: split-panel login page with dark theme"
```

---

## Task 4: Page Scaffolding

**Files:**
- Create: `src/ui/pages/__init__.py`
- Create: `src/ui/pages/dashboard.py`
- Create: `src/ui/pages/credit.py`
- Create: `src/ui/pages/demand.py`
- Create: `src/ui/pages/training.py`
- Create: `src/ui/pages/policies.py`
- Create: `src/ui/pages/history.py`
- Create: `src/ui/pages/help.py`

**Interfaces:**
- Each page exports: `render(registry, recommender, profiles, company) -> None`

- [ ] **Step 1: Create pages/__init__.py**

```python
from __future__ import annotations
from src.ui.pages import dashboard, credit, demand, training, policies, history, help

PAGE_MAP = {
    "dashboard": dashboard,
    "credit": credit,
    "demand": demand,
    "training": training,
    "policies": policies,
    "history": history,
    "help": help,
}
```

- [ ] **Step 2: Create dashboard.py**

```python
from __future__ import annotations
import streamlit as st
from src.ui.components.display import metric_cards


def render(registry, recommender, profiles, company) -> None:
    """Render the dashboard page."""
    st.markdown(
        '<div class="page-header"><h1>Dashboard</h1>'
        '<p class="lead">Build governed models, review operational signals, and translate model output into accountable decisions.</p></div>',
        unsafe_allow_html=True,
    )

    def active(task):
        try:
            return registry.load_latest(company, task)[1]
        except Exception:
            return None

    credit_model = active("credit")
    forecast_model = active("forecast")

    metric_cards(
        {"platform": "Centralized", "credit_model": "Ready" if credit_model else "Not trained", "demand_model": "Ready" if forecast_model else "Not trained", "approval": "Required"},
        ["platform", "credit_model", "demand_model", "approval"],
    )

    st.markdown('<div class="section-head"><h2>Model readiness</h2><small>Admin-owned platform metrics</small></div>', unsafe_allow_html=True)

    left, right = st.columns(2)
    with left:
        st.markdown("#### Credit")
        st.caption("Portfolio risk model")
        if credit_model:
            metric_cards(credit_model.get("metrics", {}), ["ROC_AUC", "F1_Score", "Recall"])
            st.caption(f"Active version: {credit_model.get('version', 'Unknown')}")
        else:
            st.info("No active credit model. Use Training to create one.")
    with right:
        st.markdown("#### Demand")
        st.caption("Historical signal model")
        if forecast_model:
            metric_cards(forecast_model.get("metrics", {}), ["MAE", "WAPE", "R2"])
            st.caption(f"Active version: {forecast_model.get('version', 'Unknown')}")
        else:
            st.info("No active demand model. Use Training to create one.")
```

- [ ] **Step 3: Create credit.py (stub)**

```python
from __future__ import annotations
import streamlit as st


def render(registry, recommender, profiles, company) -> None:
    """Render the analyze credit risk page."""
    st.markdown(
        '<div class="page-header"><h1>Credit risk</h1>'
        '<p class="lead">Upload current customer records. The active saved model runs without retraining.</p></div>',
        unsafe_allow_html=True,
    )
    st.info("Credit risk analysis — full implementation coming in Task 7.")
```

- [ ] **Step 4: Create demand.py (stub)**

```python
from __future__ import annotations
import streamlit as st


def render(registry, recommender, profiles, company) -> None:
    """Render the analyze demand page."""
    st.markdown(
        '<div class="page-header"><h1>Demand analysis</h1>'
        '<p class="lead">Evaluate completed historical periods and identify unusual movement or inventory exposure.</p></div>',
        unsafe_allow_html=True,
    )
    st.info("Demand analysis — full implementation coming in Task 8.")
```

- [ ] **Step 5: Create training.py (stub)**

```python
from __future__ import annotations
import streamlit as st


def render(registry, recommender, profiles, company) -> None:
    """Render the training page."""
    st.markdown(
        '<div class="page-header"><h1>Training</h1>'
        '<p class="lead">Validate data, train on one partition, evaluate on untouched records, and save a version.</p></div>',
        unsafe_allow_html=True,
    )
    st.info("Model training — full implementation coming in Task 9.")
```

- [ ] **Step 6: Create policies.py (stub)**

```python
from __future__ import annotations
import streamlit as st


def render(registry, recommender, profiles, company) -> None:
    """Render the company policies page."""
    st.markdown(
        '<div class="page-header"><h1>Company rules</h1>'
        '<p class="lead">Personalize recommendations without changing model predictions.</p></div>',
        unsafe_allow_html=True,
    )
    st.info("Company policies — full implementation coming in Task 10.")
```

- [ ] **Step 7: Create history.py (stub)**

```python
from __future__ import annotations
import streamlit as st


def render(registry, recommender, profiles, company) -> None:
    """Render the model history page."""
    st.markdown(
        '<div class="page-header"><h1>Model versions</h1>'
        '<p class="lead">Inspect saved versions and choose the active model for each workflow.</p></div>',
        unsafe_allow_html=True,
    )
    st.info("Model history — full implementation coming in Task 11.")
```

- [ ] **Step 8: Create help.py (stub)**

```python
from __future__ import annotations
import streamlit as st


def render(registry, recommender, profiles, company) -> None:
    """Render the help page."""
    st.markdown(
        '<div class="page-header"><h1>About</h1>'
        '<p class="lead">A concise guide to the system boundaries and operating model.</p></div>',
        unsafe_allow_html=True,
    )
    st.markdown("""1. Choose a company workspace.
2. Train with validated historical data.
3. Review holdout metrics before operational use.
4. Analyze current records without retraining.
5. Require human review for consequential recommendations.
6. Use Model versions to inspect or reactivate prior models.""")
```

- [ ] **Step 9: Verify all pages show stubs**

Run the app, sign in, click each sidebar button. Each page should show its header and a blue info stub message.

- [ ] **Step 10: Commit**

```bash
git add src/ui/pages/
git commit -m "feat: page scaffolding with stubs for all 7 pages"
```

---

## Task 5: Refactor app.py to Router

**Files:**
- Rewrite: `src/ui/app.py`

**Interfaces:**
- Consumes: `render_login()` from `login.py`, `render_sidebar()` from `sidebar.py`, `PAGE_MAP` from `pages/__init__.py`
- Consumes: `apply_dark_theme()` from `theme.py`
- Consumes: `is_authenticated()`, `sign_out()`, `current_user()` from `auth.py`

- [ ] **Step 1: Rewrite app.py**

Replace `src/ui/app.py` entirely:

```python
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
from src.ui.theme import apply_dark_theme
from src.ui.login import render_login
from src.ui.components.sidebar import render_sidebar
from src.ui.pages import PAGE_MAP
from src.services.auth import is_authenticated
from src.services.model_registry import ModelRegistry
from src.agents.recommender import RecommendationEngine
from src.services.company_profile import CompanyProfileStore

st.set_page_config(
    page_title="Finance Decision Studio",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_dark_theme()

# ── Session gate ────────────────────────────────────────────────────────────
if not is_authenticated():
    render_login()
    st.stop()

# ── Sidebar + header ────────────────────────────────────────────────────────
selected_page = render_sidebar()

# ── Clear stale results ─────────────────────────────────────────────────────
keys_to_remove = [
    k for k in st.session_state.keys()
    if k.startswith(("credit_result_", "forecast_result_", "credit_training_", "augmentation_"))
]
for k in keys_to_remove:
    del st.session_state[k]

# ── Shared instances ────────────────────────────────────────────────────────
registry = ModelRegistry()
recommender = RecommendationEngine()
profiles = CompanyProfileStore()
company = "admin_company"
registry.company_dir(company, create=True)
profiles.save(profiles.load(company))

# ── Route to page ───────────────────────────────────────────────────────────
PAGE_MAP[selected_page].render(registry, recommender, profiles, company)
```

- [ ] **Step 2: Verify full flow**

Run the app. Expected flow:
1. Login page appears (split panel, dark theme)
2. Sign in with `admin` / `change-this-password`
3. Dashboard loads with dark theme, icon sidebar, header bar
4. Clicking sidebar buttons navigates between stub pages
5. Session state persists across navigation

- [ ] **Step 3: Commit**

```bash
git add src/ui/app.py
git commit -m "feat: refactor app.py to router with dark theme and sidebar"
```

---

## Task 6: Migrate Credit Analysis Page

**Files:**
- Rewrite: `src/ui/pages/credit.py`

**Interfaces:**
- Consumes: `registry`, `recommender`, `company` from render args
- Consumes: `csv_uploader`, `field_mapping` from `components/fields.py`
- Consumes: `metric_cards` from `components/display.py`
- Produces: credit risk analysis flow (upload → map → analyze → results)

- [ ] **Step 1: Rewrite credit.py with full implementation**

```python
from __future__ import annotations
import pandas as pd
import streamlit as st
from src.services.schema import available_credit_fields, apply_mapping, validate_credit, CREDIT_ID, quality_report
from src.ui.components.fields import csv_uploader, field_mapping
from src.ui.components.display import metric_cards


def render(registry, recommender, profiles, company) -> None:
    """Render the analyze credit risk page."""
    st.markdown(
        '<div class="page-header"><h1>Credit risk</h1>'
        '<p class="lead">Upload current customer records. The active saved model runs without retraining.</p></div>',
        unsafe_allow_html=True,
    )

    df = csv_uploader("Customer credit data", "credit_predict")
    if df is None:
        return

    # Data summary
    q = quality_report(df)
    metric_cards(q, ["rows", "columns", "duplicate_rows", "missing_cells"])
    with st.expander("Preview uploaded data"):
        st.dataframe(df.head(25), use_container_width=True, hide_index=True)
        st.caption(f"Missing data: {q['missing_percent']:.2f}%")

    # Field mapping
    fields = available_credit_fields(df.columns, False)
    mp, errs = field_mapping(df, fields, "cp_v4")
    mapped = apply_mapping(df, mp)
    validation = validate_credit(mapped, False)
    for e in validation:
        st.error(e)

    if st.button("Analyze portfolio", type="primary", disabled=bool(errs or validation)):
        try:
            with st.status("Running portfolio analysis…", expanded=True) as status:
                model, _ = registry.load_latest(company, "credit")
                p, tiers = model.predict_risk(mapped)
                explanations = model.explain(mapped)
                identifiers = mapped[CREDIT_ID].astype(str) if CREDIT_ID in mapped.columns else mapped.index.astype(str)
                result = pd.DataFrame({CREDIT_ID: identifiers, "risk_score": p, "risk_tier": tiers})
                result["key_indicators"] = [
                    " • ".join(f"{i['feature']}: {i['relative_position']}" for i in x.get("unusual_indicators", []))
                    for x in explanations
                ]
                result["recommended_actions"] = [
                    " • ".join(recommender.credit(x)["recommended_actions"]) for x in explanations
                ]
                st.session_state[f"credit_result_{company}"] = result
                status.update(label="Analysis complete", state="complete")
        except Exception as e:
            st.exception(f"Portfolio analysis failed: {e}")

    result = st.session_state.get(f"credit_result_{company}")
    if result is not None:
        metric_cards(
            {"customers": len(result), "low": int((result.risk_tier == "LOW_RISK").sum()), "medium": int((result.risk_tier == "MEDIUM_RISK").sum()), "high": int((result.risk_tier == "HIGH_RISK").sum())},
            ["customers", "low", "medium", "high"],
        )
        chart, table = st.columns([1, 2])
        chart.bar_chart(result.risk_tier.value_counts(), height=300)
        table.dataframe(
            result, use_container_width=True, hide_index=True,
            column_config={"risk_score": st.column_config.ProgressColumn("Risk score", min_value=0, max_value=1, format="%.0%%")},
        )
        st.download_button("Download portfolio report", result.to_csv(index=False).encode(), "credit_portfolio.csv", "text/csv")
```

- [ ] **Step 2: Verify credit page**

Run the app, navigate to Credit risk. Upload a CSV. Verify: data summary shows, field mapping works, analyze button runs, results display with chart and table.

- [ ] **Step 3: Commit**

```bash
git add src/ui/pages/credit.py
git commit -m "feat: migrate credit risk analysis page"
```

---

## Task 7: Migrate Demand Analysis Page

**Files:**
- Rewrite: `src/ui/pages/demand.py`

- [ ] **Step 1: Rewrite demand.py**

```python
from __future__ import annotations
import pandas as pd
import streamlit as st
from src.services.schema import FORECAST_FIELDS, apply_mapping, validate_forecast, quality_report
from src.ui.components.fields import csv_uploader, field_mapping
from src.ui.components.display import metric_cards


def render(registry, recommender, profiles, company) -> None:
    """Render the analyze demand page."""
    st.markdown(
        '<div class="page-header"><h1>Demand analysis</h1>'
        '<p class="lead">Evaluate completed historical periods and identify unusual movement or inventory exposure.</p></div>',
        unsafe_allow_html=True,
    )
    st.info("This is historical evaluation, not a future multi-step forecast.")

    df = csv_uploader("Historical demand data", "forecast_eval")
    if df is None:
        return

    # Data summary
    q = quality_report(df)
    metric_cards(q, ["rows", "columns", "duplicate_rows", "missing_cells"])
    with st.expander("Preview uploaded data"):
        st.dataframe(df.head(25), use_container_width=True, hide_index=True)
        st.caption(f"Missing data: {q['missing_percent']:.2f}%")

    # Field mapping
    mp, errs = field_mapping(df, FORECAST_FIELDS, "fe")
    mapped = apply_mapping(df, mp)
    validation = validate_forecast(mapped, True)
    for e in validation:
        st.error(e)

    if st.button("Evaluate signals", type="primary", disabled=bool(errs or validation)):
        try:
            with st.status("Evaluating demand signals…", expanded=True) as status:
                model, _ = registry.load_latest(company, "forecast")
                featured = model.create_features(mapped)
                met = model.evaluate_featured(featured)
                result = model.detect_anomalies(mapped)
                result["recommended_actions"] = [" • ".join(recommender.forecast(row)) for _, row in result.iterrows()]
                st.session_state[f"forecast_result_{company}"] = (met, result)
                status.update(label="Evaluation complete", state="complete")
        except Exception as e:
            st.exception(f"Demand evaluation failed: {e}")

    saved = st.session_state.get(f"forecast_result_{company}")
    if saved:
        met, result = saved
        metric_cards(met, ["MAE", "RMSE", "WAPE", "R2"])
        st.line_chart(result.groupby("date")[["units_sold", "forecast_units_sold"]].sum(), height=320)
        alerts = result[(result.is_anomaly == 1) | (result.is_stockout_risk == 1)]
        metric_cards({"anomalies": int(result.is_anomaly.sum()), "stockout_risks": int(result.is_stockout_risk.sum())}, ["anomalies", "stockout_risks"])
        st.dataframe(alerts, use_container_width=True, hide_index=True)
        st.download_button("Download demand report", result.to_csv(index=False).encode(), "demand_analysis.csv", "text/csv")
```

- [ ] **Step 2: Verify demand page**

Navigate to Demand. Upload CSV. Verify mapping, evaluation, charts, alerts table all work.

- [ ] **Step 3: Commit**

```bash
git add src/ui/pages/demand.py
git commit -m "feat: migrate demand analysis page"
```

---

## Task 8: Migrate Training Page

**Files:**
- Rewrite: `src/ui/pages/training.py`

This is the largest page. Implementation is the full training logic from the original `app.py` lines 252-479, moved into the `render()` function.

- [ ] **Step 1: Rewrite training.py**

Copy the full training page logic from the original `app.py` (lines 252-479) into `src/ui/pages/training.py`. The function signature is `render(registry, recommender, profiles, company)`. All imports go at the top. The body is identical to the original, just inside the `render()` function.

Key imports needed at top of file:

```python
from __future__ import annotations
import pandas as pd
import streamlit as st
from src.services.schema import available_credit_fields, apply_mapping, validate_credit, validate_forecast, FORECAST_FIELDS, quality_report
from src.services.training import train_credit, train_forecast, compare_credit_augmentation, train_all_credit, train_all_forecast, train_credit_with_optimal_threshold, grid_search_credit, grid_search_forecast
from src.agents.credit_agent import AVAILABLE_CREDIT_MODELS
from src.agents.forecast_agent import AVAILABLE_FORECAST_MODELS
from src.ui.components.fields import csv_uploader, field_mapping
from src.ui.components.display import metric_cards
```

The `render()` function contains the full training logic (radio for Credit/Demand, CSV upload, field mapping, model selection, hyperparameters, training, augmentation, grid search). Copy verbatim from the original app.py lines 254-479, replacing the old helper calls (`load_csv(...)`) with direct `csv_uploader(...)` calls and `cards(...)` with `metric_cards(...)`.

- [ ] **Step 2: Verify training page**

Navigate to Training. Test: upload credit CSV, select model, train. Verify metrics display. Test "train all models" path. Test forecast training path.

- [ ] **Step 3: Commit**

```bash
git add src/ui/pages/training.py
git commit -m "feat: migrate training page with all model options"
```

---

## Task 9: Migrate Policies, History, Help Pages

**Files:**
- Rewrite: `src/ui/pages/policies.py`
- Rewrite: `src/ui/pages/history.py`
- Rewrite: `src/ui/pages/help.py`

- [ ] **Step 1: Rewrite policies.py**

```python
from __future__ import annotations
import streamlit as st


def render(registry, recommender, profiles, company) -> None:
    """Render the company policies page."""
    st.markdown(
        '<div class="page-header"><h1>Company rules</h1>'
        '<p class="lead">Personalize recommendations without changing model predictions.</p></div>',
        unsafe_allow_html=True,
    )

    profile = profiles.load(company)
    with st.form("company_policy"):
        st.markdown("### Workspace identity")
        left, right = st.columns(2)
        display = left.text_input("Company display name", profile.display_name, placeholder="Example: North Region Finance")
        currency = right.text_input("Currency", profile.currency)
        language = left.selectbox("Preferred language", ["English", "French", "Arabic"], index=["English", "French", "Arabic"].index(profile.language) if profile.language in ["English", "French", "Arabic"] else 0)
        human = right.checkbox("Require human approval", profile.require_human_approval)
        st.markdown("### Recommendation controls")
        rules = st.text_area("Mandatory rules", "\n".join(profile.recommendation_rules), height=115, placeholder="One rule per line")
        blocked = st.text_area("Forbidden action keywords", "\n".join(profile.forbidden_actions), height=115, placeholder="One phrase per line")
        submitted = st.form_submit_button("Save company rules", type="primary")
    if submitted:
        profile.display_name = display.strip()
        profile.currency = currency.strip() or "TND"
        profile.language = language
        profile.require_human_approval = human
        profile.recommendation_rules = [x.strip() for x in rules.splitlines() if x.strip()]
        profile.forbidden_actions = [x.strip() for x in blocked.splitlines() if x.strip()]
        profiles.save(profile)
        st.success("Company rules saved.")
```

- [ ] **Step 2: Rewrite history.py**

```python
from __future__ import annotations
import pandas as pd
import streamlit as st


def render(registry, recommender, profiles, company) -> None:
    """Render the model history page."""
    st.markdown(
        '<div class="page-header"><h1>Model versions</h1>'
        '<p class="lead">Inspect saved versions and choose the active model for each workflow.</p></div>',
        unsafe_allow_html=True,
    )

    for task in ["credit", "forecast"]:
        st.markdown(f"### {task.title()}")
        versions = registry.versions(company, task)
        if not versions:
            st.info("No saved versions.")
            continue
        rows = [
            {"version": v["version"], "saved_at": v["saved_at_utc"], **{k: value for k, value in v.get("metrics", {}).items() if isinstance(value, (int, float, str))}}
            for v in versions
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        chosen = st.selectbox("Activate version", [v["version"] for v in versions], key=f"version_{task}")
        if st.button("Set active", key=f"activate_{task}"):
            registry.activate(company, task, chosen)
            st.success("Active model updated.")
```

- [ ] **Step 3: Rewrite help.py**

```python
from __future__ import annotations
import streamlit as st


def render(registry, recommender, profiles, company) -> None:
    """Render the help page."""
    st.markdown(
        '<div class="page-header"><h1>About</h1>'
        '<p class="lead">A concise guide to the system boundaries and operating model.</p></div>',
        unsafe_allow_html=True,
    )
    st.markdown("""1. Choose a company workspace.
2. Train with validated historical data.
3. Review holdout metrics before operational use.
4. Analyze current records without retraining.
5. Require human review for consequential recommendations.
6. Use Model versions to inspect or reactivate prior models.""")
```

- [ ] **Step 4: Verify all three pages**

Navigate to Policies: form renders, save works.
Navigate to History: tables show, version activation works.
Navigate to Help: numbered list displays.

- [ ] **Step 5: Commit**

```bash
git add src/ui/pages/policies.py src/ui/pages/history.py src/ui/pages/help.py
git commit -m "feat: migrate policies, history, and help pages"
```

---

## Task 10: Delete Old Code and Final Cleanup

**Files:**
- Delete: `src/ui/components/layout.py`
- Modify: `src/ui/components/__init__.py`
- Verify: `app.py` under 100 lines

- [ ] **Step 1: Update components/__init__.py**

Remove layout imports (layout.py is being deleted). Keep fields and display imports:

```python
from __future__ import annotations
"""Reusable Streamlit UI components for Finance Decision Studio."""

from src.ui.components.fields import (
    csv_uploader,
    field_mapping,
    model_select,
    slider_pair,
    checkbox_group,
)
from src.ui.components.display import (
    result_metrics,
    result_table,
    result_chart,
    download_button,
    metric_cards,
)

__all__ = [
    "csv_uploader", "field_mapping", "model_select", "slider_pair",
    "checkbox_group", "result_metrics", "result_table", "result_chart",
    "download_button", "metric_cards",
]
```

- [ ] **Step 2: Add metric_cards to display.py**

The `metric_cards` function was in `layout.py`. Move it to `display.py` since pages import it from there:

Add to the end of `src/ui/components/display.py`:

```python
def metric_cards(values: dict, labels: list[str]) -> None:
    """Render a row of metric cards from a dict and ordered label list."""
    cols = st.columns(len(labels))
    for col, name in zip(cols, labels):
        val = values.get(name, "—")
        if isinstance(val, float):
            val = f"{val:.3f}" if abs(val) < 10 else f"{val:.2f}"
        col.metric(name.replace("_", " "), val)
```

Also add `import streamlit as st` at the top of display.py if not already there.

- [ ] **Step 3: Delete layout.py**

```bash
rm src/ui/components/layout.py
```

- [ ] **Step 4: Verify everything works**

Run the app. Sign in. Navigate through ALL 7 pages. Verify no import errors, no missing functions, all pages render correctly.

- [ ] **Step 5: Count app.py lines**

```bash
wc -l src/ui/app.py
```

Expected: under 100 lines.

- [ ] **Step 6: Commit**

```bash
git add -A src/ui/
git commit -m "feat: delete old layout.py, move metric_cards to display.py, final cleanup"
```

---

## Task 11: Full Integration Test

- [ ] **Step 1: Start fresh — clear session**

Close all browser tabs for the app. Kill any running Streamlit processes.

- [ ] **Step 2: Launch and test login**

Run: `.venv/Scripts/streamlit run src/ui/app.py --server.headless true --server.port 8502`

Verify:
- Dark background, no light flash
- Split-panel login (left branding, right form)
- Wrong credentials → error message
- Correct credentials (`admin` / `change-this-password`) → redirects to dashboard

- [ ] **Step 3: Test sidebar navigation**

Click each of the 7 sidebar buttons. Verify:
- Active button highlighted
- Header title changes
- Page content loads (no stub messages — all full implementations)

- [ ] **Step 4: Test each page**

- **Dashboard**: metric cards show, model status displays
- **Credit risk**: upload CSV, field mapping works, analyze produces results
- **Demand**: upload CSV, evaluation produces charts and alerts
- **Training**: upload CSV, train a model, metrics display
- **Policies**: form saves, success message shows
- **History**: version tables display
- **Help**: numbered list shows

- [ ] **Step 5: Test sign out**

Click user avatar area (or add a sign-out mechanism if not yet wired). Verify session clears, login page reappears.

- [ ] **Step 6: Final commit**

```bash
git add -A
git commit -m "feat: complete UI redesign — dark theme, icon sidebar, page refactor"
```
