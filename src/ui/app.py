import io,os,json,hashlib,urllib.request
from pathlib import Path
import pandas as pd, numpy as np, streamlit as st
from src.config import MAX_UPLOAD_MB
from src.services.auth import verify,signup,create_session,validate_session,destroy_session
from src.services.schemas import template,documentation,normalize,CREDIT_FIELDS,FORECAST_FIELDS
from src.services.validation import validate
from src.services.model_contract import validate_for_model, template_for_model
from src.services.tabular_io import read_uploaded_table, read_tabular_bytes
from src.services.client_history_input import empty_editor_frame, prepare_history_assessment, RECORD_TYPE, HISTORY, CURRENT
from src.services.modeling import train_credit,train_forecast,forecast_features
from src.services.registry import Registry

reg = Registry()
from src.services.intelligence import interpret, recommend_model
from src.services.metrics import regression,classification
from src.services.financial_forecast_runtime import future_projection, forecast_alerts, financial_mode
from src.services.workspace import Workspace

from src.agents.credit_agent import CreditRiskAgent
from src.agents.forecast_agent import CashflowForecastAgent
from src.ui.theme import apply_theme, apply_light_theme, apply_dark_theme
from src.services.flexible_schema import analyze_dataframe, validate_flexible, auto_clean_dataset, enhance_schema_with_slm, enhance_schema_with_slm_forecast, clear_schema_cache, save_template, get_current_template, update_template_on_schema_change, save_schema_version, get_schema_versions, get_latest_schema_version, compare_schemas, suggest_schema_improvements, check_schema_migration_required

st.set_page_config(page_title='ML Intelligence Center',page_icon='◆',layout='wide')

# Hide Streamlit navbar/toolbar completely
hide_navbar_css = """
<style>
/* Hide all Streamlit navbar elements */
.stApp header, 
.stApp header > div,
.stApp header > div > div,
.stApp header button,
.stApp .stToolbar,
.stApp .stDeployButton,
.stApp #MainMenu,
.stApp .stDecoration,
.stApp .stStatusWidget {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    height: 0 !important;
    width: 0 !important;
    pointer-events: none !important;
    position: absolute !important;
    left: -9999px !important;
}

/* Hide header completely */
header {
    display: none !important;
    height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
}

/* Remove header spacing */
[data-testid="stHeader"] {
    display: none !important;
    height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
}

/* Hide deploy button specifically */
.stDeployButton {
    display: none !important;
}

/* Hide hamburger menu */
#MainMenu {
    display: none !important;
}

/* Remove white bar above content - target root elements */
.stApp,
.stApp > div,
.stApp > div > div,
.stApp .main,
.stApp .block-container {
    padding-top: 0 !important;
    margin-top: 0 !important;
}

/* Allow normal scrolling for content pages */
html, body {
    height: auto !important;
    min-height: 100vh !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow-y: auto !important;
}

.stApp {
    height: auto !important;
    min-height: 100vh !important;
    display: block !important;
    overflow-y: auto !important;
}

.stApp .main {
    flex: none !important;
    display: block !important;
    justify-content: flex-start !important;
    align-items: flex-start !important;
    padding: 0 !important;
    min-height: auto !important;
    overflow-y: auto !important;
}

.stApp .main .block-container {
    width: 100% !important;
    max-width: 1420px !important;
    padding: 1.5rem 2.4rem 4rem !important;
    overflow-y: auto !important;
}

/* Remove any top decoration or white bars */
[data-testid="stDecoration"],
.stDecoration,
.stApp .stDecoration {
    display: none !important;
    height: 0 !important;
    width: 0 !important;
}



/* Hide any white background bars at the top */
.stApp header,
.stApp .stHeader,
.stApp [data-testid="stHeader"] {
    background: transparent !important;
    display: none !important;
    height: 0 !important;
}

/* Remove login-container styling */
.login-container {
    display: none !important;
}

/* Ensure dataframes and containers can scroll */
/* Enable scrolling for all main content containers */
[style="min-height: 200px"] {
    overflow-y: auto !important;
}

/* Fix scroll on status containers */
.stStatusWidget {
    overflow-y: auto !important;
}

/* Remove any white bars from tabs */
[data-testid="stTabs"],
.stTabs {
    background: transparent !important;
    border: none !important;
}

/* Remove any padding from tabs container */
[data-testid="stTabs"] > div {
    padding: 0 !important;
    margin: 0 !important;
}

/* Fix selectbox/dropdown visibility for both light and dark modes */
.stSelectbox, [data-testid="stSelectbox"] {
    color: var(--text) !important;
}

/* Fix selectbox dropdown options - force readable colors in both themes */
div[data-baseweb="popover"] > div > div {
    background-color: #ffffff !important;
    color: #000000 !important;
}

div[data-baseweb="popover"] div[data-baseweb="element-container"] {
    background-color: #ffffff !important;
    color: #000000 !important;
}

/* Fix selectbox dropdown items */
div[data-baseweb="popover"] div[role="option"] {
    background-color: #ffffff !important;
    color: #000000 !important;
}

div[data-baseweb="popover"] div[role="option"]:hover {
    background-color: #f0f0f0 !important;
    color: #000000 !important;
}

/* Fix all dropdown/option elements with readable colors */
div[data-baseweb="popover"] div div {
    background-color: #ffffff !important;
    color: #000000 !important;
}

div[data-baseweb="popover"] div div:hover {
    background-color: #f0f0f0 !important;
    color: #000000 !important;
}

/* Fix selectbox container */
[data-testid="stSelectbox"] > div {
    color: var(--text) !important;
}

/* Fix multiselect visibility */
.stMultiSelect, [data-testid="stMultiSelect"] {
    color: var(--text) !important;
}

/* Fix multiselect dropdown with readable colors */
div[data-baseweb="multiselect"] div div {
    color: #000000 !important;
    background-color: #ffffff !important;
}

/* Force all option elements to be readable */
[role="option"] {
    background-color: #ffffff !important;
    color: #000000 !important;
}

[role="option"]:hover {
    background-color: #f0f0f0 !important;
    color: #000000 !important;
}


/* Training schema selectors are chip-only: remove a chip to transfer it. */
.st-key-credit_schema_feature_columns input, .st-key-credit_schema_id_columns input,
.st-key-forecast_schema_feature_columns input, .st-key-forecast_schema_id_columns input {display:none !important;}
.st-key-credit_schema_feature_columns [data-baseweb="select"] > div > div:last-child,
.st-key-credit_schema_id_columns [data-baseweb="select"] > div > div:last-child,
.st-key-forecast_schema_feature_columns [data-baseweb="select"] > div > div:last-child,
.st-key-forecast_schema_id_columns [data-baseweb="select"] > div > div:last-child {display:none !important;}

.stTextInput input,.stNumberInput input{color:var(--text)!important;-webkit-text-fill-color:var(--text)!important;background:var(--surface)!important}.stTextInput label,.stNumberInput label{color:var(--text)!important;opacity:1!important}
/* Theme toggle button styling */
#theme-toggle-header-btn {
    position: fixed !important;
    top: 20px !important;
    right: 20px !important;
    z-index: 999999999 !important;
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    font-size: 1.8rem !important;
    line-height: 1 !important;
    padding: 8px !important;
    margin: 0 !important;
    cursor: pointer !important;
    width: auto !important;
    height: auto !important;
    min-height: unset !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: transform 0.2s ease, opacity 0.2s ease !important;
    color: inherit !important;
    user-select: none !important;
}

#theme-toggle-header-btn:hover {
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    transform: scale(1.1) !important;
    opacity: 0.8 !important;
}

#theme-toggle-header-btn:active {
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    transform: scale(0.95) !important;
}

#theme-toggle-header-btn {
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
}

/* Prevent compact risk labels from wrapping while preserving readable spacing. */
.stCheckbox label p { white-space: nowrap !important; }

/* Theme toggle button styling - circular with border, no background */
.st-key-native_theme_toggle button {
    min-width: 2.5rem !important;
    min-height: 2.5rem !important;
    padding: 0 !important;
    border-radius: 50% !important;
    border: 2px solid var(--border) !important;
    background: transparent !important;
    font-size: 1.2rem !important;
    margin: 0 0 0.5rem 0 !important;
}
.st-key-native_theme_toggle button:hover {
    border-color: var(--primary) !important;
    background: transparent !important;
}
/* Remove container spacing around theme toggle */
.st-key-native_theme_toggle > div {
    margin: 0 !important;
    padding: 0 !important;
}
/* Hide sidebar close/collapse button */

"""
st.markdown(hide_navbar_css, unsafe_allow_html=True)

# ── Theme State with LocalStorage & URL Persistence ──────────────────
theme_param = st.query_params.get('theme')
if theme_param in ('dark', 'light'):
    st.session_state.dark_mode = (theme_param == 'dark')
elif 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

apply_theme(is_dark=st.session_state.dark_mode)

# JavaScript bridge to sync localStorage with Streamlit
session_token_value = st.session_state.get('session_token', '')
storage_sync_script = f"""
<script>
(function() {{
  try {{
    const storedTheme = localStorage.getItem('finance_theme_mode');
    const currentParam = new URLSearchParams(window.location.search).get('theme');
    
    // If user has a stored theme preference and it's not yet in the URL query params, sync it
    if (storedTheme && (!currentParam || currentParam !== storedTheme)) {{
      const url = new URL(window.location.href);
      url.searchParams.set('theme', storedTheme);
      window.location.replace(url.href);
      return;
    }}
    
    // Save current active theme into localStorage
    const currentTheme = {'"dark"' if st.session_state.dark_mode else '"light"'};
    localStorage.setItem('finance_theme_mode', currentTheme);
    
    // Restore session token from localStorage if available and not in URL
    const savedToken = localStorage.getItem('finance_session_token');
    const sessionParam = new URLSearchParams(window.location.search).get('session');
    if (savedToken && (!sessionParam || sessionParam !== savedToken)) {{
      const url = new URL(window.location.href);
      url.searchParams.set('session', savedToken);
      window.location.replace(url.href);
      return;
    }}
    
    // Save session token to localStorage when logged in
    const sessionToken = '{session_token_value}';
    if (sessionToken) {{
      localStorage.setItem('finance_session_token', sessionToken);
    }} else {{
      localStorage.removeItem('finance_session_token');
    }}
  }} catch(e) {{
    // Silently ignore storage errors if cookies/storage blocked
  }}
}})();
</script>
"""
st.markdown(storage_sync_script, unsafe_allow_html=True)


# ── Helpers ──────────────────────────────────────────────────────────

# ── Helpers ──────────────────────────────────────────────────────────
def _synchronize_column_partition(changed_key, other_key, options):
    """Removing a chip moves that column to the opposite group."""
    selected = set(st.session_state.get(changed_key, []))
    st.session_state[other_key] = [c for c in options if c not in selected]


def _initialize_column_partition(prefix, options, included_defaults):
    """Ensure every option belongs to exactly one visible group."""
    included_key = f"{prefix}_schema_feature_columns"
    excluded_key = f"{prefix}_schema_id_columns"
    signature_key = f"_{prefix}_column_partition_signature"
    signature = tuple(options)
    if st.session_state.get(signature_key) != signature:
        included = [c for c in included_defaults if c in options]
        st.session_state[included_key] = included
        st.session_state[excluded_key] = [c for c in options if c not in set(included)]
        st.session_state[signature_key] = signature
    else:
        included = [c for c in st.session_state.get(included_key, []) if c in options]
        excluded = [c for c in st.session_state.get(excluded_key, []) if c in options]
        included_set = set(included)
        excluded_set = set(excluded) - included_set
        included.extend(c for c in options if c not in included_set and c not in excluded_set)
        st.session_state[included_key] = included
        st.session_state[excluded_key] = [c for c in options if c not in set(included)]
    return included_key, excluded_key


def suggest_best_search_field(df):
    """AI suggests the best field for searching based on data characteristics."""
    if df is None or len(df) == 0:
        return None
    
    columns = df.columns.tolist()
    
    if not columns:
        return None
    
    # Analyze each column for search suitability
    column_scores = {}
    
    for col in columns:
        score = 0
        col_lower = col.lower()
        
        # High priority for ID-like columns
        if any(keyword in col_lower for keyword in ['client_id', 'customer_id', 'customer', 'client']):
            score += 100
        elif 'id' in col_lower:
            score += 80
        elif 'name' in col_lower:
            score += 70
        elif 'code' in col_lower:
            score += 60
        elif 'number' in col_lower:
            score += 50
        
        # Check if column has good search characteristics
        try:
            unique_ratio = df[col].nunique() / len(df)
            # Ideal: 0.1 to 0.9 unique ratio (not too unique, not too constant)
            if 0.1 <= unique_ratio <= 0.9:
                score += 30
            elif unique_ratio > 0.9:
                score += 10  # Too unique but still searchable
            else:
                score += 5   # Too constant but still searchable
            
            # Prefer string-like columns
            if df[col].dtype == 'object':
                score += 20
            elif df[col].dtype in ['int64', 'float64']:
                score += 15
            
            # Check if column has reasonable length for search
            if df[col].dtype == 'object':
                avg_length = df[col].astype(str).str.len().mean()
                if 3 <= avg_length <= 50:  # Not too short, not too long
                    score += 25
                    
        except:
            # If analysis fails, give neutral score
            score += 10
        
        column_scores[col] = score
    
    # Return the column with highest score
    if column_scores:
        best_column = max(column_scores, key=column_scores.get)
        return best_column
    
    return columns[0] if columns else None

