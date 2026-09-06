import io,os,json
from pathlib import Path
import pandas as pd, numpy as np, streamlit as st
from src.config import MAX_UPLOAD_MB
from src.services.auth import verify,signup,create_session,validate_session,destroy_session
from src.services.schemas import template,documentation,normalize,CREDIT_FIELDS,FORECAST_FIELDS
from src.services.validation import validate
from src.services.modeling import train_credit,train_forecast,forecast_features
from src.services.registry import Registry
from src.services.intelligence import interpret
from src.services.metrics import regression,classification
from src.services.workspace import Workspace
from src.agents.credit_agent import CreditRiskAgent
from src.agents.forecast_agent import CashflowForecastAgent

st.set_page_config(page_title='ML Intelligence Center',page_icon='◆',layout='wide')
st.markdown('''<style>:root{--ink:#14212b;--muted:#64727e;--brand:#23566b;--line:#dce3e8;--bg:#f5f7f8}.stApp{background:var(--bg)}.block-container{max-width:1480px;padding:4rem 2.4rem 4rem}h1,h2,h3{color:var(--ink);letter-spacing:-.025em}.stCaption,p{color:var(--muted)}[data-testid=stSidebar]{background:#eaf0f3;border-right:1px solid var(--line)}[data-testid=stMetric]{background:white;border:1px solid var(--line);border-radius:14px;padding:1rem}.stButton>button,.stDownloadButton>button{border-radius:9px;min-height:42px;font-weight:650}.hero{background:white;border:1px solid var(--line);border-radius:18px;padding:1.5rem 1.7rem;margin-bottom:1rem}.k{font-size:.72rem;text-transform:uppercase;letter-spacing:.1em;color:var(--brand);font-weight:800}.good{color:#176b50}.warn{color:#95621b}.bad{color:#a63c3c}</style>''',unsafe_allow_html=True)

reg=Registry()

# ── Helpers ──────────────────────────────────────────────────────────
def title(k,h,d):
    st.markdown(f'<div class="hero"><div class="k">{k}</div><h1>{h}</h1><p>{d}</p></div>',unsafe_allow_html=True)

def show_metrics(m):
    keys=[k for k,v in m.items() if isinstance(v,(int,float)) and not isinstance(v,bool)][:8]
    if not keys: return
    for c,k in zip(st.columns(min(4,len(keys))),keys[:4]):
        c.metric(k,'N/A' if m[k] is None else f"{m[k]:.3f}")
    if len(keys)>4:
        for c,k in zip(st.columns(min(4,len(keys)-4)),keys[4:8]):
            c.metric(k,'N/A' if m[k] is None else f"{m[k]:.3f}")

def read_upload(f):
    if f.size>MAX_UPLOAD_MB*1024*1024: raise ValueError(f'File exceeds {MAX_UPLOAD_MB} MB.')
    try: return pd.read_csv(f,sep=None,engine='python')
    except UnicodeDecodeError: f.seek(0); return pd.read_csv(f,encoding='latin-1')

def report_ui(r):
    a,b,c,d=st.columns(4)
    a.metric('Rows',r.rows); b.metric('Columns',r.columns); c.metric('Duplicates',r.duplicates); d.metric('Missing cells',r.missing_cells)
    for i in r.issues: (st.error if i.level=='error' else st.warning)(i.message)

def excel_bytes(df):
    b=io.BytesIO()
    with pd.ExcelWriter(b,engine='openpyxl') as w: df.to_excel(w,index=False,sheet_name='Results')
    return b.getvalue()

# ── Session restore from token ───────────────────────────────────────
if 'user' not in st.session_state:
    token=st.query_params.get('session')
    if token:
        restored=validate_session(token)
        if restored:
            st.session_state.user=restored
            st.session_state.session_token=token

