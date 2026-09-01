from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
import streamlit as st
from src.services.schema import *
from src.services.training import train_credit, train_forecast
from src.services.model_registry import ModelRegistry
from src.agents.recommender import RecommendationEngine
from src.services.company_profile import CompanyProfileStore
from src.services.auth import credentials_configured, current_user, is_authenticated, sign_in, sign_out

st.set_page_config(page_title="Finance Decision Studio", page_icon="📈", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
:root{--bg:#f2f4f6;--panel:#fbfcfd;--sidebar:#e6eaee;--ink:#17212b;--muted:#667381;--line:#d3d9df;--brand:#315c6d;--brand2:#4f7f82;--good:#267054;--warn:#9a6818;--bad:#a84646}
html,body,[class*="css"]{font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}
.stApp{background:var(--bg);color:var(--ink)}
[data-testid="stHeader"]{background:rgba(242,244,246,.94);border-bottom:1px solid var(--line)}
[data-testid="stSidebar"]{background:var(--sidebar);border-right:1px solid #cbd2d9}
[data-testid="stSidebar"] .block-container{padding:1.35rem 1.1rem 2rem}
.block-container{max-width:1420px;padding:2rem 2.25rem 4rem}
h1{font-size:2rem!important;line-height:1.16!important;letter-spacing:-.035em!important;margin-bottom:.35rem!important}h2{font-size:1.35rem!important;letter-spacing:-.02em!important}h3{font-size:1.05rem!important}.stCaption,p{color:var(--muted)}
/* Do not style BaseWeb popovers globally. Explicit Streamlit light theme controls menus. */
[data-testid="stMetric"]{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:1rem 1.1rem;box-shadow:0 1px 2px rgba(23,33,43,.025)}
[data-testid="stMetricLabel"]{font-size:.74rem;text-transform:uppercase;letter-spacing:.055em;color:var(--muted)}
[data-testid="stMetricValue"]{font-size:1.7rem;color:var(--ink);font-weight:680}
.stButton>button,.stDownloadButton>button{min-height:42px;border-radius:9px;font-weight:650;border:1px solid #bcc6ce;box-shadow:none}
.stButton>button[kind="primary"]{background:var(--brand);border-color:var(--brand);color:#fff}.stButton>button[kind="primary"]:hover{background:#274b59;border-color:#274b59}
.stTextInput input,.stTextArea textarea{background:#fbfcfd!important;border:1px solid #bfc8d0!important;border-radius:9px!important;color:var(--ink)!important}
[data-testid="stFileUploaderDropzone"]{background:var(--panel);border:1px dashed #aeb9c3;border-radius:12px;padding:1rem}
[data-testid="stFileUploaderDropzone"] button{background:#e1e7eb!important;color:#263746!important;border:1px solid #bdc8d0!important}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:10px;overflow:hidden}
div[data-testid="stAlert"]{border-radius:10px;border-width:1px;padding:.8rem 1rem}
[data-testid="stExpander"]{background:var(--panel);border:1px solid var(--line);border-radius:10px}
.hero{background:linear-gradient(135deg,#fbfcfd,#e7edef);border:1px solid var(--line);border-radius:15px;padding:1.45rem 1.6rem;margin-bottom:1.25rem}.hero p{max-width:760px;margin:.35rem 0 0}
.kicker{color:var(--brand2);font-size:.72rem;letter-spacing:.09em;text-transform:uppercase;font-weight:750;margin-bottom:.45rem}
.section-head{display:flex;justify-content:space-between;align-items:end;margin:1.6rem 0 .75rem}.section-head small{color:var(--muted)}
.rule-card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:1.15rem;margin-bottom:.8rem}
[data-testid="stSidebar"] [role="radiogroup"] label{padding:.58rem .65rem;border-radius:8px;margin:.12rem 0}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){background:#d5dee4;color:#17303c}
@media(max-width:900px){.block-container{padding:1.2rem}.hero{padding:1.15rem}}
</style>
""", unsafe_allow_html=True)


# Authentication gate: no workspace data or model controls are shown before login.
def render_login():
    st.markdown('<div class="login-shell"><div class="kicker">Secure access</div><h1>Welcome back</h1><p>Sign in with the administrator account configured in the project environment.</p></div>', unsafe_allow_html=True)
    if not credentials_configured():
        st.error("Administrator credentials are missing. Add ADMIN_USERNAME and ADMIN_PASSWORD to the project .env file, then restart the app.")
        st.stop()
    left, center, right = st.columns([1, 1.2, 1])
    with center:
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Email or administrator username", placeholder="admin@example.com", autocomplete="username")
            password = st.text_input("Password", type="password", autocomplete="current-password")
            submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)
        if submitted:
            if not username.strip() or not password:
                st.warning("Enter both your username and password.")
            elif sign_in(username, password):
                st.rerun()
            else:
                st.error("The username or password is incorrect. Check your .env settings and try again.")
        st.caption("For your security, the session expires automatically after inactivity.")

if not is_authenticated():
    render_login()
    st.stop()

registry=ModelRegistry(); recommender=RecommendationEngine(); profiles=CompanyProfileStore()
st.markdown("""<style>
:root{--ink:#0b1723;--muted:#3f4d5a;--line:#c8d1da;--panel:#ffffff;--brand:#234f62}
.stApp, .stApp p, .stApp label, .stApp span{color:var(--ink)}
.stCaptionContainer p,[data-testid="stCaptionContainer"] p,.stMarkdown p{color:var(--muted)!important}
[data-testid="stSidebar"]{background:#e9eef2!important}
[data-testid="stSidebar"] *{color:#102331!important}
.stTextInput label,.stTextArea label,.stSelectbox label,.stSlider label,.stFileUploader label{font-weight:700!important}
.stButton>button,.stDownloadButton>button{min-height:46px!important}
.login-shell{max-width:680px;margin:5vh auto 1.25rem;background:#fff;border:1px solid var(--line);border-radius:18px;padding:1.8rem 2rem;text-align:center;box-shadow:0 12px 36px rgba(17,38,54,.08)}
.login-shell p{margin:.5rem 0 0!important}
[data-testid="stAlert"] p{color:#17212b!important}
</style>""", unsafe_allow_html=True)

companies=registry.list_companies(); default=companies[0] if companies else "demo_company"
with st.sidebar:
    st.markdown("### Finance Decision Studio")
    st.caption("Governed model operations")
    st.success(f"Signed in as {current_user()}", icon="✅")
    if st.button("Sign out", use_container_width=True):
        sign_out(); st.rerun()
    company=st.text_input("Company workspace",value=default,help="Models and policies are isolated by this ID.").strip()
    st.divider()
    page=st.radio("Navigation",["Dashboard","Analyze credit risk","Analyze demand","Train models","Company policies","Model history","Help"])
    st.divider();st.caption("Secure workspace • Human oversight")

def load_csv(label,key):
    f=st.file_uploader(label,type=["csv"],key=key)
    if not f:return None
    try:return pd.read_csv(f,sep=None,engine="python")
    except Exception as e:st.error(f"Could not read the CSV. {e}");return None

def active(task):
    try:return registry.load_latest(company,task)[1]
    except Exception:return None

def cards(values,names):
    cols=st.columns(len(names))
    for col,name in zip(cols,names):
        value=values.get(name,"Not available")
        if isinstance(value,float):value=f"{value:.3f}"
        col.metric(name.replace("_"," "),value)

def data_summary(df):
    q=quality_report(df);cards(q,["rows","columns","duplicate_rows","missing_cells"])
    with st.expander("Preview uploaded data"):
        st.dataframe(df.head(25),use_container_width=True,hide_index=True)
        st.caption(f"Missing data: {q['missing_percent']:.2f}%")

def mapping(df,fields,key):
    guesses=suggest_mapping(df.columns,fields);result={};choices=[""]+list(df.columns)
    with st.expander("Review field mapping",expanded=True):
        st.caption("Suggested matches are preselected. Every source field can be used only once.")
        a,b=st.columns(2)
        for i,field in enumerate(fields):
            guess=guesses.get(field,"");result[field]=(a if i%2==0 else b).selectbox(field,choices,index=choices.index(guess) if guess in choices else 0,key=f"{key}_{field}")
    errors=mapping_errors(result)
    for error in errors:st.error(error)
    return result,errors

def title(kicker,heading,description):
    st.markdown(f'<div class="kicker">{kicker}</div>',unsafe_allow_html=True);st.title(heading);st.caption(description)

if page=="Dashboard":
    credit,forecast=active("credit"),active("forecast")
    st.markdown(f'<div class="hero"><div class="kicker">Workspace overview</div><h1>{company or "Choose a company"}</h1><p>Build governed models, review operational signals, and translate model output into accountable decisions.</p></div>',unsafe_allow_html=True)
    cards({"companies":len(companies),"credit_model":"Ready" if credit else "Not trained","demand_model":"Ready" if forecast else "Not trained","approval":"Required"},["companies","credit_model","demand_model","approval"])
    st.markdown('<div class="section-head"><h2>Model readiness</h2><small>Active versions and holdout results</small></div>',unsafe_allow_html=True)
    left,right=st.columns(2)
    with left:
        st.markdown('<div class="rule-card"><div class="kicker">Credit</div><h3>Portfolio risk model</h3>',unsafe_allow_html=True)
        if credit:cards(credit.get("metrics",{}),["ROC_AUC","F1_Score","Recall"]);st.caption(f"Active version: {credit.get('version','Unknown')}")
        else:st.info("No active credit model. Use Training to create one.")
        st.markdown('</div>',unsafe_allow_html=True)
    with right:
        st.markdown('<div class="rule-card"><div class="kicker">Demand</div><h3>Historical signal model</h3>',unsafe_allow_html=True)
        if forecast:cards(forecast.get("metrics",{}),["MAE","WAPE","R2"]);st.caption(f"Active version: {forecast.get('version','Unknown')}")
        else:st.info("No active demand model. Use Training to create one.")
        st.markdown('</div>',unsafe_allow_html=True)
    st.warning("Predictions and recommendations are decision support. A responsible employee must review consequential decisions.")

elif page=="Analyze credit risk":
    title("Operational analysis","Credit risk","Upload current customer records. The active saved model runs without retraining.")
    df=load_csv("Customer credit data","credit_predict")
    if df is not None:
        data_summary(df);mp,errs=mapping(df,[CREDIT_ID]+CREDIT_FEATURES,"cp");mapped=apply_mapping(df,mp);validation=validate_credit(mapped,False)
        for e in validation:st.error(e)
        if st.button("Analyze portfolio",type="primary",disabled=bool(errs or validation)):
            try:
                model,_=registry.load_latest(company,"credit");p,tiers=model.predict_risk(mapped);explanations=model.explain(mapped)
                result=pd.DataFrame({CREDIT_ID:mapped[CREDIT_ID].astype(str),"risk_score":p,"risk_tier":tiers})
                result["key_indicators"]=[" • ".join(f"{i['feature']}: {i['relative_position']}" for i in x.get("unusual_indicators",[])) for x in explanations]
                result["recommended_actions"]=[" • ".join(recommender.credit(x)["recommended_actions"]) for x in explanations]
                st.session_state[f"credit_result_{company}"]=result
            except Exception as e:st.error(f"Portfolio analysis failed. {e}")
    result=st.session_state.get(f"credit_result_{company}")
    if result is not None:
        cards({"customers":len(result),"low":int((result.risk_tier=="LOW_RISK").sum()),"medium":int((result.risk_tier=="MEDIUM_RISK").sum()),"high":int((result.risk_tier=="HIGH_RISK").sum())},["customers","low","medium","high"])
        chart,table=st.columns([1,2]);chart.bar_chart(result.risk_tier.value_counts(),height=300);table.dataframe(result,use_container_width=True,hide_index=True,column_config={"risk_score":st.column_config.ProgressColumn("Risk score",min_value=0,max_value=1,format="%.0f%%")})
        st.download_button("Download portfolio report",result.to_csv(index=False).encode(),"credit_portfolio.csv","text/csv")

elif page=="Analyze demand":
    title("Operational analysis","Demand analysis","Evaluate completed historical periods and identify unusual movement or inventory exposure.")
    st.info("This is historical evaluation, not a future multi-step forecast.")
    df=load_csv("Historical demand data","forecast_eval")
    if df is not None:
        data_summary(df);mp,errs=mapping(df,FORECAST_FIELDS,"fe");mapped=apply_mapping(df,mp);validation=validate_forecast(mapped,True)
        for e in validation:st.error(e)
        if st.button("Evaluate signals",type="primary",disabled=bool(errs or validation)):
            try:
                model,_=registry.load_latest(company,"forecast");featured=model.create_features(mapped);met=model.evaluate_featured(featured);result=model.detect_anomalies(mapped);result["recommended_actions"]=[" • ".join(recommender.forecast(row)) for _,row in result.iterrows()];st.session_state[f"forecast_result_{company}"]=(met,result)
            except Exception as e:st.error(f"Demand evaluation failed. {e}")
    saved=st.session_state.get(f"forecast_result_{company}")
    if saved:
        met,result=saved;cards(met,["MAE","RMSE","WAPE","R2"]);st.line_chart(result.groupby("date")[["units_sold","forecast_units_sold"]].sum(),height=320)
        alerts=result[(result.is_anomaly==1)|(result.is_stockout_risk==1)];cards({"anomalies":int(result.is_anomaly.sum()),"stockout_risks":int(result.is_stockout_risk.sum())},["anomalies","stockout_risks"]);st.dataframe(alerts,use_container_width=True,hide_index=True)
        st.download_button("Download demand report",result.to_csv(index=False).encode(),"demand_analysis.csv","text/csv")

elif page=="Train models":
    title("Controlled workflow","Training","Validate data, train on one partition, evaluate on untouched records, and save a version.")
    task=st.radio("Model family",["Credit risk","Demand"],horizontal=True)
    if task=="Credit risk":
        df=load_csv("Labeled credit history","credit_train")
        if df is not None:
            data_summary(df);mp,errs=mapping(df,[CREDIT_ID]+CREDIT_FEATURES+[CREDIT_TARGET],"ct");mapped=apply_mapping(df,mp);validation=validate_credit(mapped,True)
            for e in validation:st.error(e)
            a,b,c=st.columns(3);model_type=a.selectbox("Model",["boosted","baseline"]);review=b.slider("Review threshold",.10,.85,.50,.05);high=c.slider("High-risk threshold",.20,.95,.60,.05)
            if review>high:validation.append("threshold");st.error("Review threshold cannot exceed the high-risk threshold.")
            if st.button("Train credit model",type="primary",disabled=bool(errs or validation)):
                try:
                    with st.status("Training credit model",expanded=True) as s:
                        st.write("Creating stratified holdout");model,met=train_credit(mapped,model_type,review_threshold=review,high_risk_threshold=high);st.write("Saving version");registry.save(company,"credit",model,{"metrics":met,"mapping":mp,"data_summary":quality_report(mapped)});s.update(label="Credit model saved",state="complete")
                    cards(met,["ROC_AUC","PR_AUC","Accuracy","F1_Score","Precision","Recall"])
                except Exception as e:st.error(f"Training failed. {e}")
    else:
        df=load_csv("Historical demand training data","forecast_train")
        if df is not None:
            data_summary(df);mp,errs=mapping(df,FORECAST_FIELDS,"ft");mapped=apply_mapping(df,mp);validation=validate_forecast(mapped,True)
            for e in validation:st.error(e)
            model_type=st.selectbox("Model",["boosted","baseline"],key="forecast_model")
            if st.button("Train demand model",type="primary",disabled=bool(errs or validation)):
                try:
                    with st.status("Training demand model",expanded=True) as s:
                        st.write("Creating chronological holdout");model,met=train_forecast(mapped,model_type);st.write("Saving version");registry.save(company,"forecast",model,{"metrics":met,"mapping":mp,"data_summary":quality_report(mapped)});s.update(label="Demand model saved",state="complete")
                    cards(met,["MAE","RMSE","WAPE","R2"])
                except Exception as e:st.error(f"Training failed. {e}")

elif page=="Company policies":
    title("Governance","Company rules","Personalize recommendations without changing model predictions.")
    profile=profiles.load(company)
    with st.form("company_policy"):
        st.markdown("### Workspace identity")
        left,right=st.columns(2);display=left.text_input("Company display name",profile.display_name,placeholder="Example: North Region Finance");currency=right.text_input("Currency",profile.currency)
        language=left.selectbox("Preferred language",["English","French","Arabic"],index=["English","French","Arabic"].index(profile.language) if profile.language in ["English","French","Arabic"] else 0)
        human=right.checkbox("Require human approval",profile.require_human_approval)
        st.markdown("### Recommendation controls")
        rules=st.text_area("Mandatory rules","\n".join(profile.recommendation_rules),height=115,placeholder="One rule per line")
        blocked=st.text_area("Forbidden action keywords","\n".join(profile.forbidden_actions),height=115,placeholder="One phrase per line")
        submitted=st.form_submit_button("Save company rules",type="primary")
    if submitted:
        profile.display_name=display.strip();profile.currency=currency.strip() or "TND";profile.language=language;profile.require_human_approval=human;profile.recommendation_rules=[x.strip() for x in rules.splitlines() if x.strip()];profile.forbidden_actions=[x.strip() for x in blocked.splitlines() if x.strip()];profiles.save(profile);st.success("Company rules saved.")

elif page=="Model history":
    title("Lifecycle","Model versions","Inspect saved versions and choose the active model for each workflow.")
    for task in ["credit","forecast"]:
        st.markdown(f"### {task.title()}");versions=registry.versions(company,task)
        if not versions:st.info("No saved versions.");continue
        rows=[{"version":v["version"],"saved_at":v["saved_at_utc"],**{k:value for k,value in v.get("metrics",{}).items() if isinstance(value,(int,float,str))}} for v in versions];st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
        chosen=st.selectbox("Activate version",[v["version"] for v in versions],key=f"version_{task}")
        if st.button("Set active",key=f"activate_{task}"):registry.activate(company,task,chosen);st.success("Active model updated.")

else:
    title("Product guide","About","A concise guide to the system boundaries and operating model.")
    st.markdown("""1. Choose a company workspace.  
2. Train with validated historical data.  
3. Review holdout metrics before operational use.  
4. Analyze current records without retraining.  
5. Require human review for consequential recommendations.  
6. Use Model versions to inspect or reactivate prior models.""")