def _as_dict(value):
    """Return validation/report objects as dictionaries across dict and Pydantic versions."""
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    try:
        return dict(value)
    except Exception:
        return {"value": str(value)}

def title(k,h,d):
    st.markdown(f'<div class="app-hero"><div class="app-kicker">{k}</div><h1 style="margin:0.3rem 0 0.35rem;">{h}</h1><p>{d}</p></div>',unsafe_allow_html=True)

def show_metrics(m):
    labels = {
        'roc_auc': 'ROC-AUC', 'pr_auc': 'PR-AUC', 'f1': 'F1 Score',
        'accuracy': 'Accuracy', 'precision': 'Precision', 'recall': 'Recall',
        'wape': 'WAPE', 'mae': 'MAE', 'rmse': 'RMSE', 'r2': 'R² Score'
    }
    keys=[k for k,v in m.items() if isinstance(v,(int,float)) and not isinstance(v,bool)][:8]
    if not keys: return
    for c,k in zip(st.columns(min(4,len(keys))),keys[:4]):
        lbl = labels.get(k.lower(), k.replace('_', ' ').title())
        c.metric(lbl, 'N/A' if m[k] is None else f"{m[k]:.3f}")
    if len(keys)>4:
        for c,k in zip(st.columns(min(4,len(keys)-4)),keys[4:8]):
            lbl = labels.get(k.lower(), k.replace('_', ' ').title())
            c.metric(lbl, 'N/A' if m[k] is None else f"{m[k]:.3f}")

def render_risk_kpis(summary):
    a,b,c,d,e=st.columns(5)
    a.metric('Total Evaluated',f"{summary['total_records']:,}")
    b.metric('🔴 High Risk',f"{summary['high_risk']:,}")
    c.metric('🟡 Medium Risk',f"{summary['medium_risk']:,}")
    d.metric('🟢 Low Risk',f"{summary['low_risk']:,}")
    e.metric('Avg Risk Score',f"{summary['average_risk']:.1%}")

def render_analysis_guidance(advice):
    st.subheader("Managerial Decision Support")
    st.markdown(f"**{advice.get('executive_summary','Analysis completed from verified model evidence.')}**")
    cols=st.columns(2)
    with cols[0]:
        st.markdown("**Key observations**")
        for item in advice.get("strengths",[]): st.success(item)
        for item in advice.get("weaknesses",[]): st.warning(item)
    with cols[1]:
        st.markdown("**Recommended managerial actions**")
        for item in advice.get("recommendations",[]): st.info(item)
    st.caption(f"Generated by {advice.get('generator','decision-support engine')}. {advice.get('human_review_notice','Human review is required for consequential action.')}")


def render_forecast_alerts(result, target):
    alerts=forecast_alerts(result,target)
    st.subheader("Financial Risk Alerts")
    if alerts.empty: st.success("No configured anomaly, decline, stock, or cashflow alert was triggered.")
    else: st.dataframe(alerts,use_container_width=True,hide_index=True)
    return alerts

def render_model_assessment(ass):
    st.markdown(
        f"""
<div class="ai-box" style="margin-top:0.9rem;">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.55rem;flex-wrap:wrap;gap:0.3rem;">
    <div style="font-size:0.75rem;font-weight:800;letter-spacing:0.08em;text-transform:uppercase;color:var(--primary);">
      Governance & Evaluation Summary
    </div>
    <span class="badge badge-neutral">Generated by {ass.get('generator','AI Engine')}</span>
  </div>
  <p style="margin:0;font-size:0.95rem;line-height:1.6;color:var(--text);font-weight:500;">
    {ass.get('executive_summary','')}
  </p>
</div>
""",
        unsafe_allow_html=True,
    )
    c1,c2=st.columns(2)
    with c1:
        st.markdown('<div style="font-weight:700;color:var(--success);font-size:0.88rem;margin:0.6rem 0 0.35rem;">✓ Validated Strengths</div>',unsafe_allow_html=True)
        for x in ass.get('strengths',[]):
            st.markdown(f'<div class="rec-card" style="border-left:3px solid var(--success);"><div style="font-size:0.88rem;color:var(--text);">{x}</div></div>',unsafe_allow_html=True)
    with c2:
        st.markdown('<div style="font-weight:700;color:var(--warning);font-size:0.88rem;margin:0.6rem 0 0.35rem;">⚠ Cautions & Edge Cases</div>',unsafe_allow_html=True)
        for x in ass.get('weaknesses',[]):
            st.markdown(f'<div class="rec-card" style="border-left:3px solid var(--warning);"><div style="font-size:0.88rem;color:var(--text);">{x}</div></div>',unsafe_allow_html=True)
    st.markdown('<div style="font-weight:700;color:var(--primary);font-size:0.88rem;margin:0.75rem 0 0.35rem;">→ Recommendations for Production</div>',unsafe_allow_html=True)
    for x in ass.get('recommendations',[]):
        st.markdown(f'<div class="rec-card" style="border-left:3px solid var(--primary);"><div style="font-size:0.88rem;color:var(--text);">{x}</div></div>',unsafe_allow_html=True)
    st.caption(f"Generated by {ass.get('generator','AI Engine')}. {ass.get('human_review_notice','')}")