# ── Login ────────────────────────────────────────────────────────────
def login():
    st.markdown('<div class="hero"><div class="k">Secure analytics platform</div><h1>ML Intelligence Center</h1><p>Administrators train models and test agents. Companies run analyses through approved agents.</p></div>',unsafe_allow_html=True)
    a,b=st.tabs(['Sign in','Create company account'])
    with a:
        with st.form('login'):
            e=st.text_input('Email'); p=st.text_input('Password',type='password'); go=st.form_submit_button('Sign in',type='primary')
        if go:
            u=verify(e,p)
            if u:
                token=create_session(u['email'])
                st.session_state.user=u
                st.session_state.session_token=token
                st.query_params['session']=token
                st.rerun()
            else: st.error('Invalid credentials or inactive account.')
    with b:
        with st.form('signup'):
            c=st.text_input('Company name'); n=st.text_input('Your name'); e=st.text_input('Work email'); p=st.text_input('Password',type='password'); go=st.form_submit_button('Create workspace')
        if go:
            ok,msg=signup(c,n,e,p); (st.success if ok else st.error)(msg)

if 'user' not in st.session_state: login(); st.stop()
u=st.session_state.user; role=u['role']; company=u['company_id']

# ── Sidebar ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('## ◆ Intelligence Center')
    st.caption('Model operations' if role=='admin' else 'Business analysis workspace')
    st.write(f"**{u['name']}**"); st.caption(u['email'])
    if role=='admin':
        pages=['Model Training','Credit Risk Agent','Forecast Agent']
    else:
        pages=['Credit Risk Analysis','Demand Forecast']
    page=st.radio('Navigation',pages)
    if st.button('Sign out',use_container_width=True):
        destroy_session(st.session_state.get('session_token'))
        st.session_state.clear()
        st.query_params.clear()
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
            fs=st.file_uploader('Upload credit training CSV',type='csv',accept_multiple_files=True,key='train_credit')
            if fs:
                frames=[]
                try:
                    for f in fs: frames.append(read_upload(f))
                    base=set(frames[0].columns)
                    if any(set(x.columns)!=base for x in frames[1:]): st.error('Files have different columns. Training blocked.'); st.stop()
                    raw=pd.concat(frames,ignore_index=True); d,r=validate(raw,'credit',True); report_ui(r); st.dataframe(d.head(30),use_container_width=True,hide_index=True)
                    algs=st.multiselect('Algorithms',['Logistic Regression','Random Forest','XGBoost'],default=['Logistic Regression','XGBoost'],key='alg_credit')
                    if st.button('Train credit models',type='primary',disabled=not(r.valid and algs),key='btn_train_credit'):
                        with st.status('Training credit models…',expanded=True) as s:
                            st.write('Validated dataset'); st.write('Creating train/validation/test splits')
                            runs,best=train_credit(d,algs); st.write('Evaluating holdout data'); s.update(label='Credit training complete',state='complete')
                        st.session_state.credit_training=(runs,best,r.dict())
                except Exception as e: st.error(f'Training failed: {e}')

            if 'credit_training' in st.session_state:
                runs,best,q=st.session_state.credit_training
                _top1,_top2=st.columns([3,1])
                with _top1: st.subheader('Model Comparison')
                with _top2:
                    if st.button('🗑️ Forget training',key='forget_credit'):
                        del st.session_state.credit_training; st.rerun()
                rows=[{'Algorithm':x['algorithm'],**x['validation']} for x in runs]
                st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
                st.success(f"Recommended: {best['algorithm']} (selected by validation PR-AUC then F1)")
                st.subheader('Test Metrics'); show_metrics(best['test'])
                ass=interpret('credit',best['test'],q); st.info(ass['executive_summary'])
                st.write('**Strengths:**')
                for x in ass['strengths']: st.write(f'- {x}')
                st.write('**Weaknesses:**')
                for x in ass['weaknesses']: st.write(f'- {x}')
                st.write('**Recommendations:**')
                for x in ass['recommendations']: st.write(f'- {x}')
                st.caption(f"Generated by {ass['generator']}. {ass['human_review_notice']}")
                if st.button('Save & activate credit model',type='primary',key='save_credit'):
                    vid=reg.save('credit',best,q,ass); reg.activate('credit',vid)
                    st.success(f'Credit model {vid} saved and activated.')

            # Show current active version and history
            st.divider()
            st.subheader('Active Model')
            try:
                _,meta=reg.active('credit')
                st.success(f"✅ Active credit model: **{meta['version_id']}** — {meta['algorithm']}")
            except: st.warning('⚠️ No active credit model yet. Train a model above and save it.')
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
            fs=st.file_uploader('Upload forecast training CSV',type='csv',accept_multiple_files=True,key='train_forecast')
            if fs:
                frames=[]
                try:
                    for f in fs: frames.append(read_upload(f))
                    base=set(frames[0].columns)
                    if any(set(x.columns)!=base for x in frames[1:]): st.error('Files have different columns. Training blocked.'); st.stop()
                    raw=pd.concat(frames,ignore_index=True); d,r=validate(raw,'forecast',True); report_ui(r); st.dataframe(d.head(30),use_container_width=True,hide_index=True)
                    algs=st.multiselect('Algorithms',['Ridge','Random Forest','XGBoost'],default=['Ridge','XGBoost'],key='alg_forecast')
                    if st.button('Train forecast models',type='primary',disabled=not(r.valid and algs),key='btn_train_forecast'):
                        with st.status('Training forecast models…',expanded=True) as s:
                            st.write('Validated dataset'); st.write('Creating chronological splits')
                            runs,best=train_forecast(d,algs); st.write('Evaluating holdout data'); s.update(label='Forecast training complete',state='complete')
                        st.session_state.forecast_training=(runs,best,r.dict())
                except Exception as e: st.error(f'Training failed: {e}')

            if 'forecast_training' in st.session_state:
                runs,best,q=st.session_state.forecast_training
                _top1,_top2=st.columns([3,1])
                with _top1: st.subheader('Model Comparison')
                with _top2:
                    if st.button('🗑️ Forget training',key='forget_forecast'):
                        del st.session_state.forecast_training; st.rerun()
                rows=[{'Algorithm':x['algorithm'],**x['validation']} for x in runs]
                st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
                st.success(f"Recommended: {best['algorithm']} (lowest validation WAPE)")
                st.subheader('Test Metrics'); show_metrics(best['test'])
                ass=interpret('forecast',best['test'],q); st.info(ass['executive_summary'])
                st.write('**Strengths:**'); 
                for x in ass['strengths']: st.write(f'- {x}')
                st.write('**Weaknesses:**')
                for x in ass['weaknesses']: st.write(f'- {x}')
                st.write('**Recommendations:**')
                for x in ass['recommendations']: st.write(f'- {x}')
                st.caption(f"Generated by {ass['generator']}. {ass['human_review_notice']}")
                if st.button('Save & activate forecast model',type='primary',key='save_forecast'):
                    vid=reg.save('forecast',best,q,ass); reg.activate('forecast',vid)
                    st.success(f'Forecast model {vid} saved and activated.')

            st.divider()
            st.subheader('Active Model')
            try:
                _,meta=reg.active('forecast')
                st.success(f"✅ Active forecast model: **{meta['version_id']}** — {meta['algorithm']}")
            except: st.warning('⚠️ No active forecast model yet. Train a model above and save it.')
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

        with st.expander('📋 Download template & field docs'):
            st.download_button('Download credit template',template('credit').to_csv(index=False).encode(),'credit_risk_template.csv','text/csv')
            st.dataframe(documentation('credit'),use_container_width=True,hide_index=True)

        f=st.file_uploader('Upload credit data CSV',type='csv',key='agent_credit_upload')
        if f:
            try:
                raw=read_upload(f); d,r=validate(raw,'credit',False); report_ui(r)
                st.dataframe(d.head(20),use_container_width=True,hide_index=True)
                if r.valid and st.button('Run Credit Risk Agent',type='primary',key='run_credit_agent'):
                    with st.status('Running credit risk agent…',expanded=True) as s:
                        agent=CreditRiskAgent(model_type='xgboost')
                        # Use the active pipeline model directly for predictions
                        feats=meta['features']
                        proba=model.predict_proba(d[feats].apply(pd.to_numeric,errors='coerce'))[:,1]
                        tier=np.where(proba>=.65,'HIGH',np.where(proba>=.35,'MEDIUM','LOW'))
                        res=d.copy(); res['risk_score']=proba; res['risk_tier']=tier
                        summary={'average_risk':float(proba.mean()),'high_risk':int((tier=='HIGH').sum()),'medium_risk':int((tier=='MEDIUM').sum()),'low_risk':int((tier=='LOW').sum()),'total_records':len(d)}
                        advice=interpret('credit',summary,r.dict())
                        s.update(label='Analysis complete',state='complete')
                    st.session_state.credit_agent_results=(res,meta,summary,advice)
            except Exception as e: st.error(f'Error: {e}')

        if 'credit_agent_results' in st.session_state:
            res,meta,summary,advice=st.session_state.credit_agent_results

            st.subheader('Risk Overview')
            a,b,c,d=st.columns(4)
            a.metric('Total Records',summary['total_records'])
            b.metric('🔴 High Risk',summary['high_risk'])
            c.metric('🟡 Medium Risk',summary['medium_risk'])
            d.metric('🟢 Low Risk',summary['low_risk'])
            st.metric('Average Risk Score',f"{summary['average_risk']:.3f}")

            st.subheader('Decision Support')
            st.info(advice['executive_summary'])
            st.write('**Recommendations:**')
            for i,x in enumerate(advice['recommendations']): st.write(f'{i+1}. {x}')
            st.caption(f"Generated by {advice['generator']}. {advice['human_review_notice']}")

            st.subheader('Filter Results')
            search=st.text_input('Search',key='search_credit')
            tiers=st.multiselect('Risk tier',sorted(res.risk_tier.unique()),default=sorted(res.risk_tier.unique()),key='filter_tier')
            lo,hi=st.slider('Risk score range',0.0,1.0,(0.0,1.0),key='filter_score')
            filt=res[res.risk_tier.isin(tiers) & res.risk_score.between(lo,hi)]
            if search: filt=filt[filt.astype(str).apply(lambda r:r.str.contains(search,case=False,na=False).any(),axis=1)]
            st.caption(f'{len(filt):,} of {len(res):,} records')
            st.dataframe(filt.head(2000),use_container_width=True,hide_index=True)

            a,b=st.columns(2)
            a.download_button('Download CSV',filt.to_csv(index=False).encode(),'credit_risk_results.csv','text/csv',use_container_width=True)
            b.download_button('Download Excel',excel_bytes(filt),'credit_risk_results.xlsx',use_container_width=True)

    # ── Page 3: Forecast Agent ───────────────────────────────────────
    elif page=='Forecast Agent':
        title('Agent Testing','Forecast Agent','Upload demand data and test the forecast agent. View predictions, anomalies, and stockout risks.')

        try: model,meta=reg.active('forecast')
        except:
            st.warning('No active forecast model. Train and activate one on Model Training first.'); st.stop()

        st.caption(f"Active model: **{meta['version_id']}** — {meta['algorithm']}")

        with st.expander('📋 Download template & field docs'):
            st.download_button('Download forecast template',template('forecast').to_csv(index=False).encode(),'demand_forecast_template.csv','text/csv')
            st.dataframe(documentation('forecast'),use_container_width=True,hide_index=True)

        f=st.file_uploader('Upload forecast data CSV',type='csv',key='agent_forecast_upload')
        if f:
            try:
                raw=read_upload(f); d,r=validate(raw,'forecast',False); report_ui(r)
                st.dataframe(d.head(20),use_container_width=True,hide_index=True)
                if r.valid and st.button('Run Forecast Agent',type='primary',key='run_forecast_agent'):
                    with st.status('Running forecast agent…',expanded=True) as s:
                        fd=forecast_features(d)
                        pred=np.clip(model.predict(fd[meta['features']]),0,None)
                        res=fd.copy(); res['forecast_units_sold']=pred
                        res['residual']=res.units_sold-pred
                        sd=max(float(res.residual.std()),1e-9)
                        res['is_anomaly']=res.residual.abs()>2*sd
                        res['stockout_risk']=res.inventory_level<2*pred if 'inventory_level' in res.columns else False
                        summary=regression(res.units_sold,pred)
                        summary['anomalies']=int(res.is_anomaly.sum())
                        summary['stockout_risks']=int(res.stockout_risk.sum()) if 'stockout_risk' in res.columns else 0
                        advice=interpret('forecast',summary,r.dict())
                        s.update(label='Forecast complete',state='complete')
                    st.session_state.forecast_agent_results=(res,meta,summary,advice)
            except Exception as e: st.error(f'Error: {e}')

        if 'forecast_agent_results' in st.session_state:
            res,meta,summary,advice=st.session_state.forecast_agent_results

            st.subheader('Forecast Overview')
            show_metrics({k:v for k,v in summary.items() if k not in ('anomalies','stockout_risks')})
            a,b=st.columns(2)
            a.metric('⚠️ Anomalies Detected',summary.get('anomalies',0))
            b.metric('📦 Stockout Risks',summary.get('stockout_risks',0))

            st.subheader('Decision Support')
            st.info(advice['executive_summary'])
            st.write('**Recommendations:**')
            for i,x in enumerate(advice['recommendations']): st.write(f'{i+1}. {x}')
            st.caption(f"Generated by {advice['generator']}. {advice['human_review_notice']}")

            st.subheader('Filter Results')
            search=st.text_input('Search',key='search_forecast')
            stores=sorted(res.store_id.astype(str).unique()) if 'store_id' in res.columns else []
            cats=sorted(res.category.astype(str).unique()) if 'category' in res.columns else []
            sel_stores=st.multiselect('Store',stores,default=stores,key='filter_store') if stores else stores
            sel_cats=st.multiselect('Category',cats,default=cats,key='filter_cat') if cats else cats
            filt=res.copy()
            if sel_stores: filt=filt[filt.store_id.astype(str).isin(sel_stores)]
            if sel_cats: filt=filt[filt.category.astype(str).isin(sel_cats)]
            show_anomalies=st.checkbox('Show anomalies only',key='anomaly_only')
            if show_anomalies: filt=filt[filt.is_anomaly==True]
            if search: filt=filt[filt.astype(str).apply(lambda r:r.str.contains(search,case=False,na=False).any(),axis=1)]
            st.caption(f'{len(filt):,} of {len(res):,} records')
            st.dataframe(filt.head(2000),use_container_width=True,hide_index=True)

            a,b=st.columns(2)
            a.download_button('Download CSV',filt.to_csv(index=False).encode(),'forecast_results.csv','text/csv',use_container_width=True)
            b.download_button('Download Excel',excel_bytes(filt),'forecast_results.xlsx',use_container_width=True)

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

        with st.expander('📋 Download template & field documentation'):
            st.download_button('Download credit template',template('credit').to_csv(index=False).encode(),'credit_risk_template.csv','text/csv',key='co_credit_tpl')
            st.dataframe(documentation('credit'),use_container_width=True,hide_index=True)

        f=st.file_uploader('Upload your credit data CSV',type='csv',key='co_credit_upload')
        if f:
            try:
                raw=read_upload(f); d,r=validate(raw,'credit',False); report_ui(r)
                st.dataframe(d.head(20),use_container_width=True,hide_index=True)
                if r.valid and st.button('Analyze Credit Risk',type='primary',key='co_run_credit'):
                    with st.status('Running credit risk analysis…',expanded=True) as s:
                        feats=meta['features']
                        proba=model.predict_proba(d[feats].apply(pd.to_numeric,errors='coerce'))[:,1]
                        tier=np.where(proba>=.65,'HIGH',np.where(proba>=.35,'MEDIUM','LOW'))
                        res=d.copy(); res['risk_score']=proba; res['risk_tier']=tier
                        summary={'average_risk':float(proba.mean()),'high_risk':int((tier=='HIGH').sum()),'medium_risk':int((tier=='MEDIUM').sum()),'low_risk':int((tier=='LOW').sum()),'total_records':len(d)}
                        advice=interpret('credit',summary,r.dict())
                        aid=ws.save('credit',d,res,{'model_version':meta['version_id'],'summary':summary,'slm':advice})
                        s.update(label='Analysis complete',state='complete')
                    st.session_state.co_credit_results=(res,meta,summary,advice,aid)
            except Exception as e: st.error(f'Error: {e}')

        if 'co_credit_results' in st.session_state:
            res,meta,summary,advice,aid=st.session_state.co_credit_results

            st.subheader('Risk Overview')
            a,b,c,d=st.columns(4)
            a.metric('Total Records',summary['total_records'])
            b.metric('🔴 High Risk',summary['high_risk'])
            c.metric('🟡 Medium Risk',summary['medium_risk'])
            d.metric('🟢 Low Risk',summary['low_risk'])

            st.subheader('Decision Support')
            st.info(advice['executive_summary'])
            st.write('**Recommendations:**')
            for i,x in enumerate(advice['recommendations']): st.write(f'{i+1}. {x}')
            st.caption(f"Generated by {advice['generator']}. {advice['human_review_notice']}")

            st.subheader('Filter Results')
            search=st.text_input('Search',key='co_search_credit')
            tiers=st.multiselect('Risk tier',sorted(res.risk_tier.unique()),default=sorted(res.risk_tier.unique()),key='co_filter_tier')
            lo,hi=st.slider('Risk score range',0.0,1.0,(0.0,1.0),key='co_filter_score')
            filt=res[res.risk_tier.isin(tiers) & res.risk_score.between(lo,hi)]
            if search: filt=filt[filt.astype(str).apply(lambda r:r.str.contains(search,case=False,na=False).any(),axis=1)]
            st.caption(f'{len(filt):,} of {len(res):,} records')
            st.dataframe(filt.head(2000),use_container_width=True,hide_index=True)

            a,b,c=st.columns(3)
            a.download_button('Download CSV',filt.to_csv(index=False).encode(),f'{aid}_filtered.csv','text/csv',use_container_width=True)
            b.download_button('Download Excel',excel_bytes(filt),f'{aid}_filtered.xlsx',use_container_width=True)
            report=json.dumps({'analysis_id':aid,'type':'credit','model_version':meta['version_id'],'summary':summary,'recommendations':advice},indent=2,default=str)
            c.download_button('Download Report',report.encode(),f'{aid}_report.json','application/json',use_container_width=True)

        st.divider()
        st.subheader('Recent Analyses')
        hist=ws.history()
        credit_hist=[h for h in hist if h.get('task')=='credit']
        st.dataframe(pd.DataFrame(credit_hist),use_container_width=True,hide_index=True) if credit_hist else st.caption('No previous credit analyses.')

    # ── Page 2: Demand Forecast ──────────────────────────────────────
    elif page=='Demand Forecast':
        title('Demand Planning','Demand Forecast','Upload your data, run the forecast agent trained by the admin, and download predictions.')

        try: model,meta=reg.active('forecast')
        except:
            st.warning('No forecast model available yet. Please contact the platform administrator.'); st.stop()

        st.caption(f"Model version: {meta['version_id']}")

        with st.expander('📋 Download template & field documentation'):
            st.download_button('Download forecast template',template('forecast').to_csv(index=False).encode(),'demand_forecast_template.csv','text/csv',key='co_forecast_tpl')
            st.dataframe(documentation('forecast'),use_container_width=True,hide_index=True)

        f=st.file_uploader('Upload your forecast data CSV',type='csv',key='co_forecast_upload')
        if f:
            try:
                raw=read_upload(f); d,r=validate(raw,'forecast',False); report_ui(r)
                st.dataframe(d.head(20),use_container_width=True,hide_index=True)
                if r.valid and st.button('Run Forecast',type='primary',key='co_run_forecast'):
                    with st.status('Running forecast analysis…',expanded=True) as s:
                        fd=forecast_features(d)
                        pred=np.clip(model.predict(fd[meta['features']]),0,None)
                        res=fd.copy(); res['forecast_units_sold']=pred
                        res['residual']=res.units_sold-pred
                        sd=max(float(res.residual.std()),1e-9)
                        res['is_anomaly']=res.residual.abs()>2*sd
                        res['stockout_risk']=res.inventory_level<2*pred if 'inventory_level' in res.columns else False
                        summary=regression(res.units_sold,pred)
                        summary['anomalies']=int(res.is_anomaly.sum())
                        summary['stockout_risks']=int(res.stockout_risk.sum()) if 'stockout_risk' in res.columns else 0
                        advice=interpret('forecast',summary,r.dict())
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

            st.subheader('Decision Support')
            st.info(advice['executive_summary'])
            st.write('**Recommendations:**')
            for i,x in enumerate(advice['recommendations']): st.write(f'{i+1}. {x}')
            st.caption(f"Generated by {advice['generator']}. {advice['human_review_notice']}")

            st.subheader('Filter Results')
            search=st.text_input('Search',key='co_search_forecast')
            stores=sorted(res.store_id.astype(str).unique()) if 'store_id' in res.columns else []
            cats=sorted(res.category.astype(str).unique()) if 'category' in res.columns else []
            sel_stores=st.multiselect('Store',stores,default=stores,key='co_filter_store') if stores else stores
            sel_cats=st.multiselect('Category',cats,default=cats,key='co_filter_cat') if cats else cats
            filt=res.copy()
            if sel_stores: filt=filt[filt.store_id.astype(str).isin(sel_stores)]
            if sel_cats: filt=filt[filt.category.astype(str).isin(sel_cats)]
            show_anomalies=st.checkbox('Show anomalies only',key='co_anomaly_only')
            if show_anomalies: filt=filt[filt.is_anomaly==True]
            if search: filt=filt[filt.astype(str).apply(lambda r:r.str.contains(search,case=False,na=False).any(),axis=1)]
            st.caption(f'{len(filt):,} of {len(res):,} records')
            st.dataframe(filt.head(2000),use_container_width=True,hide_index=True)

            a,b,c=st.columns(3)
            a.download_button('Download CSV',filt.to_csv(index=False).encode(),f'{aid}_filtered.csv','text/csv',use_container_width=True)
            b.download_button('Download Excel',excel_bytes(filt),f'{aid}_filtered.xlsx',use_container_width=True)
            report=json.dumps({'analysis_id':aid,'type':'forecast','model_version':meta['version_id'],'summary':summary,'recommendations':advice},indent=2,default=str)
            c.download_button('Download Report',report.encode(),f'{aid}_report.json','application/json',use_container_width=True)

        st.divider()
        st.subheader('Recent Analyses')
        hist=ws.history()
        forecast_hist=[h for h in hist if h.get('task')=='forecast']
        st.dataframe(pd.DataFrame(forecast_hist),use_container_width=True,hide_index=True) if forecast_hist else st.caption('No previous forecast analyses.')