def render_active_model(task_type, meta):
    if hasattr(meta, 'active'):
        try:
            _, meta = meta.active(task_type)
        except Exception:
            st.info(f'No active {task_type} model yet.')
            return
    if not isinstance(meta, dict):
        st.info(f'No active {task_type} model yet.')
        return
    vid = meta.get('version_id', 'N/A')
    algo = meta.get('algorithm', 'unknown')
    trained = str(meta.get('training_timestamp', 'N/A'))[:19]
    st.markdown(
        f"""
<div class="active-model-card">
  <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:0.5rem;">
    <div>
      <span class="badge badge-success">● Active Production Model</span>
      <h3 style="margin:0.35rem 0 0.2rem;font-size:1.25rem;">{vid}</h3>
      <div style="color:var(--muted);font-size:0.85rem;">
        Algorithm: <strong style="color:var(--text);">{algo}</strong> &nbsp;•&nbsp; 
        Trained: <span style="color:var(--text);">{trained}</span>
      </div>
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

@st.cache_data(show_spinner=False, max_entries=6)
def _read_upload_cached(data: bytes, filename: str):
    # Streamlit reruns the script after every widget action. Cache parsing by
    # file content so CSV/Excel decoding happens only once per uploaded file.
    return read_tabular_bytes(data, filename)


def read_upload(f):
    if f.size > MAX_UPLOAD_MB * 1024 * 1024:
        raise ValueError(f'File exceeds {MAX_UPLOAD_MB} MB.')
    return _read_upload_cached(f.getvalue(), f.name).copy(deep=False)


def _schema_cache_key(df, task, meanings):
    # A quick, stable signature. Hash only a small sample rather than the full
    # training set, which keeps large-file recognition responsive.
    sample = df.head(64)
    sample_hash = int(pd.util.hash_pandas_object(sample, index=True).sum()) if len(sample) else 0
    meaning_items = tuple(sorted((str(k), str(v)) for k, v in (meanings or {}).items()))
    return (task, len(df), tuple(map(str, df.columns)), tuple(map(str, df.dtypes)), sample_hash, meaning_items)

def report_ui(r):
    a,b,c,d=st.columns(4)
    a.metric('Validated Rows',f"{r.rows:,}")
    b.metric('Columns Count',r.columns)
    c.metric('Duplicates',r.duplicates)
    d.metric('Missing Cells',r.missing_cells)
    for i in r.issues: (st.error if i.level=='error' else st.warning)(i.message)

def excel_bytes(df):
    b=io.BytesIO()
    with pd.ExcelWriter(b,engine='openpyxl') as w: df.to_excel(w,index=False,sheet_name='Results')
    return b.getvalue()

def column_meanings_editor(columns, prefix):
    """Optional administrator-authored semantics persisted with the trained model."""
    columns=[str(c) for c in columns]
    state_key=f"{prefix}_column_meanings_data"
    signature_key=f"_{prefix}_column_meanings_signature"
    if st.session_state.get(signature_key) != tuple(columns):
        previous={str(row.get("Column")):str(row.get("Meaning") or "") for row in st.session_state.get(state_key,[])}
        st.session_state[state_key]=pd.DataFrame({"Column":columns,"Meaning":[previous.get(c,"") for c in columns]})
        st.session_state[signature_key]=tuple(columns)
    st.caption("Optional: describe what each column means. The descriptions are saved with this model, supplied to the SLM as semantic context, and shown when users hover over table headers.")
    edited=st.data_editor(
        st.session_state[state_key], hide_index=True, use_container_width=True,
        disabled=["Column"], num_rows="fixed", key=f"{prefix}_column_meanings_editor",
        column_config={
            "Column":st.column_config.TextColumn("Column",width="medium"),
            "Meaning":st.column_config.TextColumn("Meaning (optional)",width="large",help="Business definition, units, coding, or when the value is known."),
        },
    )
    st.session_state[state_key]=edited
    return {str(row.Column):str(row.Meaning).strip() for row in edited.itertuples(index=False) if pd.notna(row.Meaning) and str(row.Meaning).strip()}

def saved_model_contract(meta):
    """Return the exact administrator training-file structure saved with this model."""
    source_columns=list(meta.get('training_source_columns') or [])
    prediction_columns=set(meta.get('prediction_input_columns') or meta.get('raw_features') or [])
    contract=list(meta.get('input_contract') or [])
    meanings={str(k):str(v) for k,v in (meta.get('column_meanings') or {}).items()}
    by_name={str(item.get('name')):item for item in contract}
    rows=[]
    for position,name in enumerate(source_columns):
        item=by_name.get(str(name),{})
        role=item.get('role') or ('prediction input' if name in prediction_columns else 'training-only column')
        rows.append({
            'Column':str(name),
            'Order':position+1,
            'Training data type':item.get('dtype','unknown'),
            'Used for prediction':bool(item.get('used_by_model',name in prediction_columns)),
            'Required when testing':bool(name in prediction_columns),
            'Role':role,
            'Meaning':item.get('meaning') or meanings.get(str(name),''),
            'Example from training':item.get('example',''),
        })
    return source_columns,pd.DataFrame(rows)

def render_saved_model_structure(meta,task,key_prefix):
    source_columns,docs=saved_model_contract(meta)
    if not source_columns:
        st.error('The active model does not contain its original training-file structure. Retrain and activate this agent once. No predefined fallback is used.')
        return
    label='payment-risk' if task=='credit' else 'forecast'
    prediction_count=len(meta.get('prediction_input_columns') or meta.get('raw_features') or [])
    st.caption(f"Active {label} model: {meta.get('version_id','unknown')} | Training file: {len(source_columns)} columns | Prediction inputs: {prediction_count}")
    empty=pd.DataFrame(columns=source_columns)
    st.download_button(
        'Download empty training-structure template',
        empty.to_csv(index=False).encode('utf-8'),
        f'{label}_empty_training_structure.csv',
        'text/csv',
        key=f'{key_prefix}_download',
    )
    st.dataframe(docs,use_container_width=True,hide_index=True,height=min(600,80+36*len(docs)))
    st.info('The downloaded CSV contains the exact headers and order of the file used to train this active model. Training target and outcome columns remain in the empty structure for an exact match, but are not required or used when testing new records.')


def _manual_features(model,meta):
    features=list(meta.get("raw_features") or meta.get("features") or [])
    if not features and hasattr(model,"feature_names_in_"): features=list(model.feature_names_in_)
    return [str(x) for x in features if str(x)!="client_id"],set(meta.get("numeric_features") or [])

def manual_credit_form(model,meta,prefix):
    raw_features=list(meta.get("raw_features") or meta.get("prediction_input_columns") or meta.get("features") or [])
    model_features=list(meta.get("features") or raw_features)
    if not raw_features:
        st.error("No raw feature contract is saved. Retrain the active model.")
        return None
    st.markdown("#### Customer payment history")
    st.caption("The table shows every field required by the active model. Add one row per invoice, use History for completed payments, and use Current for the invoice to assess. Scroll horizontally when the model contains many fields.")
    state_key=prefix+"_history_editor_data"
    if state_key not in st.session_state:
        st.session_state[state_key]=empty_editor_frame(raw_features,3)
    numeric=set(meta.get("numeric_features") or [])
    meanings={str(k):str(v) for k,v in (meta.get("column_meanings") or {}).items()}
    for item in meta.get("input_contract") or []:
        if item.get("meaning"): meanings.setdefault(str(item.get("name")),str(item.get("meaning")))
    config={
        RECORD_TYPE: st.column_config.SelectboxColumn("Record Type",options=[HISTORY,CURRENT],required=True,width="small",help="History = a completed previous invoice. Current = the invoice to assess."),
        "client_id": st.column_config.TextColumn("Client ID", required=True, width="medium"),
        "cust_number": st.column_config.TextColumn("Customer Number", required=True, width="medium"),
        "customer_id": st.column_config.TextColumn("Customer ID", required=True, width="medium"),
        "clear_date": st.column_config.TextColumn("Payment / Clear Date",help="History rows only. Leave blank for a current unpaid invoice."),
        "is_late": st.column_config.NumberColumn("Was Late (0/1)",min_value=0,max_value=1,step=1,help="Optional when Payment Date and Due Date are supplied."),
        "delay_days": st.column_config.NumberColumn("Delay Days",min_value=0,step=1,help="Optional historical outcome."),
    }
    for feature in raw_features:
        if feature in numeric:
            config[feature]=st.column_config.NumberColumn(_readable_factor_name(feature),width="medium",help=meanings.get(str(feature)) or None)
        else:
            config[feature]=st.column_config.TextColumn(_readable_factor_name(feature),width="medium",help=meanings.get(str(feature)) or None)
    edited=st.data_editor(
        st.session_state[state_key], num_rows="dynamic", use_container_width=True,
        hide_index=True, column_config=config, key=prefix+"_history_editor",
        height=min(560, 150 + 42 * max(3, len(st.session_state[state_key]))),
    )
    c1,c2=st.columns([1,3])
    with c1:
        go=st.button("Assess current payment",type="primary",key=prefix+"_history_submit",use_container_width=True)
    with c2:
        st.caption("Tip: keep the same client/customer number on all rows for one customer. The last invoice can be marked Current.")
    if not go:return None
    try:
        current,stats=prepare_history_assessment(edited,model_features)
    except ValueError as exc:
        st.error(str(exc));return None
    if stats["history_rows"] and not stats["model_uses_history"]:
        st.warning("The active model was trained without customer-history features. The Current row can still be scored, but historical rows will influence predictions only after retraining and activating a new model with this project version.")
    elif stats["history_used"]:
        st.success(f"Using {stats['history_rows']} historical payment record(s) to assess {stats['current_rows']} current invoice(s).")
    return current

def _baseline_value(series):
    numeric=pd.to_numeric(series,errors='coerce')
    if numeric.notna().mean() >= .8:
        return float(numeric.median())
    mode=series.astype('string').dropna().mode()
    return str(mode.iloc[0]) if not mode.empty else ''

def _slm_review_factor_phrases(items):
    """Let the configured local SLM improve wording without inventing evidence."""
    endpoint=os.getenv('SLM_ENDPOINT','');model_name=os.getenv('SLM_MODEL','qwen2.5:1.5b')
    if not endpoint or not items:return {}
    compact={str(i):row for i,row in enumerate(items[:200])}
    prompt={'instruction':'Rewrite each supplied model-sensitivity factor as a short factual label. Do not add features, causality, or facts. Return JSON mapping each id to one short string.','items':compact}
    try:
        req=urllib.request.Request(endpoint,data=json.dumps({'model':model_name,'stream':False,'prompt':'Return strict JSON only: '+json.dumps(prompt,default=str)}).encode(),headers={'Content-Type':'application/json'})
        raw=json.loads(urllib.request.urlopen(req,timeout=25).read());out=json.loads(raw['response'])
        return out if isinstance(out,dict) else {}
    except Exception:return {}

def _readable_factor_name(name):
    labels={
        "total_open_amount":"Invoice amount",
        "business_code":"Business unit",
        "buisness_year":"Business year",
        "business_year":"Business year",
        "invoice_currency":"Invoice currency",
        "document type":"Document type",
        "cust_payment_terms":"Customer payment terms",
        "payment_window_days":"Payment window",
        "previous_late_ratio":"Previous late-payment rate",
        "average_previous_delay_days":"Average previous delay",
        "maximum_previous_delay_days":"Maximum previous delay",
        "previous_invoice_count":"Previous invoice count",
        "invoice_vs_customer_average":"Amount compared with customer average",
    }
    key=str(name).strip().lower()
    return labels.get(key, str(name).replace("_", " ").strip().title())


def _display_factor_value(value):
    if pd.isna(value):
        return "Not available"
    if isinstance(value, (float, np.floating)):
        return f"{float(value):,.2f}"
    return str(value)


def key_risk_factors(aligned,model,meta,probabilities,top_k=3,min_impact=.0005):
    """Return readable, multiline, model-grounded local prediction drivers."""
    features=list(meta.get('features') or aligned.columns)
    base=aligned.loc[:,features].copy();n=len(base)
    impacts={name:np.zeros(n) for name in features}
    values={name:base[name].copy() for name in features}
    for name in features:
        changed=base.copy();changed[name]=_baseline_value(base[name])
        try:
            impacts[name]=np.abs(probabilities-model.predict_proba(changed)[:,1])
        except Exception:
            impacts[name]=np.zeros(n)
    result=[]
    for pos in range(n):
        ranked=sorted(features,key=lambda f:float(impacts[f][pos]),reverse=True)
        meaningful=[name for name in ranked if float(impacts[name][pos])>=min_impact][:top_k]
        if not meaningful:
            result.append("No strong individual driver identified. The score results from several weak combined factors.")
            continue
        lines=[]
        for number,name in enumerate(meaningful,1):
            impact=float(impacts[name][pos])
            percent=impact*100
            impact_text="less than 0.1%" if percent < .1 else f"{percent:.1f}%"
            label=_readable_factor_name(name)
            value=_display_factor_value(values[name].iloc[pos])
            lines.append(f"{number}. {label}: {value} | Influence: {impact_text}")
        result.append("\n".join(lines))
    return result

def score_credit(raw,model,meta):
    model_features=list(meta.get("features") or [])
    # Uploaded one-customer history files can use Record Type just like the editor.
    if "record_type" in raw.columns:
        raw,_history_stats=prepare_history_assessment(raw,model_features)
    elif any(feature.startswith("previous_") or feature in {"customer_history_available","recent_5_late_ratio","average_previous_delay_days","maximum_previous_delay_days","days_since_previous_invoice","consecutive_previous_late_count","invoice_vs_customer_average"} for feature in model_features):
        # For a one-customer history file without Record Type, earlier rows are
        # history and the latest row per customer is the invoice to assess.
        raw,_history_stats=prepare_history_assessment(raw,model_features)
    d,r=validate_for_model(raw,model,meta)
    if not r.valid:return None,r,None,d
    feats=meta.get("features") or list(d.columns);p=model.predict_proba(d.loc[:,feats])[:,1];tier=np.where(p>=.65,"HIGH",np.where(p>=.35,"MEDIUM","LOW"))
    res=d.copy();res.insert(0,"client_id",raw["client_id"].astype(str).to_numpy() if "client_id" in raw else [f"client_{i+1}" for i in range(len(d))]);res["risk_score"]=p;res["risk_tier"]=tier
    res["key_risk_factors"]=key_risk_factors(d,model,meta,p)
    summary={"average_risk":float(p.mean()),"high_risk":int((tier=="HIGH").sum()),"medium_risk":int((tier=="MEDIUM").sum()),"low_risk":int((tier=="LOW").sum()),"total_records":len(d)}
    return res,r,summary,d

# ── Session restore from token ───────────────────────────────────────
if 'user' not in st.session_state:
    token=st.query_params.get('session')
    if token:
        restored=validate_session(token)
        if restored:
            st.session_state.user=restored
            st.session_state.session_token=token
            # Sync to localStorage
            st.markdown(f'<script>localStorage.setItem("finance_session_token", "{token}");</script>', unsafe_allow_html=True)

def login():
    st.markdown('<div style="margin-top: 40px;"></div>', unsafe_allow_html=True)
    col1, col2 = st.columns([1.15, 1], gap="large")
    with col1:
        st.markdown(
            """
<div class="app-hero" style="height: 100%; display: flex; flex-direction: column; justify-content: space-between; padding: 2.2rem 2rem;">
  <div>
    <div class="app-kicker">Enterprise Financial Intelligence</div>
    <h1 style="margin: 0.6rem 0 0.8rem; font-size: 2.2rem; line-height: 1.2;">ML Intelligence Center</h1>
    <p style="font-size: 1.02rem; line-height: 1.6; margin-bottom: 1.5rem; color: var(--muted);">
      Two-sided enterprise financial decision support system. Governed model lifecycle management for administrators, and real-time risk & cashflow forecasting for organizations.
    </p>
    <div style="display: flex; flex-direction: column; gap: 0.75rem; margin-top: 1.2rem;">
      <div style="display: flex; align-items: center; gap: 0.65rem; color: var(--text); font-size: 0.92rem;">
        <span class="badge badge-primary">Governed AI</span> Stratified & chronological evaluation splits
      </div>
      <div style="display: flex; align-items: center; gap: 0.65rem; color: var(--text); font-size: 0.92rem;">
        <span class="badge badge-success">Credit Risk</span> Multi-algorithm scoring, tiers & SHAP impact
      </div>
      <div style="display: flex; align-items: center; gap: 0.65rem; color: var(--text); font-size: 0.92rem;">
        <span class="badge badge-warning">Forecasting</span> Chronological WAPE evaluation & stockout alerts
      </div>
      <div style="display: flex; align-items: center; gap: 0.65rem; color: var(--text); font-size: 0.92rem;">
        <span class="badge badge-neutral">AI Guidance</span> Deterministic audit trail & executive narratives
      </div>
    </div>
  </div>
  <div style="margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--border); font-size: 0.82rem; color: var(--muted);">
    🔒 Isolated tenant workspaces & cryptographic audit tokens
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
    with col2:
        a,b=st.tabs(['Sign In','Create Workspace'])
        with a:
            st.markdown('<p style="color: var(--muted); font-size: 0.88rem; margin-bottom: 0.9rem;">Sign in to your platform account or administrator console.</p>', unsafe_allow_html=True)
            with st.form('login'):
                e=st.text_input('Work Email', placeholder='admin@finance.local')
                p=st.text_input('Password', type='password', placeholder='••••••••••••')
                go=st.form_submit_button('Sign In to Platform', type='primary', use_container_width=True)
            if go:
                u=verify(e,p)
                if u:
                    token=create_session(u['email'])
                    st.session_state.user=u
                    st.session_state.session_token=token
                    st.query_params['session']=token
                    # Save to localStorage
                    st.markdown(f'<script>localStorage.setItem("finance_session_token", "{token}");</script>', unsafe_allow_html=True)
                    st.rerun()
                else: st.error('Invalid credentials or inactive account.')
        with b:
            st.markdown('<p style="color: var(--muted); font-size: 0.88rem; margin-bottom: 0.9rem;">Register a tenant workspace for governed financial analytics.</p>', unsafe_allow_html=True)
            with st.form('signup'):
                c=st.text_input('Company Name', placeholder='Acme Global Capital')
                n=st.text_input('Full Name', placeholder='Alex Martin')
                e=st.text_input('Work Email', placeholder='alex@acme.com')
                p=st.text_input('Password (minimum 10 characters)', type='password', placeholder='••••••••••••')
                go=st.form_submit_button('Create Company Workspace', type='primary', use_container_width=True)
            if go:
                ok,msg=signup(c,n,e,p); 
                if ok:
                    st.success(msg)
                    # Auto-login after successful signup
                    u=verify(e,p)
                    if u:
                        token=create_session(u['email'])
                        st.session_state.user=u
                        st.session_state.session_token=token
                        st.query_params['session']=token
                        # Save to localStorage
                        st.markdown(f'<script>localStorage.setItem("finance_session_token", "{token}");</script>', unsafe_allow_html=True)
                        st.rerun()
                else:
                    st.error(msg)

if 'user' not in st.session_state: login(); st.stop()
u=st.session_state.user; role=u['role']; company=u['company_id']

# ── Sidebar ──────────────────────────────────────────────────────────
with st.sidebar:

    st.markdown(
        f"""
    <div style="padding: 0 0 0.5rem; border-bottom: 1px solid var(--border); margin-bottom: 0.9rem;">
      <div class="app-kicker" style="margin-bottom: 0.2rem;">Fintech AI Platform</div>
      <h2 style="margin: 0; font-size: 1.25rem; letter-spacing: -0.025em; display: flex; align-items: center; gap: 0.4rem;">
        <span style="color: var(--primary);">◆</span> ML Center
      </h2>
    </div>
    <div class="user-chip">
      <div style="font-weight: 750; color: var(--text); font-size: 0.9rem;">{u['name']}</div>
      <div style="color: var(--muted); font-size: 0.77rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{u['email']}</div>
      <div style="margin-top: 0.35rem;">
        <span class="badge {'badge-primary' if role=='admin' else 'badge-success'}">
          {'★ Platform Administrator' if role=='admin' else f'🏢 {u.get("company_id","Workspace")}'}
        </span>
      </div>
    </div>
    """,
        unsafe_allow_html=True,
    )
    if role=='admin':
        pages=['Model Training','Credit Risk Agent','Forecast Agent']
    else:
        pages=['Credit Risk Analysis','Demand Forecast']
    page=st.radio('Navigation',pages)
    st.markdown('<div style="margin-top: 1rem;"></div>', unsafe_allow_html=True)
    if st.button('Sign Out', use_container_width=True):
        destroy_session(st.session_state.get('session_token'))
        current_theme = st.query_params.get('theme')
        st.session_state.clear()
        st.query_params.clear()
        if current_theme:
            st.query_params['theme'] = current_theme
        # Clear session token from localStorage
        st.markdown('<script>localStorage.removeItem("finance_session_token");</script>', unsafe_allow_html=True)
        st.rerun()

# ══════════════════════════════════════════════════════════════════════
#  ADMIN PAGES
# ══════════════════════════════════════════════════════════════════════
if role=='admin':

    # ── Page 1: Model Training ───────────────────────────────────────
    if page=='Model Training':

        tab_credit, tab_forecast = st.tabs(['💳 Credit Risk Model','📈 Forecast Model'])

        # — Credit training tab —
        with tab_credit:
            st.subheader('Train Credit Risk Model')
            
            # Initialize training step
            if 'credit_training_step' not in st.session_state:
                st.session_state.credit_training_step = 1
            
            # Step 1: Upload
            if st.session_state.credit_training_step == 1:
                st.markdown('### Step 1: Upload Training Data')
                fs=st.file_uploader('Upload credit training file (CSV, XLSX, or XLS)',type=['csv','xlsx','xls'],accept_multiple_files=False,key='train_credit')
                if fs:
                    try:
                        raw=read_upload(fs)
                        
                        # Store data for next step
                        st.session_state.credit_training_data = raw
                        st.session_state.credit_file_hash = hashlib.md5((fs.name + str(getattr(fs, 'size', ''))).encode()).hexdigest()[:8]
                        
                        if st.button('Continue to Schema Analysis', type='primary'):
                            st.session_state.credit_training_step = 2
                            st.rerun()
                    except Exception as e:
                        st.error(f'Error processing file: {e}')
            
            # Step 2: Schema Analysis
            elif st.session_state.credit_training_step == 2:
                st.markdown('### Step 2: Schema Analysis')
                raw = st.session_state.credit_training_data

                # Collect business meanings before any automatic role mapping. This gives
                # the rule-based analyzer and SLM semantic context for target/features/IDs.
                credit_columns = [str(c) for c in raw.columns]
                credit_meaning_signature = tuple(credit_columns)
                meanings_ready = st.session_state.get('_credit_meanings_ready_signature') == credit_meaning_signature
                if not meanings_ready:
                    st.markdown('### Step 2A: Describe Columns')
                    st.info('Add the business meaning of ambiguous columns before mapping. This helps identify targets, useful features, IDs, and possible data-leakage columns. Meanings may be left blank when a column name is already clear.')
                    entered_meanings = column_meanings_editor(credit_columns, 'credit_schema')
                    if st.button('Analyze and map columns', type='primary', key='credit_analyze_with_meanings'):
                        st.session_state.credit_column_meanings = entered_meanings
                        st.session_state._credit_meanings_ready_signature = credit_meaning_signature
                        st.session_state.pop('_credit_schema_cache_key', None)
                        st.session_state.pop('_credit_schema_cache_value', None)
                        st.rerun()
                    st.stop()

                column_meanings = st.session_state.get('credit_column_meanings', {})
                st.markdown('### Step 2B: Review Column Mapping')
                if st.button('← Edit column meanings', key='credit_edit_meanings'):
                    st.session_state.pop('_credit_meanings_ready_signature', None)
                    st.rerun()

                # Flexible mode with auto-detection
                st.markdown('### 🔍 Auto-Detected Schema')
                
                # Check for schema migration requirements first
                fingerprint = hashlib.md5(json.dumps(sorted([str(c) for c in raw.columns]), sort_keys=True).encode()).hexdigest()[:8]
                has_saved_schemas = len(get_schema_versions('credit')) > 0
                
                if has_saved_schemas:
                    migration_check = check_schema_migration_required(fingerprint, 'credit')
                    
                    if migration_check['migration_required']:
                        st.warning('⚠️ **New Schema Architecture Detected')
                        st.markdown(f"""
**Migration Alert:** Your file has a different structure than the previous training data.

**Changes:**
- {migration_check['message']}
- Previous Schema: `{migration_check['old_schema'].version_id[:20]}...`
- Created: {migration_check['old_schema'].created_at}
""", unsafe_allow_html=True)
                        
                        if migration_check['can_compare']:
                            comp = migration_check['comparison']
                            st.markdown('**Detailed Changes:**')
                            if comp['added_features']:
                                st.markdown(f"✅ **Added Features:** {', '.join(comp['added_features'][:5])}")
                            if comp['removed_features']:
                                st.markdown(f"❌ **Removed Features:** {', '.join(comp['removed_features'][:5])}")
                            if comp['target_changed']:
                                st.markdown(f"🎯 **Target Changed:** `{comp['old_target']}` → `{comp['new_target']}`")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button('✅ Yes, Migrate to New Architecture', type='primary', key='migrate_credit'):
                                st.session_state.credit_migration_confirmed = True
                                st.rerun()
                        with col2:
                            if st.button('❌ No, Keep Current Architecture', key='keep_credit'):
                                st.session_state.credit_migration_confirmed = False
                                st.stop()
                        
                        if not st.session_state.get('credit_migration_confirmed', False):
                            st.stop()
                
                # Analyze each file/schema only once. Widget reruns reuse the result.
                credit_meanings = column_meanings
                credit_schema_key = _schema_cache_key(raw, "credit", credit_meanings)
                force_refresh = st.checkbox('🔄 Force AI Re-analysis (ignore cache)', value=False, key='force_refresh_credit') if has_saved_schemas else False
                if force_refresh or st.session_state.get('_credit_schema_cache_key') != credit_schema_key:
                    rule_based_schema = analyze_dataframe(raw)
                    with st.spinner('🤖 Analyzing schema...'):
                        schema = enhance_schema_with_slm(raw, rule_based_schema, force_slm=force_refresh, column_meanings=credit_meanings)
                    st.session_state['_credit_schema_cache_key'] = credit_schema_key
                    st.session_state['_credit_schema_cache_value'] = schema
                else:
                    schema = st.session_state['_credit_schema_cache_value']
                
                # Show cache/AI status only if there are saved schemas to compare
                if has_saved_schemas:
                    # Show cache status
                    if hasattr(schema, 'from_cache') and schema.from_cache:
                        st.info('⚡ Using cached schema analysis (instant loading)')
                    else:
                        st.info('ℹ️ New schema detected - using AI analysis')
                    
                    # Show SLM status
                    if hasattr(schema, 'slm_reasoning') and schema.slm_reasoning:
                        st.success('✅ Enhanced with AI-powered analysis')
                    else:
                        st.info('ℹ️ Using rule-based analysis (AI unavailable)')
                
                # Show detected schema
                st.markdown(f"**Suggested Target:** `{schema.suggested_target or 'None detected'}`")
                
                # Show AI reasoning if available
                if hasattr(schema, 'slm_reasoning') and schema.slm_reasoning:
                    with st.expander('🧠 AI Analysis Details'):
                        if schema.slm_reasoning.get('target'):
                            st.markdown(f"**Target Reasoning:** {schema.slm_reasoning['target']}")
                        if schema.slm_reasoning.get('task'):
                            st.markdown(f"**Task Type Reasoning:** {schema.slm_reasoning['task']}")
                        if schema.slm_reasoning.get('confidence'):
                            confidence = schema.slm_reasoning['confidence']
                            st.markdown(f"**AI Confidence:** {confidence:.0%}")
                        
                        if schema.slm_suggestions:
                            st.markdown('**AI Suggestions:**')
                            for suggestion in schema.slm_suggestions:
                                st.markdown(f"- {suggestion}")
                
                # Show column analysis
                st.markdown('#### Column Analysis')
                col_df = pd.DataFrame([{
                    'Column': c.name,
                    'Type': c.dtype,
                    'Role': c.suggested_role,
                    'Missing': c.missing_count,
                    'Unique': c.unique_count,
                    'Confidence': f"{c.confidence:.0%}"
                } for c in schema.columns])
                st.dataframe(col_df, use_container_width=True, hide_index=True)
                
                # Generate and offer template download
                st.markdown('#### 📄 Data Template')
                st.markdown('Download an empty CSV template with the same structure for data collection:')
                
                # Save template
                fingerprint = hashlib.md5(json.dumps(sorted([str(c) for c in raw.columns]), sort_keys=True).encode()).hexdigest()[:8]
                try:
                    save_template(schema, fingerprint, 'credit')
                    template_path = get_current_template(fingerprint)
                    if template_path:
                        template_df = pd.read_csv(template_path)
                        st.download_button('Download Template', template_df.to_csv(index=False).encode(), 'credit_data_template.csv', 'text/csv')
                except Exception as e:
                    st.info(f'Template generation skipped: {e}')
                
                # Let user confirm/modify schema
                st.markdown('#### Confirm Schema')
                # Build every widget option and default from the current uploaded file only.
                column_names = list(dict.fromkeys(str(c.name) for c in schema.columns if str(c.name) in raw.columns))
                suggested_target = schema.suggested_target if schema.suggested_target in column_names else None
                target_options = ([suggested_target] if suggested_target else []) + [c for c in column_names if c != suggested_target]
                if not target_options:
                    st.error('No usable columns were detected in the uploaded file.')
                    st.stop()
                target_col = st.selectbox('Select Target Variable', target_options, index=0, key='credit_schema_target_column')

                # Build smart defaults for included columns (features)
                feature_options = [c for c in column_names if c != target_col]
                feature_defaults = list(dict.fromkeys(
                    c for c in (schema.suggested_features or []) if c in feature_options
                ))
                
                # If AI didn't suggest many features, add important financial ones as defaults
                important_patterns = ['amount', 'payment', 'invoice', 'due', 'terms', 'credit', 'balance', 'price', 'cost']
                if len(feature_defaults) < 5:  # If AI suggested too few features
                    for col in feature_options:
                        if col not in feature_defaults and any(pattern in col.lower() for pattern in important_patterns):
                            # Exclude data leakage patterns
                            if not any(leakage in col.lower() for leakage in ['clear', 'settle', 'settlement', 'paid_date', 'result', 'outcome']):
                                feature_defaults.append(col)
                
                # Add important date patterns if still too few features
                if len(feature_defaults) < 5:
                    date_patterns = ['due', 'invoice', 'posting', 'create', 'period', 'fiscal', 'year', 'quarter', 'month']
                    for col in feature_options:
                        if col not in feature_defaults and any(pattern in col.lower() for pattern in date_patterns):
                            # Exclude data leakage patterns
                            if not any(leakage in col.lower() for leakage in ['clear', 'settle', 'settlement', 'paid_date', 'result', 'outcome']):
                                feature_defaults.append(col)
                
                # If still too few, add all remaining columns except clear data leakage
                if len(feature_defaults) < 3:
                    for col in feature_options:
                        if col not in feature_defaults:
                            col_lower = col.lower()
                            # Only exclude clear data leakage and IDs
                            if not any(leakage in col_lower for leakage in ['clear', 'settle', 'settlement', 'paid_date', 'result', 'outcome']):
                                if not any(id_pattern in col_lower for id_pattern in ['id', 'key', 'uuid', 'identifier']):
                                    feature_defaults.append(col)
                
                # Complete, exclusive chip-only partition. No third/unassigned pool.
                excluded_options = list(feature_options)
                included_key, excluded_key = _initialize_column_partition('credit', feature_options, feature_defaults)
                included_assigned = list(st.session_state[included_key])
                excluded_assigned = list(st.session_state[excluded_key])
                feature_cols = st.multiselect('Included Columns (Features)', included_assigned,
                    key=included_key, on_change=_synchronize_column_partition,
                    args=(included_key, excluded_key, feature_options))
                id_cols = st.multiselect('Excluded Columns (IDs, Data Leakage, Low Value)', excluded_assigned,
                    key=excluded_key, on_change=_synchronize_column_partition,
                    args=(excluded_key, included_key, excluded_options))
                st.caption('Column meanings were applied before automatic mapping. Use “Edit column meanings” above to revise them and rerun the mapping.')

                if st.button('Continue to Training', type='primary'):
                    # Update schema based on user selection
                    # Remove overlapping columns from features (IDs take precedence)
                    final_features = [f for f in feature_cols if f not in id_cols]
                    
                    for c in schema.columns:
                        if c.name == target_col:
                            c.suggested_role = 'target'
                        elif c.name in final_features:
                            c.suggested_role = 'feature'
                        elif c.name in id_cols:
                            c.suggested_role = 'id'
                    
                    schema.suggested_target = target_col
                    schema.suggested_features = final_features
                    schema.suggested_ids = id_cols
                    
                    d, validation_result = validate_flexible(raw, schema, training=True)
                    
                    # Store in session state to persist after button click
                    st.session_state.credit_validated = True
                    st.session_state.credit_validation_data = d
                    st.session_state.credit_validation_result = validation_result
                    st.session_state.credit_schema = schema
                    st.session_state.credit_column_meanings = column_meanings
                    st.session_state.credit_raw = raw
                    st.session_state.credit_training_step = 3
                    st.rerun()
            
            # Step 3: Train
            elif st.session_state.credit_training_step == 3:
                st.markdown('### Step 3: Train Model')
                
                # If already validated, show training UI
                if st.session_state.get('credit_validated', False):
                    d = st.session_state.credit_validation_data
                    validation_result = st.session_state.credit_validation_result
                    schema = st.session_state.credit_schema
                    raw = st.session_state.credit_raw
                    
                    # Show validation results
                    if validation_result['issues']:
                        st.markdown('#### Validation Issues')
                        for issue in validation_result['issues']:
                            level_icon = '⚠️' if issue['level'] == 'warning' else '❌'
                            st.markdown(f"{level_icon} **{issue.get('column', 'General')}:** {issue['message']}")
                    
                    if validation_result['valid']:
                        st.success('✅ Dataset validated successfully!')
                        st.dataframe(d.head(30), use_container_width=True, hide_index=True)
                        
                        # Auto-clean data (temporarily disabled due to type conversion issues)
                        # st.markdown('#### 🔧 Auto Data Cleaning')
                        # d_cleaned, cleaning_report = auto_clean_dataset(d, schema)
                        # if cleaning_report['fixes_applied']:
                        #     st.info(f"**Data cleaning applied:**")
                        #     for fix in cleaning_report['fixes_applied']:
                        #         st.markdown(f"- {fix}")
                        #     st.caption(f"Rows: {cleaning_report['original_rows']:,} → {cleaning_report['final_rows']:,}")
                        # else:
                        #     st.success("✅ No data quality issues detected")
                        d_cleaned = d
                        
                        # Let the administrator choose which payment-risk models to train.
                        available_algs = ['Logistic Regression', 'Random Forest', 'Extra Trees',
                                          'Hist Gradient Boosting', 'Gradient Boosting', 'XGBoost']
                        st.markdown('#### Select models to train')
                        st.info('Check one or more algorithms. Only the selected models will be trained and compared.')
                        credit_model_columns = st.columns(2)
                        algs = []
                        for model_index, model_name in enumerate(available_algs):
                            with credit_model_columns[model_index % 2]:
                                if st.checkbox(model_name, value=True, key=f'credit_model_choice_{model_index}'):
                                    algs.append(model_name)
                        if not algs:
                            st.warning('Select at least one model before starting training.')
                        else:
                            st.caption(f'{len(algs)} model(s) selected: ' + ', '.join(algs))

                        if st.button('Train selected models',type='primary',key='btn_train_flex',disabled=not algs):
                            try:
                                st.write('Starting training...')
                                with st.status('Training flexible schema models…',expanded=True) as s:
                                    st.write('Using auto-detected schema'); st.write('Creating train/validation/test splits')
                                    progress_bar = st.progress(0, text='Training models...')
                                    def update_progress(current, total, model_name):
                                        progress = current / total
                                        progress_bar.progress(progress, text=f'Training {model_name} ({current}/{total})')
                                    # Train from raw business columns. The fitted sklearn pipeline owns
                                    # imputation and one-hot encoding, which keeps inference contracts stable.
                                    target_col = schema.suggested_target
                                    if not target_col or target_col not in d_cleaned.columns:
                                        raise ValueError(f"Target column '{target_col}' was not found in the training file.")
                                    feature_cols = [
                                        c for c in schema.suggested_features
                                        if c in d_cleaned.columns and c != target_col
                                    ]
                                    if not feature_cols:
                                        feature_cols = [c for c in d_cleaned.columns if c != target_col]
                                    st.write(f'Raw feature contract: {len(feature_cols)} columns')
                                    runs,best=train_credit(d_cleaned,algs,feature_columns=feature_cols,target_column=target_col,column_meanings=st.session_state.get("credit_column_meanings",{}), progress_callback=update_progress); st.write('Evaluating holdout data')
                                    s.update(label='Flexible training complete',state='complete')
                                st.session_state.credit_training=(runs,best,validation_result)
                                st.success('Training completed successfully!')
                                st.session_state.credit_training_step = 4
                                st.rerun()
                            except Exception as train_error:
                                st.error(f'Training failed: {train_error}')
                                import traceback
                                st.error(traceback.format_exc())
                        
                        if st.button('← Back to Schema Selection'):
                            for key in ['credit_validated', 'credit_validation_data', 'credit_validation_result', 'credit_schema', 'credit_raw']:
                                if key in st.session_state:
                                    del st.session_state[key]
                            st.session_state.credit_training_step = 2
                            st.rerun()
                
            # Step 4: Save & Activate
            elif st.session_state.credit_training_step == 4:
                st.markdown('### Step 4: Save & Activate Model')
                
                if 'credit_training' in st.session_state:
                    runs,best,q=st.session_state.credit_training
                    _top1,_top2=st.columns([3,1])
                    with _top1: st.subheader('Model Comparison')
                    with _top2:
                        if st.button('🗑️ Forget training',key='forget_credit'):
                            del st.session_state.credit_training
                            st.session_state.credit_training_step = 3
                            st.rerun()
                    recommendation=recommend_model('credit',runs,q)
                    recommended_name=recommendation['recommended_algorithm']
                    rows=[]
                    for x in runs:
                        row={'Algorithm':x['algorithm'],'Suggested':x['algorithm']==recommended_name,**x['validation']}
                        rows.append(row)
                    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
                    st.success(f"Suggested model: {recommended_name}. All validation metrics and the complete feature contract were considered by {recommendation.get('generator','the ranking engine')}.")
                    st.caption(recommendation.get('reasoning',''))
                    names=[x['algorithm'] for x in runs]
                    selected_name=st.selectbox('Final model selection',names,index=names.index(recommended_name),key='credit_final_model',help='The suggested model is selected by default. The administrator may choose another model after reviewing the comparison table.')
                    selected=next(x for x in runs if x['algorithm']==selected_name)
                    st.subheader('Selected Model Test Metrics'); show_metrics(selected['test'])
                    ass=interpret('credit',selected['test'],{**q,'model_comparison':rows,'selection':selected_name,'suggested':recommended_name})
                    render_model_assessment(ass)
                    if st.button('Save & activate selected credit model',type='primary',key='save_credit'):
                        try:
                            st.write('Saving model to registry...')
                            vid=reg.save('credit',selected,q,ass)
                            st.write(f'Created version: {vid}')
                            st.write('Activating model...')
                            reg.activate('credit',vid)
                            st.success(f'Credit model {vid} saved and activated.')
                            # Clear all training-related state to go back to initial state
                            for key in ['credit_training', 'credit_validated', 'credit_validation_data', 'credit_validation_result', 'credit_schema', 'credit_raw', 'credit_file_hash', 'credit_training_data', 'credit_training_step']:
                                if key in st.session_state:
                                    del st.session_state[key]
                            st.rerun()
                        except Exception as e:
                            st.error(f'Failed to save/activate model: {e}')
                            import traceback
                            st.error(traceback.format_exc())
            
            # Back button on all steps > 1
            if st.session_state.credit_training_step > 1:
                if st.button('← Start Over'):
                    for key in ['credit_training', 'credit_validated', 'credit_validation_data', 'credit_validation_result', 'credit_schema', 'credit_raw', 'credit_file_hash', 'credit_training_data', 'credit_training_step']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()

            # Show current active version and history (only when not in training)
            if st.session_state.get('credit_training_step', 1) == 1:
                st.divider()
                try:
                    _active_model, _active_meta = reg.active('credit')
                    render_active_model('credit', _active_meta)
                except (FileNotFoundError, Exception):
                    st.info('No active credit model yet. Train and save one above.')
                versions=reg.versions('credit')
                if versions:
                    st.subheader('Saved Versions')
                    for v in versions:
                        vid=v['version_id']
                        col1,col2=st.columns([4,1])
                        with col1:
                            st.write(f"**{vid}** — {v.get('algorithm','N/A')} — Trained: {v.get('training_timestamp','N/A')[:19]}")
                        with col2:
                            if st.button("🗑️ Delete", key=f"del_credit_{vid}"):
                                try:
                                    reg.delete("credit", vid)
                                    st.success("Model deleted successfully.")
                                    st.rerun()
                                except AttributeError:
                                    st.error(
                                        "Registry.delete() not found. "
                                        "Check src/services/registry.py and restart the application."
                                    )
                                except Exception as e:
                                    st.error(f"Delete failed: {str(e)}")

        # — Forecast training tab —
        with tab_forecast:
            st.subheader('Train Forecast Model')
            
            # Initialize training step
            if 'forecast_training_step' not in st.session_state:
                st.session_state.forecast_training_step = 1
            
            # Step 1: Upload
            if st.session_state.forecast_training_step == 1:
                st.markdown('### Step 1: Upload Training Data')
                fs=st.file_uploader('Upload forecast training file (CSV, XLSX, or XLS)',type=['csv','xlsx','xls'],accept_multiple_files=False,key='train_forecast')
                if fs:
                    try:
                        raw=read_upload(fs)
                        
                        # Store data for next step
                        st.session_state.forecast_training_data = raw
                        st.session_state.forecast_file_hash = hashlib.md5((fs.name + str(getattr(fs, 'size', ''))).encode()).hexdigest()[:8]
                        
                        if st.button('Continue to Schema Analysis', type='primary'):
                            st.session_state.forecast_training_step = 2
                            st.rerun()
                    except Exception as e:
                        st.error(f'Error processing file: {e}')
            
            # Step 2: Schema Analysis
            elif st.session_state.forecast_training_step == 2:
                st.markdown('### Step 2: Schema Analysis')
                raw = st.session_state.forecast_training_data

                # Collect business meanings before any automatic role mapping.
                forecast_columns = [str(c) for c in raw.columns]
                forecast_meaning_signature = tuple(forecast_columns)
                meanings_ready = st.session_state.get('_forecast_meanings_ready_signature') == forecast_meaning_signature
                if not meanings_ready:
                    st.markdown('### Step 2A: Describe Columns')
                    st.info('Add the business meaning of ambiguous columns before mapping. This helps identify the forecast target, useful predictors, IDs, dates, and possible leakage columns. Meanings may be left blank when a column name is already clear.')
                    entered_meanings = column_meanings_editor(forecast_columns, 'forecast_schema')
                    if st.button('Analyze and map columns', type='primary', key='forecast_analyze_with_meanings'):
                        st.session_state.forecast_column_meanings = entered_meanings
                        st.session_state._forecast_meanings_ready_signature = forecast_meaning_signature
                        st.session_state.pop('_forecast_schema_cache_key', None)
                        st.session_state.pop('_forecast_schema_cache_value', None)
                        st.rerun()
                    st.stop()

                column_meanings = st.session_state.get('forecast_column_meanings', {})
                st.markdown('### Step 2B: Review Column Mapping')
                if st.button('← Edit column meanings', key='forecast_edit_meanings'):
                    st.session_state.pop('_forecast_meanings_ready_signature', None)
                    st.rerun()

                # Flexible mode with auto-detection
                st.markdown('### 🔍 Auto-Detected Schema')
                
                # Check for schema migration requirements first
                fingerprint = hashlib.md5(json.dumps(sorted([str(c) for c in raw.columns]), sort_keys=True).encode()).hexdigest()[:8]
                has_saved_schemas = len(get_schema_versions('forecast')) > 0
                
                if has_saved_schemas:
                    migration_check = check_schema_migration_required(fingerprint, 'forecast')
                    
                    if migration_check['migration_required']:
                        st.warning('⚠️ **New Schema Architecture Detected')
                        st.markdown(f"""
**Migration Alert:** Your file has a different structure than the previous training data.

**Changes:**
- {migration_check['message']}
- Previous Schema: `{migration_check['old_schema'].version_id[:20]}...`
- Created: {migration_check['old_schema'].created_at}
""", unsafe_allow_html=True)
                        
                        if migration_check['can_compare']:
                            comp = migration_check['comparison']
                            st.markdown('**Detailed Changes:**')
                            if comp['added_features']:
                                st.markdown(f"✅ **Added Features:** {', '.join(comp['added_features'][:5])}")
                            if comp['removed_features']:
                                st.markdown(f"❌ **Removed Features:** {', '.join(comp['removed_features'][:5])}")
                            if comp['target_changed']:
                                st.markdown(f"🎯 **Target Changed:** `{comp['old_target']}` → `{comp['new_target']}`")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button('✅ Yes, Migrate to New Architecture', type='primary', key='migrate_forecast'):
                                st.session_state.forecast_migration_confirmed = True
                                st.rerun()
                        with col2:
                            if st.button('❌ No, Keep Current Architecture', key='keep_forecast'):
                                st.session_state.forecast_migration_confirmed = False
                                st.stop()
                        
                        if not st.session_state.get('forecast_migration_confirmed', False):
                            st.stop()
                
                # Analyze each file/schema only once. Widget reruns reuse the result.
                forecast_meanings = column_meanings
                forecast_schema_key = _schema_cache_key(raw, "forecast", forecast_meanings)
                force_refresh = st.checkbox('🔄 Force AI Re-analysis (ignore cache)', value=False, key='forecast_refresh') if has_saved_schemas else False
                if force_refresh or st.session_state.get('_forecast_schema_cache_key') != forecast_schema_key:
                    rule_based_schema = analyze_dataframe(raw)
                    with st.spinner('🤖 Analyzing schema...'):
                        schema = enhance_schema_with_slm_forecast(raw, rule_based_schema, force_slm=force_refresh, column_meanings=forecast_meanings)
                    st.session_state['_forecast_schema_cache_key'] = forecast_schema_key
                    st.session_state['_forecast_schema_cache_value'] = schema
                else:
                    schema = st.session_state['_forecast_schema_cache_value']
                
                # Show cache/AI status only if there are saved schemas to compare
                if has_saved_schemas:
                    # Show cache status
                    if hasattr(schema, 'from_cache') and schema.from_cache:
                        st.info('⚡ Using cached schema analysis (instant loading)')
                    elif force_refresh:
                        st.success('✅ AI re-analysis complete')
                    else:
                        st.info('ℹ️ New schema detected - using AI analysis')
                    
                    # Show SLM status
                    if hasattr(schema, 'slm_reasoning') and schema.slm_reasoning:
                        st.success('✅ Enhanced with AI-powered analysis')
                    else:
                        st.info('ℹ️ Using rule-based analysis (AI unavailable)')
                
                # Show detected schema
                st.markdown(f"**Suggested Target:** `{schema.suggested_target or 'None detected'}`")
                
                # Show AI reasoning if available
                if hasattr(schema, 'slm_reasoning') and schema.slm_reasoning:
                    with st.expander('🧠 AI Analysis Details'):
                        if schema.slm_reasoning.get('target'):
                            st.markdown(f"**Target Reasoning:** {schema.slm_reasoning['target']}")
                        if schema.slm_reasoning.get('task'):
                            st.markdown(f"**Task Type Reasoning:** {schema.slm_reasoning['task']}")
                        if schema.slm_reasoning.get('confidence'):
                            confidence = schema.slm_reasoning['confidence']
                            st.markdown(f"**AI Confidence:** {confidence:.0%}")
                        
                        if schema.slm_suggestions:
                            st.markdown('**AI Suggestions:**')
                            for suggestion in schema.slm_suggestions:
                                st.markdown(f"- {suggestion}")
                
                # Show column analysis
                st.markdown('#### Column Analysis')
                col_df = pd.DataFrame([{
                    'Column': c.name,
                    'Type': c.dtype,
                    'Role': c.suggested_role,
                    'Missing': c.missing_count,
                    'Unique': c.unique_count,
                    'Confidence': f"{c.confidence:.0%}"
                } for c in schema.columns])
                st.dataframe(col_df, use_container_width=True, hide_index=True)
                
                # Generate and offer template download
                st.markdown('#### 📄 Data Template')
                st.markdown('Download an empty CSV template with the same structure for data collection:')
                
                # Save template
                fingerprint = hashlib.md5(json.dumps(sorted([str(c) for c in raw.columns]), sort_keys=True).encode()).hexdigest()[:8]
                try:
                    save_template(schema, fingerprint, 'forecast')
                    template_path = get_current_template(fingerprint)
                    if template_path:
                        template_df = pd.read_csv(template_path)
                        st.download_button('Download Template', template_df.to_csv(index=False).encode(), 'forecast_data_template.csv', 'text/csv')
                except Exception as e:
                    st.info(f'Template generation skipped: {e}')
                
                # Schema evolution tracking for forecast
                st.markdown('#### 📊 Schema Evolution')
                latest_schema = get_latest_schema_version('forecast')
                if latest_schema and latest_schema.fingerprint != fingerprint:
                    st.info('🔄 New schema structure detected!')
                    comparison = compare_schemas(latest_schema.fingerprint, fingerprint)
                    if comparison.get('can_compare'):
                        st.markdown(f"**Previous Version:** {comparison['old_version'][:20]}...")
                        st.markdown(f"**New Version:** {comparison['new_version'][:20]}...")
                        
                        if comparison['added_features']:
                            st.markdown(f"**✅ Added Features ({len(comparison['added_features'])}):** {', '.join(comparison['added_features'][:5])}")
                        if comparison['removed_features']:
                            st.markdown(f"**❌ Removed Features ({len(comparison['removed_features'])}):** {', '.join(comparison['removed_features'][:5])}")
                        if comparison['target_changed']:
                            st.markdown(f"**🎯 Target Changed:** `{comparison['old_target']}` → `{comparison['new_target']}`")
                
                # Initialize force_refresh (will be shown conditionally below)
                force_refresh = False
                
                # Enhance with SLM if available (using cache)
                with st.spinner('🤖 Analyzing schema...'):
                    schema = enhance_schema_with_slm_forecast(raw, rule_based_schema, force_slm=force_refresh, column_meanings=st.session_state.get("forecast_column_meanings", {}))
                
                # Show cache/AI status only if there are saved schemas to compare
                if has_saved_schemas:
                    # Add force refresh option
                    force_refresh = st.checkbox('🔄 Force AI Re-analysis (ignore cache)', value=False, key='force_refresh_forecast')
                    
                    # Show cache status
                    if hasattr(schema, 'from_cache') and schema.from_cache:
                        st.info('⚡ Using cached schema analysis (instant loading)')
                    else:
                        st.info('ℹ️ New schema detected - using AI analysis')
                    
                    # Show SLM status
                    if hasattr(schema, 'slm_reasoning') and schema.slm_reasoning:
                        st.success('✅ Enhanced with AI-powered analysis')
                    else:
                        st.info('ℹ️ Using rule-based analysis (AI unavailable)')
                
                # Let user confirm/modify schema
                st.markdown('#### Confirm Schema')
                # Build every widget option and default from the current uploaded file only.
                column_names = list(dict.fromkeys(str(c.name) for c in schema.columns if str(c.name) in raw.columns))
                suggested_target = schema.suggested_target if schema.suggested_target in column_names else None
                target_options = ([suggested_target] if suggested_target else []) + [c for c in column_names if c != suggested_target]
                if not target_options:
                    st.error('No usable columns were detected in the uploaded file.')
                    st.stop()
                target_col = st.selectbox('Select Target Variable', target_options, index=0, key='forecast_schema_target_column')

                # Build smart defaults for included columns (features)
                feature_options = [c for c in column_names if c != target_col]
                feature_defaults = list(dict.fromkeys(
                    c for c in (schema.suggested_features or []) if c in feature_options
                ))
                
                # If AI didn't suggest many features, add important financial ones as defaults
                important_patterns = ['amount', 'payment', 'invoice', 'due', 'terms', 'credit', 'balance', 'price', 'cost', 'units', 'sales', 'quantity']
                if len(feature_defaults) < 5:  # If AI suggested too few features
                    for col in feature_options:
                        if col not in feature_defaults and any(pattern in col.lower() for pattern in important_patterns):
                            # Exclude data leakage patterns
                            if not any(leakage in col.lower() for leakage in ['clear', 'settle', 'settlement', 'paid_date', 'result', 'outcome']):
                                feature_defaults.append(col)
                
                # Add important date patterns if still too few features
                if len(feature_defaults) < 5:
                    date_patterns = ['due', 'invoice', 'posting', 'create', 'period', 'fiscal', 'year', 'quarter', 'month']
                    for col in feature_options:
                        if col not in feature_defaults and any(pattern in col.lower() for pattern in date_patterns):
                            # Exclude data leakage patterns
                            if not any(leakage in col.lower() for leakage in ['clear', 'settle', 'settlement', 'paid_date', 'result', 'outcome']):
                                feature_defaults.append(col)
                
                # If still too few, add all remaining columns except clear data leakage
                if len(feature_defaults) < 3:
                    for col in feature_options:
                        if col not in feature_defaults:
                            col_lower = col.lower()
                            # Only exclude clear data leakage and IDs
                            if not any(leakage in col_lower for leakage in ['clear', 'settle', 'settlement', 'paid_date', 'result', 'outcome']):
                                if not any(id_pattern in col_lower for id_pattern in ['id', 'key', 'uuid', 'identifier']):
                                    feature_defaults.append(col)
                
                # Complete, exclusive chip-only partition. No third/unassigned pool.
                excluded_options = list(feature_options)
                included_key, excluded_key = _initialize_column_partition('forecast', feature_options, feature_defaults)
                included_assigned = list(st.session_state[included_key])
                excluded_assigned = list(st.session_state[excluded_key])
                feature_cols = st.multiselect('Included Columns (Features)', included_assigned,
                    key=included_key, on_change=_synchronize_column_partition,
                    args=(included_key, excluded_key, feature_options))
                id_cols = st.multiselect('Excluded Columns (IDs, Data Leakage, Low Value)', excluded_assigned,
                    key=excluded_key, on_change=_synchronize_column_partition,
                    args=(excluded_key, included_key, excluded_options))
                st.caption('Column meanings were applied before automatic mapping. Use “Edit column meanings” above to revise them and rerun the mapping.')

                if st.button('Continue to Training', type='primary'):
                    # Update schema based on user selection
                    # Remove overlapping columns from features (IDs take precedence)
                    final_features = [f for f in feature_cols if f not in id_cols]
                    
                    for c in schema.columns:
                        if c.name == target_col:
                            c.suggested_role = 'target'
                        elif c.name in final_features:
                            c.suggested_role = 'feature'
                        elif c.name in id_cols:
                            c.suggested_role = 'id'
                    
                    schema.suggested_target = target_col
                    schema.suggested_features = final_features
                    schema.suggested_ids = id_cols
                    
                    d, validation_result = validate_flexible(raw, schema, training=True)
                    
                    # Store in session state to persist after button click
                    st.session_state.forecast_validated = True
                    st.session_state.forecast_validation_data = d
                    st.session_state.forecast_validation_result = validation_result
                    st.session_state.forecast_schema = schema
                    st.session_state.forecast_column_meanings = column_meanings
                    st.session_state.forecast_raw = raw
                    st.session_state.forecast_training_step = 3
                    st.rerun()
            
            # Step 3: Train
            elif st.session_state.forecast_training_step == 3:
                st.markdown('### Step 3: Train Model')
                
                # If already validated, show training UI
                if st.session_state.get('forecast_validated', False):
                    d = st.session_state.forecast_validation_data
                    validation_result = st.session_state.forecast_validation_result
                    schema = st.session_state.forecast_schema
                    raw = st.session_state.forecast_raw
                    
                    # Show validation results
                    if validation_result['issues']:
                        st.markdown('#### Validation Issues')
                        for issue in validation_result['issues']:
                            level_icon = '⚠️' if issue['level'] == 'warning' else '❌'
                            st.markdown(f"{level_icon} **{issue.get('column', 'General')}:** {issue['message']}")
                    
                    if validation_result['valid']:
                        st.success('✅ Dataset validated successfully!')
                        st.dataframe(d.head(30), use_container_width=True, hide_index=True)
                        
                        # Auto-clean data (temporarily disabled due to type conversion issues)
                        # st.markdown('#### 🔧 Auto Data Cleaning')
                        # d_cleaned, cleaning_report = auto_clean_dataset(d, schema)
                        # if cleaning_report['fixes_applied']:
                        #     st.info(f"**Data cleaning applied:**")
                        #     for fix in cleaning_report['fixes_applied']:
                        #         st.markdown(f"- {fix}")
                        #     st.caption(f"Rows: {cleaning_report['original_rows']:,} → {cleaning_report['final_rows']:,}")
                        # else:
                        #     st.success("✅ No data quality issues detected")
                        d_cleaned = d
                        
                        # Let the administrator choose which forecasting models to train.
                        available_algs = ['Ridge', 'Random Forest', 'Extra Trees',
                                          'Hist Gradient Boosting', 'Gradient Boosting', 'XGBoost']
                        st.markdown('#### Select models to train')
                        st.info('Check one or more algorithms. Only the selected models will be trained and compared.')
                        forecast_model_columns = st.columns(2)
                        algs = []
                        for model_index, model_name in enumerate(available_algs):
                            with forecast_model_columns[model_index % 2]:
                                if st.checkbox(model_name, value=True, key=f'forecast_model_choice_{model_index}'):
                                    algs.append(model_name)
                        if not algs:
                            st.warning('Select at least one model before starting training.')
                        else:
                            st.caption(f'{len(algs)} model(s) selected: ' + ', '.join(algs))

                        if st.button('Train selected models',type='primary',key='btn_train_flex_forecast',disabled=not algs):
                            try:
                                st.write('Starting training...')
                                with st.status('Training flexible schema models…',expanded=True) as s:
                                    st.write('Using auto-detected schema'); st.write('Creating chronological splits')
                                    # For forecast, preprocessing happens inside train_forecast via forecast_features
                                    # Pass target column, but let train_forecast determine features from transformed data
                                    target_col = schema.suggested_target
                                    runs,best=train_forecast(d_cleaned,algs,feature_columns=None,target_column=target_col,column_meanings=st.session_state.get("forecast_column_meanings",{})); st.write('Evaluating holdout data'); 
                                    s.update(label='Flexible training complete',state='complete')
                                st.session_state.forecast_training=(runs,best,validation_result)
                                st.success('Training completed successfully!')
                                st.session_state.forecast_training_step = 4
                                st.rerun()
                            except Exception as train_error:
                                st.error(f'Training failed: {train_error}')
                                import traceback
                                st.error(traceback.format_exc())
                        
                        if st.button('← Back to Schema Selection'):
                            for key in ['forecast_validated', 'forecast_validation_data', 'forecast_validation_result', 'forecast_schema', 'forecast_raw']:
                                if key in st.session_state:
                                    del st.session_state[key]
                            st.session_state.forecast_training_step = 2
                            st.rerun()
            
            # Step 4: Save & Activate
            elif st.session_state.forecast_training_step == 4:
                st.markdown('### Step 4: Save & Activate Model')
                
                if 'forecast_training' in st.session_state:
                    runs,best,q=st.session_state.forecast_training
                    _top1,_top2=st.columns([3,1])
                    with _top1: st.subheader('Model Comparison')
                    with _top2:
                        if st.button('🗑️ Forget training',key='forget_forecast'):
                            del st.session_state.forecast_training
                            st.session_state.forecast_training_step = 3
                            st.rerun()
                    recommendation=recommend_model('forecast',runs,q)
                    recommended_name=recommendation['recommended_algorithm']
                    rows=[]
                    for x in runs:
                        row={'Algorithm':x['algorithm'],'Suggested':x['algorithm']==recommended_name,**x['validation']}
                        rows.append(row)
                    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
                    st.success(f"Suggested model: {recommended_name}. WAPE, RMSE, MAE, R2 and the complete feature contract were considered by {recommendation.get('generator','the ranking engine')}.")
                    st.caption(recommendation.get('reasoning',''))
                    names=[x['algorithm'] for x in runs]
                    selected_name=st.selectbox('Final model selection',names,index=names.index(recommended_name),key='forecast_final_model',help='The suggested model is selected by default. The administrator may choose another model after reviewing the comparison table.')
                    selected=next(x for x in runs if x['algorithm']==selected_name)
                    st.subheader('Selected Model Test Metrics'); show_metrics(selected['test'])
                    ass=interpret('forecast',selected['test'],{**q,'model_comparison':rows,'selection':selected_name,'suggested':recommended_name})
                    render_model_assessment(ass)
                    if st.button('Save & activate selected forecast model',type='primary',key='save_forecast'):
                        try:
                            st.write('Saving model to registry...')
                            vid=reg.save('forecast',selected,q,ass)
                            st.write(f'Created version: {vid}')
                            st.write('Activating model...')
                            reg.activate('forecast',vid)
                            st.success(f'Forecast model {vid} saved and activated.')
                            # Clear all training-related state to go back to initial state
                            for key in ['forecast_training', 'forecast_validated', 'forecast_validation_data', 'forecast_validation_result', 'forecast_schema', 'forecast_raw', 'forecast_file_hash', 'forecast_training_data', 'forecast_training_step']:
                                if key in st.session_state:
                                    del st.session_state[key]
                            st.rerun()
                        except Exception as e:
                            st.error(f'Failed to save/activate model: {e}')
                            import traceback
                            st.error(traceback.format_exc())
            
            # Back button on all steps > 1
            if st.session_state.forecast_training_step > 1:
                if st.button('← Start Over'):
                    for key in ['forecast_training', 'forecast_validated', 'forecast_validation_data', 'forecast_validation_result', 'forecast_schema', 'forecast_raw', 'forecast_file_hash', 'forecast_training_data', 'forecast_training_step']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()

            # Show current active version and history (only when not in training)
            if st.session_state.get('forecast_training_step', 1) == 1:
                st.divider()
                try:
                    _active_model, _active_meta = reg.active('forecast')
                    render_active_model('forecast', _active_meta)
                except (FileNotFoundError, Exception):
                    st.info('No active forecast model yet. Train and save one above.')
                versions=reg.versions('forecast')
                if versions:
                    st.subheader('Saved Versions')
                for v in versions:
                    vid=v['version_id']
                    col1,col2=st.columns([4,1])
                    with col1:
                        st.write(f"**{vid}** — {v.get('algorithm','N/A')} — Trained: {v.get('training_timestamp','N/A')[:19]}")
                    with col2:
                        if st.button('🗑️ Delete',key=f'del_forecast_{vid}'):
                            reg.delete('forecast',vid)
                            st.rerun()

    # ── Page 2: Credit Risk Agent ────────────────────────────────────
    elif page=='Credit Risk Agent':
        title('Agent Testing','Credit Risk Agent','Upload credit data and test the agent. View risk scores, risk tiers, and per-client explanations.')

        try: model,meta=reg.active('credit')
        except:
            st.warning('No active credit model. Train and activate one on Model Training first.'); st.stop()

        st.caption(f"Active model: **{meta['version_id']}** — {meta['algorithm']}")

        # If results exist, show only results (hide upload section)
        if 'credit_agent_results' in st.session_state:
            results = st.session_state.credit_agent_results
            # Handle both old and new session state formats
            if len(results) == 6:
                res, meta, summary, advice, explanations, suggested_search_field = results
            elif len(results) == 5:
                res, meta, summary, advice, explanations = results
                suggested_search_field = suggest_best_search_field(res)
            else:
                res, meta, summary, advice = results
                explanations = []
                suggested_search_field = suggest_best_search_field(res) if res is not None else None

            # Show "New Analysis" button at top
            if st.button('🔄 New Analysis', type='secondary'):
                del st.session_state.credit_agent_results
                st.rerun()

            st.subheader('Risk Overview')
            render_risk_kpis(summary)
            render_analysis_guidance(advice)

            st.subheader('Filter Results')
            
            # AI suggests the best search field
            suggested_search_field = suggest_best_search_field(res)
            
            # Build search field options - all columns available
            search_options = ['All Columns'] + sorted(res.columns)
            
            # Search with field selector
            col1, col2 = st.columns([1, 3])
            with col1:
                # Default to AI-suggested field if available
                default_index = 0  # Default to 'All Columns'
                if suggested_search_field and suggested_search_field in res.columns:
                    try:
                        default_index = search_options.index(suggested_search_field)
                    except ValueError:
                        default_index = 0
                search_field = st.selectbox('Search by', search_options, index=default_index, key='search_field_credit')
            with col2:
                search = st.text_input('Search', key='search_credit', placeholder=f'Search by {search_field}...')
            
            # Risk filter uses explicit checkboxes. All tiers are enabled by default.
            st.markdown('**Risk Filter**')
            low_col, medium_col, high_col, _space = st.columns([0.9, 1.15, 0.9, 7.05], gap='small')
            with low_col:
                include_low = st.checkbox('LOW', value=True, key='risk_filter_credit_low')
            with medium_col:
                include_medium = st.checkbox('MEDIUM', value=True, key='risk_filter_credit_medium')
            with high_col:
                include_high = st.checkbox('HIGH', value=True, key='risk_filter_credit_high')
            selected_risks = [tier for tier, enabled in (
                ('LOW', include_low), ('MEDIUM', include_medium), ('HIGH', include_high)
            ) if enabled]
            filt = res[res['risk_tier'].isin(selected_risks)] if selected_risks else res.iloc[0:0].copy()
            
            # Apply search
            if search:
                if search_field != 'All Columns' and search_field in filt.columns:
                    filt = filt[filt[search_field].astype(str).str.contains(search, case=False, na=False)]
                else:
                    filt = filt[filt.astype(str).apply(lambda r: r.str.contains(search, case=False, na=False).any(), axis=1)]
            
            st.caption(f'{len(filt):,} of {len(res):,} records')
            
            # Display simplified results
            if len(filt) > 0:
                # Create simplified display dataframe
                display_cols = []
                for i, (idx, row) in enumerate(filt.iterrows()):
                    client_id = str(row.get('client_id', idx)) if 'client_id' in row else str(idx)
                    risk_score = round(float(row['risk_score']), 3)
                    risk_tier = row['risk_tier']
                    
                    # Risk status emoji
                    if risk_tier == 'HIGH':
                        status = '⚠️ Risky'
                    elif risk_tier == 'MEDIUM':
                        status = '⚡ Moderate'
                    else:
                        status = '✅ Safe'
                    
                    # Model-grounded local sensitivity factors, optionally wording-reviewed by the SLM.
                    explanation = str(row.get('key_risk_factors', ''))
                    
                    display_cols.append({
                        'Client ID': client_id,
                        'Risk Score': risk_score,
                        'Risk Tier': risk_tier,
                        'Status': status,
                        'Main Prediction Drivers': explanation
                    })
                
                display_df = pd.DataFrame(display_cols)
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Client ID": st.column_config.TextColumn("Client ID", width="medium"),
                        "Risk Score": st.column_config.NumberColumn("Risk Score", format="%.1f%%", width="small"),
                        "Risk Tier": st.column_config.TextColumn("Risk Tier", width="small"),
                        "Status": st.column_config.TextColumn("Status", width="small"),
                        "Main Prediction Drivers": st.column_config.TextColumn(
                            "Main Prediction Drivers",
                            help="The strongest model-grounded factors for this prediction. Each influence is the change in predicted probability when the factor is replaced with its baseline value.",
                            width="large",
                        ),
                    },
                )
            else:
                st.info('No records match your filters.')
            
            # Download buttons
            a, b = st.columns(2)
            a.download_button('Download CSV', filt.to_csv(index=False).encode(), 'credit_risk_results.csv', 'text/csv', use_container_width=True)
            b.download_button('Download Excel', excel_bytes(filt), 'credit_risk_results.xlsx', use_container_width=True)
        
        # If no results, show upload section
        else:
            with st.expander('📋 Active model input structure'):
                render_saved_model_structure(meta,'credit','admin_credit_structure')

            method=st.radio("Client data input method",["Upload customer file","Enter history table"],horizontal=True,key="admin_input_method")
            raw=None
            if method=="Upload customer file":
                f=st.file_uploader("Upload one customer history file (CSV, XLSX, or XLS)",type=['csv','xlsx','xls'],key="agent_credit_upload_v2",help="Use one row per invoice. Add record_type with History or Current to assess only Current rows.")
                if f: raw=read_upload(f)
            else: raw=manual_credit_form(model,meta,"admin_manual")
            if raw is not None:
                try:
                    res,r,summary,d=score_credit(raw,model,meta);report_ui(r)
                    if r.valid:
                        st.dataframe(d.head(20),use_container_width=True,hide_index=True)
                        run=(method=="Enter history table") or st.button("Run Credit Risk Agent",type="primary",key="run_credit_agent_v2")
                        if run:
                            advice=interpret("credit",summary,_as_dict(r));st.session_state.credit_agent_results=(res,meta,summary,advice,[],suggest_best_search_field(res));st.rerun()
                except Exception as e:st.error(f"Error: {e}")
    # ── Page 3: Forecast Agent ───────────────────────────────────────
    elif page=='Forecast Agent':
        # Use native Streamlit elements here so the page remains visible even if
        # custom hero CSS or model metadata is unavailable.
        st.title('Forecast Agent')
        st.caption('Upload demand data and test the active forecast model. View predictions, anomalies, and stockout risks.')

        model = None
        meta = {}
        try:
            model, meta = reg.active('forecast')
        except FileNotFoundError:
            st.warning('No active forecast model is available. Train and activate one from Model Training > Forecast Model.')
        except Exception as exc:
            st.error(f'Unable to load the active forecast model: {exc}')

        if model is None:
            st.info('The Forecast Agent page is working, but analysis is disabled until a forecast model is activated.')
            if st.button('Go to Model Training', key='forecast_go_training'):
                st.session_state['Navigation'] = 'Model Training'
                st.rerun()
            st.stop()

        st.success('Forecast model loaded successfully.')
        st.caption(f"Active model: **{meta.get('version_id', 'Unknown version')}** | {meta.get('algorithm', 'Unknown algorithm')}")

        # If results exist, show only results (hide upload section)
        if 'forecast_agent_results' in st.session_state:
            results = st.session_state.forecast_agent_results
            # Handle both old and new session state formats
            if len(results) == 5:
                res, meta, summary, advice, suggested_search_field = results
            else:
                res, meta, summary, advice = results
                suggested_search_field = suggest_best_search_field(res) if res is not None else None

            # Show "New Analysis" button at top
            if st.button('🔄 New Analysis', type='secondary'):
                del st.session_state.forecast_agent_results
                st.rerun()

            st.subheader('Forecast Overview')
            show_metrics({k:v for k,v in summary.items() if k not in ('anomalies','stockout_risks')})
            a,b=st.columns(2)
            a.metric('⚠️ Anomalies Detected',summary.get('anomalies',0))
            b.metric('📦 Stockout Risks',summary.get('stockout_risks',0))
            render_analysis_guidance(advice)
            render_forecast_alerts(res,meta.get('target'))

            st.subheader('Filter Results')
            
            # AI suggests the best search field
            suggested_search_field = suggest_best_search_field(res)
            
            # Build search field options - all columns available
            search_options = ['All Columns'] + sorted(res.columns)
            
            # Search with field selector
            col1, col2 = st.columns([1, 3])
            with col1:
                # Default to AI-suggested field if available
                default_index = 0  # Default to 'All Columns'
                if suggested_search_field and suggested_search_field in res.columns:
                    try:
                        default_index = search_options.index(suggested_search_field)
                    except ValueError:
                        default_index = 0
                search_field = st.selectbox('Search by', search_options, index=default_index, key='search_field_forecast')
            with col2:
                search = st.text_input('Search', key='search_forecast', placeholder=f'Search by {search_field}...')
            
            stores=sorted(res.store_id.astype(str).unique()) if 'store_id' in res.columns else []
            cats=sorted(res.category.astype(str).unique()) if 'category' in res.columns else []
            sel_stores=st.multiselect('Store',stores,default=stores,key='filter_store') if stores else stores
            sel_cats=st.multiselect('Category',cats,default=cats,key='filter_cat') if cats else cats
            filt=res.copy()
            if sel_stores: filt=filt[filt.store_id.astype(str).isin(sel_stores)]
            if sel_cats: filt=filt[filt.category.astype(str).isin(sel_cats)]
            show_anomalies=st.checkbox('Show anomalies only',key='anomaly_only')
            if show_anomalies: filt=filt[filt.is_anomaly==True]
            if search:
                if search_field != 'All Columns' and search_field in filt.columns:
                    filt = filt[filt[search_field].astype(str).str.contains(search, case=False, na=False)]
                else:
                    filt = filt[filt.astype(str).apply(lambda r:r.str.contains(search, case=False, na=False).any(), axis=1)]
            st.caption(f'{len(filt):,} of {len(res):,} records')
            display_df = filt.head(2000).copy()
            display_df.columns = [str(col) for col in display_df.columns]
            st.dataframe(display_df, use_container_width=True, height=400, hide_index=True)

            a,b=st.columns(2)
            a.download_button('Download CSV',filt.to_csv(index=False).encode(),'forecast_results.csv','text/csv',use_container_width=True)
            b.download_button('Download Excel',excel_bytes(filt),'forecast_results.xlsx',use_container_width=True)
        
        # If no results, show upload section
        else:
            with st.expander('📋 Active model input structure'):
                render_saved_model_structure(meta,'forecast','admin_forecast_structure')

            f=st.file_uploader('Upload forecast data file (CSV, XLSX, or XLS)',type=['csv','xlsx','xls'],key='agent_forecast_upload_v2')
            if f:
                try:
                    raw=read_upload(f); d,r=validate(raw,'forecast',False); report_ui(r)
                    st.dataframe(d.head(20),use_container_width=True,hide_index=True)
                    horizon=st.number_input('Future forecast horizon (days)',min_value=1,max_value=365,value=30,key='admin_forecast_horizon')
                    if r.valid and st.button('Run Forecast Agent',type='primary',key='run_forecast_agent_v2'):
                        progress_container = st.empty()
                        progress_container.info('Running forecast agent…')
                        
                        fd=forecast_features(d)
                        feats=meta.get('features', [])
                        
                        # Fallback: if features not in metadata, use standard forecast features
                        if not feats:
                            from src.services.schemas import FORECAST_FIELDS
                            feats = [f.name for f in FORECAST_FIELDS if f.used]
                            st.warning(f'Using standard forecast features ({len(feats)} columns). Model metadata was missing feature names.')
                        
                        # Ensure columns exist
                        missing_cols = [f for f in feats if f not in fd.columns]
                        if missing_cols:
                            progress_container.error(f'Missing required columns: {missing_cols}')
                            st.stop()
                        
                        pred=np.clip(model.predict(fd[feats]),0,None)
                        res=fd.copy(); res['forecast_units_sold']=pred; res['forecast_value']=pred; res['is_future']=False; res['forecast_mode']=financial_mode(meta.get('target'))
                        res['residual']=res.units_sold-pred
                        sd=max(float(res.residual.std()),1e-9)
                        res['is_anomaly']=res.residual.abs()>2*sd
                        res['stockout_risk']=res.inventory_level<2*pred if 'inventory_level' in res.columns else False
                        summary=regression(res.units_sold,pred)
                        summary['anomalies']=int(res.is_anomaly.sum())
                        summary['stockout_risks']=int(res.stockout_risk.sum()) if 'stockout_risk' in res.columns else 0
                        future=future_projection(fd,model,meta,horizon); res=pd.concat([res,future],ignore_index=True,sort=False)
                        summary['future_periods']=int(len(future)); summary['forecast_mode']=financial_mode(meta.get('target'))
                        advice=interpret('forecast',summary,_as_dict(r))
                        
                        # AI suggests the best search field
                        suggested_search_field = suggest_best_search_field(res)
                        
                        progress_container.success('Forecast complete!')
                        st.session_state.forecast_agent_results=(res,meta,summary,advice,suggested_search_field)
                        st.rerun()
                except Exception as e: st.error(f'Error: {e}')

# ══════════════════════════════════════════════════════════════════════
#  COMPANY PAGES
# ══════════════════════════════════════════════════════════════════════
else:
    ws=Workspace(company)

    # ── Page 1: Credit Risk Analysis ─────────────────────────────────
    if page=='Credit Risk Analysis':
        title('Payment Risk','Credit Risk Analysis','Upload your data, run the credit risk agent trained by the admin, and download risk assessments.')

        try: model,meta=reg.active('credit')
        except:
            st.warning('No credit risk model available yet. Please contact the platform administrator.'); st.stop()

        st.caption(f"Model version: {meta['version_id']}")

        with st.expander('📋 Active model input structure'):
            render_saved_model_structure(meta,'credit','workspace_credit_structure')

        method=st.radio("Client data input method",["Upload customer file","Enter history table"],horizontal=True,key="workspace_input_method")
        raw=None
        if method=="Upload customer file":
            f=st.file_uploader("Upload one customer history file (CSV, XLSX, or XLS)",type=['csv','xlsx','xls'],key="co_credit_upload",help="Use one row per invoice. Add record_type with History or Current to assess only Current rows.")
            if f: raw=read_upload(f)
        else: raw=manual_credit_form(model,meta,"workspace_manual")
        if raw is not None:
            try:
                res,r,summary,d=score_credit(raw,model,meta);report_ui(r)
                if r.valid:
                    st.dataframe(d.head(20),use_container_width=True,hide_index=True)
                    run=(method=="Enter history table") or st.button("Analyze Credit Risk",type="primary",key="co_run_credit")
                    if run:
                        advice=interpret("credit",summary,_as_dict(r));aid=ws.save("credit",d,res,{"model_version":meta["version_id"],"summary":summary,"slm":advice,"input_method":method});st.session_state.co_credit_results=(res,meta,summary,advice,aid);st.rerun()
            except Exception as e:st.error(f"Error: {e}")

        if 'co_credit_results' in st.session_state:
            res,meta,summary,advice,aid=st.session_state.co_credit_results

            st.subheader('Risk Overview')
            render_risk_kpis(summary)
            render_analysis_guidance(advice)

            st.subheader('Filter Results')
            
            # AI suggests the best search field
            suggested_search_field = suggest_best_search_field(res)
            
            # Build stable search field options - all columns available
            search_options = ['All Columns'] + sorted(res.columns)
            
            # Search with field selector
            col1, col2 = st.columns([1, 3])
            with col1:
                # Default to AI-suggested field if available
                default_index = 0  # Default to 'All Columns'
                if suggested_search_field and suggested_search_field in res.columns:
                    try:
                        default_index = search_options.index(suggested_search_field)
                    except ValueError:
                        default_index = 0
                search_field = st.selectbox('Search by', search_options, index=default_index, key='co_search_field_credit')
            with col2:
                search = st.text_input('Search', key='co_search_credit', placeholder=f'Search by {search_field}...')
            
            st.markdown('**Risk Filter**')
            tier_values = {str(value).upper() for value in res.risk_tier.dropna().unique()}
            low_col, medium_col, high_col, _space = st.columns([0.9, 1.15, 0.9, 7.05], gap='small')
            with low_col:
                include_low = st.checkbox('LOW', value=True, disabled='LOW' not in tier_values, key='co_filter_tier_low')
            with medium_col:
                include_medium = st.checkbox('MEDIUM', value=True, disabled='MEDIUM' not in tier_values, key='co_filter_tier_medium')
            with high_col:
                include_high = st.checkbox('HIGH', value=True, disabled='HIGH' not in tier_values, key='co_filter_tier_high')
            tiers = [tier for tier, enabled in (
                ('LOW', include_low), ('MEDIUM', include_medium), ('HIGH', include_high)
            ) if enabled and tier in tier_values]
            lo,hi=st.slider('Risk score range',0.0,1.0,(0.0,1.0),key='co_filter_score')
            
            # Apply search
            if search:
                if search_field != 'All Columns' and search_field in res.columns:
                    filt = res[res[search_field].astype(str).str.contains(search, case=False, na=False)]
                else:
                    filt = res[res.astype(str).apply(lambda r: r.str.contains(search, case=False, na=False).any(), axis=1)]
            else:
                filt = res.copy()
            filt = filt[filt.risk_tier.isin(tiers) & filt.risk_score.between(lo,hi)]
            st.caption(f'{len(filt):,} of {len(res):,} records')
            display_df = filt.head(2000).copy()
            display_df.columns = [str(col) for col in display_df.columns]
            st.dataframe(display_df, use_container_width=True, height=400, hide_index=True)

            a,b,c=st.columns(3)
            a.download_button('Download CSV',filt.to_csv(index=False).encode(),f'{aid}_filtered.csv','text/csv',use_container_width=True)
            b.download_button('Download Excel',excel_bytes(filt),f'{aid}_filtered.xlsx',use_container_width=True)
            report=json.dumps({'analysis_id':aid,'type':'credit','model_version':meta['version_id'],'summary':summary,'recommendations':advice},indent=2,default=str)
            c.download_button('Download Report',report.encode(),f'{aid}_report.json','application/json',use_container_width=True)

        st.divider()
        st.subheader('Recent Analyses')
        hist=ws.history()
        credit_hist=[h for h in hist if h.get('task')=='credit']
        # Clean the history data to remove any objects with _repr_html_ methods
        if credit_hist:
            cleaned_hist=[]
            for h in credit_hist:
                cleaned_h={}
                for k,v in h.items():
                    # Convert any non-serializable objects to strings
                    if hasattr(v, '_repr_html_'):
                        cleaned_h[k]=str(v)
                    elif isinstance(v, (dict, list)):
                        cleaned_h[k]=json.dumps(v, default=str)
                    else:
                        cleaned_h[k]=v
                cleaned_hist.append(cleaned_h)
            st.dataframe(pd.DataFrame(cleaned_hist),use_container_width=True,hide_index=True)
        else:
            st.caption('No previous credit analyses.')

    # ── Page 2: Demand Forecast ──────────────────────────────────────
    elif page=='Demand Forecast':
        title('Demand Planning','Demand Forecast','Upload your data, run the forecast agent trained by the admin, and download predictions.')

        try: model,meta=reg.active('forecast')
        except:
            st.warning('No forecast model available yet. Please contact the platform administrator.'); st.stop()

        st.caption(f"Model version: {meta['version_id']}")

        with st.expander('📋 Active model input structure'):
            render_saved_model_structure(meta,'forecast','workspace_forecast_structure')

        f=st.file_uploader('Upload your forecast data file (CSV, XLSX, or XLS)',type=['csv','xlsx','xls'],key='co_forecast_upload')
        if f:
            try:
                raw=read_upload(f); d,r=validate(raw,'forecast',False); report_ui(r)
                st.dataframe(d.head(20),use_container_width=True,hide_index=True)
                horizon=st.number_input('Future forecast horizon (days)',min_value=1,max_value=365,value=30,key='company_forecast_horizon')
                if r.valid and st.button('Run Forecast',type='primary',key='co_run_forecast'):
                    with st.status('Running forecast analysis…',expanded=True) as s:
                        fd=forecast_features(d)
                        pred=np.clip(model.predict(fd[meta['features']]),0,None)
                        res=fd.copy(); res['forecast_units_sold']=pred; res['forecast_value']=pred; res['is_future']=False; res['forecast_mode']=financial_mode(meta.get('target'))
                        res['residual']=res.units_sold-pred
                        sd=max(float(res.residual.std()),1e-9)
                        res['is_anomaly']=res.residual.abs()>2*sd
                        res['stockout_risk']=res.inventory_level<2*pred if 'inventory_level' in res.columns else False
                        summary=regression(res.units_sold,pred)
                        summary['anomalies']=int(res.is_anomaly.sum())
                        summary['stockout_risks']=int(res.stockout_risk.sum()) if 'stockout_risk' in res.columns else 0
                        future=future_projection(fd,model,meta,horizon); res=pd.concat([res,future],ignore_index=True,sort=False)
                        summary['future_periods']=int(len(future)); summary['forecast_mode']=financial_mode(meta.get('target'))
                        advice=interpret('forecast',summary,_as_dict(r))
                        aid=ws.save('forecast',d,res,{'model_version':meta['version_id'],'summary':summary,'slm':advice})
                        s.update(label='Forecast complete',state='complete')
                    st.session_state.co_forecast_results=(res,meta,summary,advice,aid)
            except Exception as e: st.error(f'Error: {e}')

        if 'co_forecast_results' in st.session_state:
            res,meta,summary,advice,aid=st.session_state.co_forecast_results

            st.subheader('Forecast Overview')
            show_metrics({k:v for k,v in summary.items() if k not in ('anomalies','stockout_risks')})
            a,b=st.columns(2)
            a.metric('⚠️ Anomalies Detected',summary.get('anomalies',0))
            b.metric('📦 Stockout Risks',summary.get('stockout_risks',0))
            render_analysis_guidance(advice)
            render_forecast_alerts(res,meta.get('target'))

            st.subheader('Filter Results')
            
            # AI suggests the best search field
            suggested_search_field = suggest_best_search_field(res)
            
            # Build stable search field options - all columns available
            search_options = ['All Columns'] + sorted(res.columns)
            
            # Search with field selector
            col1, col2 = st.columns([1, 3])
            with col1:
                # Default to AI-suggested field if available
                default_index = 0  # Default to 'All Columns'
                if suggested_search_field and suggested_search_field in res.columns:
                    try:
                        default_index = search_options.index(suggested_search_field)
                    except ValueError:
                        default_index = 0
                search_field = st.selectbox('Search by', search_options, index=default_index, key='co_search_field_forecast')
            with col2:
                search = st.text_input('Search', key='co_search_forecast', placeholder=f'Search by {search_field}...')
            
            stores=sorted(res.store_id.astype(str).unique()) if 'store_id' in res.columns else []
            cats=sorted(res.category.astype(str).unique()) if 'category' in res.columns else []
            sel_stores=st.multiselect('Store',stores,default=stores,key='co_filter_store') if stores else stores
            sel_cats=st.multiselect('Category',cats,default=cats,key='co_filter_cat') if cats else cats
            filt=res.copy()
            if sel_stores: filt=filt[filt.store_id.astype(str).isin(sel_stores)]
            if sel_cats: filt=filt[filt.category.astype(str).isin(sel_cats)]
            show_anomalies=st.checkbox('Show anomalies only',key='co_anomaly_only')
            if show_anomalies: filt=filt[filt.is_anomaly==True]
            
            # Apply search
            if search:
                if search_field != 'All Columns' and search_field in res.columns:
                    filt = filt[filt[search_field].astype(str).str.contains(search, case=False, na=False)]
                else:
                    filt = filt[filt.astype(str).apply(lambda r: r.str.contains(search, case=False, na=False).any(), axis=1)]
            st.caption(f'{len(filt):,} of {len(res):,} records')
            display_df = filt.head(2000).copy()
            display_df.columns = [str(col) for col in display_df.columns]
            st.dataframe(display_df, use_container_width=True, height=400, hide_index=True)

            a,b,c=st.columns(3)
            a.download_button('Download CSV',filt.to_csv(index=False).encode(),f'{aid}_filtered.csv','text/csv',use_container_width=True)
            b.download_button('Download Excel',excel_bytes(filt),f'{aid}_filtered.xlsx',use_container_width=True)
            report=json.dumps({'analysis_id':aid,'type':'forecast','model_version':meta['version_id'],'summary':summary,'recommendations':advice},indent=2,default=str)
            c.download_button('Download Report',report.encode(),f'{aid}_report.json','application/json',use_container_width=True)

        st.divider()
        st.subheader('Recent Analyses')
        hist=ws.history()
        forecast_hist=[h for h in hist if h.get('task')=='forecast']
        if forecast_hist:
            st.dataframe(pd.DataFrame(forecast_hist),use_container_width=True,hide_index=True)
        else:
            st.caption('No previous forecast analyses.')
