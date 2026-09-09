from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
import streamlit as st
from src.services.schema import *
from src.services.training import train_credit, train_forecast, compare_credit_augmentation, train_all_credit, train_all_forecast, train_credit_with_optimal_threshold, grid_search_credit, grid_search_forecast
from src.agents.credit_agent import AVAILABLE_CREDIT_MODELS
from src.agents.forecast_agent import AVAILABLE_FORECAST_MODELS
from src.services.model_registry import ModelRegistry
from src.agents.recommender import RecommendationEngine
from src.services.company_profile import CompanyProfileStore
from src.services.auth import credentials_configured, current_user, is_authenticated, sign_in, sign_out
from src.ui.theme import apply_light_theme
from src.ui.components import (
    csv_uploader,
    field_mapping,
    page_header,
    section_head,
    two_columns,
    metric_cards,
    rule_card,
    empty_state,
    result_metrics,
    result_table,
    result_chart,
    download_button,
    status_banner,
)

st.set_page_config(page_title="Finance Decision Studio", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

# ── Theme ──────────────────────────────────────────────────────────────────
apply_light_theme()

# ── Session management ─────────────────────────────────────────────────────
def enforce_session():
    """Redirect to login if session expired."""
    if not is_authenticated():
        st.session_state.clear()
        render_login()
        st.stop()

def clear_old_results():
    """Remove stale per-company result keys on every rerun."""
    keys_to_remove = [k for k in st.session_state.keys() if k.startswith(("credit_result_", "forecast_result_", "credit_training_", "augmentation_"))]
    for k in keys_to_remove:
        del st.session_state[k]


# ── Instances ──────────────────────────────────────────────────────────────
registry = ModelRegistry()
recommender = RecommendationEngine()
profiles = CompanyProfileStore()
company = "admin_company"
registry.company_dir(company, create=True)
profiles.save(profiles.load(company))


# ── Login page ─────────────────────────────────────────────────────────────
def render_login():
    st.markdown(
        """
        <style>
        .login-hero {
            background: linear-gradient(135deg, #1a237e 0%, #283593 40%, #3949ab 100%);
            border-radius: 0 0 24px 24px;
            padding: 3rem 2rem 2.5rem;
            color: white;
            text-align: center;
            margin-bottom: 0;
        }
        .login-hero h1 { color: white !important; font-size: 2.4rem !important; letter-spacing: -.03em !important; margin-bottom: .3rem !important; }
        .login-hero p { color: rgba(255,255,255,.85) !important; font-size: 1.05rem !important; margin: 0 !important; }
        .login-card {
            max-width: 440px; margin: -1.5rem auto 2rem; background: #fff;
            border: 1px solid #e0e4e8; border-radius: 16px; padding: 2rem;
            box-shadow: 0 12px 40px rgba(26,35,126,.12);
        }
        .login-card .stButton > button { width: 100%; background: #1a237e; border-color: #1a237e; color: #fff; font-weight: 700; font-size: 1rem; min-height: 46px; }
        .login-card .stButton > button:hover { background: #283593; border-color: #283593; }
        .login-card .stCaption { color: #78909c; font-size: .85rem; margin-top: .5rem; }
        .login-error { background: #ffebee; border: 1px solid #ef9a9a; border-radius: 10px; padding: .75rem 1rem; color: #b71c1c; font-weight: 600; }
        .login-success { background: #e8f5e9; border: 1px solid #a5d6a7; border-radius: 10px; padding: .75rem 1rem; color: #1b5e20; font-weight: 600; }
        .badge { display: inline-block; background: rgba(255,255,255,.15); border-radius: 20px; padding: .3rem .9rem; font-size: .75rem; letter-spacing: .08em; text-transform: uppercase; color: rgba(255,255,255,.9); margin-bottom: 1rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="login-hero"><div class="badge">🔒 Secure Access</div><h1>Finance Decision Studio</h1><p>Governed credit-risk and demand analysis</p></div>', unsafe_allow_html=True)

    if not credentials_configured():
        st.markdown('<div class="login-error">Administrator credentials are missing. Add ADMIN_USERNAME and ADMIN_PASSWORD to the project .env file, then restart the app.</div>', unsafe_allow_html=True)
        st.stop()

    left, center, right = st.columns([1, 1.4, 1])
    with center:
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Email or administrator username", placeholder="admin@example.com", autocomplete="username")
            password = st.text_input("Password", type="password", autocomplete="current-password")
            submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)
        if submitted:
            if not username.strip() or not password:
                st.markdown('<div class="login-error">Enter both your username and password.</div>', unsafe_allow_html=True)
            elif sign_in(username, password):
                st.markdown('<div class="login-success">✓ Signed in successfully. Redirecting…</div>', unsafe_allow_html=True)
                st.rerun()
            else:
                st.markdown('<div class="login-error">The username or password is incorrect. Check your .env settings and try again.</div>', unsafe_allow_html=True)
        st.caption("For your security, the session expires automatically after inactivity.", unsafe_allow_html=True)

enforce_session()
clear_old_results()


# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📈 Finance Decision Studio")
    st.caption("Admin-controlled platform")
    st.divider()
    page = st.radio("Navigation", ["Dashboard", "Analyze credit risk", "Analyze demand", "Train models", "Company policies", "Model history", "Help"])
    st.divider()
    st.caption("Secure workspace • Human oversight")
    st.markdown("---")
    st.success(f"✅ Signed in as {current_user()}")
    if st.button("📝 Sign Up", use_container_width=True, key="signup_button"):
        st.info("Sign up functionality coming soon. Contact administrator for access.")
    st.markdown("")
    if st.button("🚪 Sign out", use_container_width=True, key="sidebar_sign_out"):
        sign_out()
        st.rerun()


# ── Helpers ────────────────────────────────────────────────────────────────
def active(task):
    try: return registry.load_latest(company, task)[1]
    except Exception: return None

def load_csv(label, key):
    return csv_uploader(label, key)

def cards(values, names):
    metric_cards(values, names)

def data_summary(df):
    q = quality_report(df)
    cards(q, ["rows", "columns", "duplicate_rows", "missing_cells"])
    with st.expander("Preview uploaded data"):
        st.dataframe(df.head(25), use_container_width=True, hide_index=True)
        st.caption(f"Missing data: {q['missing_percent']:.2f}%")

def mapping(df, fields, key):
    return field_mapping(df, fields, key)

def title(kicker, heading, description):
    page_header(kicker, heading, description)


# ── Dashboard ──────────────────────────────────────────────────────────────
if page == "Dashboard":
    credit, forecast = active("credit"), active("forecast")
    page_header("Workspace overview", company or "Choose a company", "Build governed models, review operational signals, and translate model output into accountable decisions.")
    cards({"platform": "Centralized", "credit_model": "Ready" if credit else "Not trained", "demand_model": "Ready" if forecast else "Not trained", "approval": "Required"}, ["platform", "credit_model", "demand_model", "approval"])
    section_head("Model readiness", "Admin-owned platform metrics")
    left, right = two_columns()
    with left:
        rule_card("Credit", "Portfolio risk model")
        if credit:
            cards(credit.get("metrics", {}), ["ROC_AUC", "F1_Score", "Recall"])
            st.caption(f"Active version: {credit.get('version', 'Unknown')}")
        else:
            st.info("No active credit model. Use Training to create one.")
    with right:
        rule_card("Demand", "Historical signal model")
        if forecast:
            cards(forecast.get("metrics", {}), ["MAE", "WAPE", "R2"])
            st.caption(f"Active version: {forecast.get('version', 'Unknown')}")
        else:
            st.info("No active demand model. Use Training to create one.")


# ── Analyze credit risk ────────────────────────────────────────────────────
elif page == "Analyze credit risk":
    title("Operational analysis", "Credit risk", "Upload current customer records. The active saved model runs without retraining.")
    df = load_csv("Customer credit data", "credit_predict")
    if df is not None:
        data_summary(df)
        fields = available_credit_fields(df.columns, False)
        mp, errs = mapping(df, fields, "cp_v4")
        mapped = apply_mapping(df, mp)
        validation = validate_credit(mapped, False)
        for e in validation: st.error(e)
        if st.button("Analyze portfolio", type="primary", disabled=bool(errs or validation)):
            try:
                with st.status("Running portfolio analysis…", expanded=True) as status:
                    model, _ = registry.load_latest(company, "credit")
                    p, tiers = model.predict_risk(mapped)
                    explanations = model.explain(mapped)
                    identifiers = mapped[CREDIT_ID].astype(str) if CREDIT_ID in mapped.columns else mapped.index.astype(str)
                    result = pd.DataFrame({CREDIT_ID: identifiers, "risk_score": p, "risk_tier": tiers})
                    result["key_indicators"] = [" • ".join(f"{i['feature']}: {i['relative_position']}" for i in x.get("unusual_indicators", [])) for x in explanations]
                    result["recommended_actions"] = [" • ".join(recommender.credit(x)["recommended_actions"]) for x in explanations]
                    st.session_state[f"credit_result_{company}"] = result
                    status.update(label="Analysis complete", state="complete")
            except Exception as e:
                st.exception(f"Portfolio analysis failed: {e}")
    result = st.session_state.get(f"credit_result_{company}")
    if result is not None:
        cards({"customers": len(result), "low": int((result.risk_tier == "LOW_RISK").sum()), "medium": int((result.risk_tier == "MEDIUM_RISK").sum()), "high": int((result.risk_tier == "HIGH_RISK").sum())}, ["customers", "low", "medium", "high"])
        chart, table = st.columns([1, 2])
        chart.bar_chart(result.risk_tier.value_counts(), height=300)
        table.dataframe(result, use_container_width=True, hide_index=True, column_config={"risk_score": st.column_config.ProgressColumn("Risk score", min_value=0, max_value=1, format="%.0f%%")})
        st.download_button("Download portfolio report", result.to_csv(index=False).encode(), "credit_portfolio.csv", "text/csv")


# ── Analyze demand ─────────────────────────────────────────────────────────
elif page == "Analyze demand":
    title("Operational analysis", "Demand analysis", "Evaluate completed historical periods and identify unusual movement or inventory exposure.")
    st.info("This is historical evaluation, not a future multi-step forecast.")
    df = load_csv("Historical demand data", "forecast_eval")
    if df is not None:
        data_summary(df)
        mp, errs = mapping(df, FORECAST_FIELDS, "fe")
        mapped = apply_mapping(df, mp)
        validation = validate_forecast(mapped, True)
        for e in validation: st.error(e)
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
        cards(met, ["MAE", "RMSE", "WAPE", "R2"])
        st.line_chart(result.groupby("date")[["units_sold", "forecast_units_sold"]].sum(), height=320)
        alerts = result[(result.is_anomaly == 1) | (result.is_stockout_risk == 1)]
        cards({"anomalies": int(result.is_anomaly.sum()), "stockout_risks": int(result.is_stockout_risk.sum())}, ["anomalies", "stockout_risks"])
        st.dataframe(alerts, use_container_width=True, hide_index=True)
        st.download_button("Download demand report", result.to_csv(index=False).encode(), "demand_analysis.csv", "text/csv")


# ── Train models ───────────────────────────────────────────────────────────
elif page == "Train models":
    title("Controlled workflow", "Training", "Validate data, train on one partition, evaluate on untouched records, and save a version.")
    task = st.radio("Model family", ["Credit risk", "Demand"], horizontal=True)
    if task == "Credit risk":
        df = load_csv("Labeled credit history", "credit_train")
        if df is not None:
            data_summary(df)
            fields = available_credit_fields(df.columns, True)
            mp, errs = mapping(df, fields, "ct_v4")
            mapped = apply_mapping(df, mp)
            validation = validate_credit(mapped, True)
            for e in validation: st.error(e)
            auto_select = st.checkbox("Train all models and auto-select the best", value=False, help="Trains every available credit model and picks the highest composite score.")
            optimize_threshold = st.checkbox("Auto-optimize review threshold for F1+PR-AUC", value=False, help="Sweeps thresholds on the untouched holdout to find the one maximizing F1 score.")
            if not auto_select:
                a, b, c = st.columns(3)
                model_type = a.selectbox("Model", sorted(AVAILABLE_CREDIT_MODELS), help="XGBoost and LightGBM are recommended for tabular data; alternatives remain for benchmarking.")
                review = b.slider("Review threshold", .10, .85, .50, .05)
                high = c.slider("High-risk threshold", .20, .95, .60, .05)
                if review > high:
                    validation.append("threshold")
                    st.error("Review threshold cannot exceed the high-risk threshold.")
                if st.button("Train credit model", type="primary", disabled=bool(errs or validation)):
                    try:
                        with st.status("Training credit model", expanded=True) as status:
                            if optimize_threshold:
                                st.write("Training with automatic threshold optimization")
                                model, met = train_credit_with_optimal_threshold(mapped, model_type, hyperparams=None)
                            else:
                                model, met = train_credit(mapped, model_type, review_threshold=review, high_risk_threshold=high)
                            st.write("Saving version")
                            registry.save(company, "credit", model, {"metrics": met, "mapping": mp, "data_summary": quality_report(mapped), "experiment": "baseline"})
                            status.update(label="Model saved", state="complete")
                        st.session_state[f"credit_training_{company}"] = (mapped, mp, model_type, review, high, met)
                        st.success("✅ Credit model trained and saved!")
                    except Exception as e:
                        st.exception(f"Training failed: {e}")
                trained = st.session_state.get(f"credit_training_{company}")
                if trained:
                    source, stored_mapping, stored_type, stored_review, stored_high, met = trained
                    cards(met, ["ROC_AUC", "PR_AUC", "Accuracy", "F1_Score", "Precision", "Recall", "Brier_Score"])
                    st.caption(f"Untouched holdout: {met.get('test_rows')} rows · Default prevalence: {met.get('default_prevalence', 0):.1%} · False negatives: {met.get('false_negatives')}")
                    st.markdown("### Controlled data augmentation experiment")
                    st.info("Augmentation affects only the training partition. The exact same untouched holdout is used before and after, so the comparison is fair.")
                    x, y = st.columns(2)
                    target_ratio = x.slider("Minority-to-majority target ratio", .30, 1.00, .75, .05, help="Adds minority-class training examples until this ratio is reached.")
                    jitter = y.slider("Continuous-value variation", 0.0, .10, .025, .005, help="Small scale-aware variation applied only to continuous monetary fields.")
                    if st.button("Run augmentation comparison", disabled=bool(errs or validation)):
                        try:
                            with st.status("Comparing on the same holdout", expanded=True) as status:
                                st.write("Training baseline")
                                result = compare_credit_augmentation(source, stored_type, review_threshold=stored_review, high_risk_threshold=stored_high, target_ratio=target_ratio, jitter=jitter)
                                st.write("Training augmented challenger")
                                status.update(label="Comparison complete", state="complete")
                            st.session_state[f"augmentation_{company}"] = result
                            st.success("✅ Augmentation comparison complete!")
                        except Exception as e:
                            st.exception(f"Augmentation experiment failed: {e}")
                    experiment = st.session_state.get(f"augmentation_{company}")
                    if experiment:
                        comparison = pd.DataFrame(experiment["comparison"])
                        st.dataframe(comparison, use_container_width=True, hide_index=True)
                        meta = experiment["augmentation"]
                        st.caption(f"Synthetic training rows: {meta['synthetic_rows']} · Training rows after augmentation: {meta['augmented_rows']} · Holdout unchanged")
                        choice = experiment["recommended"]
                        if choice == "augmented":
                            st.success("The augmented challenger improved the weighted validation objective without materially reducing recall.")
                        else:
                            st.warning("Augmentation did not provide a reliable improvement. Keep the non-augmented baseline.")
                        if st.button(f"Save recommended {choice} model", type="primary"):
                            selected = experiment["augmented_model"] if choice == "augmented" else experiment["baseline_model"]
                            selected_metrics = experiment["augmented_metrics"] if choice == "augmented" else experiment["baseline_metrics"]
                            selected_metrics.update({"model_type": stored_type, "augmentation": meta if choice == "augmented" else {"synthetic_rows": 0}, "selection": "same-holdout challenger comparison"})
                            registry.save(company, "credit", selected, {"metrics": selected_metrics, "mapping": stored_mapping, "data_summary": quality_report(source), "experiment": choice})
                            st.success("Recommended model version saved and activated.")
            else:
                st.markdown("### Hyperparameters for each model (override defaults)")
                hp_cols = st.columns(len(AVAILABLE_CREDIT_MODELS))
                hp_map = {}
                for mt, col in zip(sorted(AVAILABLE_CREDIT_MODELS), hp_cols):
                    with col.expander(f"{mt} params", expanded=False):
                        if mt == "xgboost":
                            n_est = col.number_input("n_estimators", 100, 2000, 650, key=f"hp_{mt}_n")
                            md = col.number_input("max_depth", 2, 12, 4, key=f"hp_{mt}_d")
                            lr = col.number_input("learning_rate", 0.005, 0.3, 0.03, format="%.3f", key=f"hp_{mt}_lr")
                            mcw = col.number_input("min_child_weight", 1, 20, 4, key=f"hp_{mt}_mcw")
                            sub = col.number_input("subsample", 0.5, 1.0, 0.85, format="%.2f", key=f"hp_{mt}_sub")
                            ctb = col.number_input("colsample_bytree", 0.5, 1.0, 0.85, format="%.2f", key=f"hp_{mt}_ctb")
                            hp_map[mt] = {"n_estimators": n_est, "max_depth": md, "learning_rate": lr, "min_child_weight": mcw, "subsample": sub, "colsample_bytree": ctb}
                        elif mt == "lightgbm":
                            n_est = col.number_input("n_estimators", 100, 2000, 600, key=f"hp_{mt}_n")
                            md = col.number_input("max_depth", 2, 12, 6, key=f"hp_{mt}_d")
                            lr = col.number_input("learning_rate", 0.005, 0.3, 0.03, format="%.3f", key=f"hp_{mt}_lr")
                            nl = col.number_input("num_leaves", 8, 128, 31, key=f"hp_{mt}_nl")
                            mcs = col.number_input("min_child_samples", 5, 100, 20, key=f"hp_{mt}_mcs")
                            hp_map[mt] = {"n_estimators": n_est, "max_depth": md, "learning_rate": lr, "num_leaves": nl, "min_child_samples": mcs}
                        elif mt == "boosted":
                            mi = col.number_input("max_iter", 50, 1000, 350, key=f"hp_{mt}_mi")
                            lr = col.number_input("learning_rate", 0.005, 0.3, 0.035, format="%.3f", key=f"hp_{mt}_lr")
                            md = col.number_input("max_depth", 2, 12, 6, key=f"hp_{mt}_d")
                            l2 = col.number_input("l2_regularization", 0.0, 10.0, 1.0, key=f"hp_{mt}_l2")
                            hp_map[mt] = {"max_iter": mi, "learning_rate": lr, "max_depth": md, "l2_regularization": l2}
                        elif mt in ("randomforest", "extra_trees"):
                            n_est = col.number_input("n_estimators", 50, 1500, 500, key=f"hp_{mt}_n")
                            md = col.number_input("max_depth", 3, 30, 12, key=f"hp_{mt}_d")
                            ms = col.number_input("min_samples_split", 2, 20, 5, key=f"hp_{mt}_ms")
                            ml = col.number_input("min_samples_leaf", 1, 10, 2, key=f"hp_{mt}_ml")
                            hp_map[mt] = {"n_estimators": n_est, "max_depth": md, "min_samples_split": ms, "min_samples_leaf": ml}
                        elif mt == "baseline":
                            mi = col.number_input("max_iter", 100, 5000, 2500, key=f"hp_{mt}_mi")
                            hp_map[mt] = {"max_iter": mi}
                review_h = st.slider("Review threshold (all models)", .10, .85, .50, .05, "review_all")
                high_h = st.slider("High-risk threshold (all models)", .20, .95, .60, .05, "high_all")
                optimize_thr = st.checkbox("Auto-optimize threshold for each model", value=False, key="opt_thr_all", help="Sweeps thresholds per model to maximize F1+PR-AUC.")
                if review_h > high_h:
                    validation.append("threshold")
                    st.error("Review threshold cannot exceed the high-risk threshold.")
                if st.button("Train all models and select the best", type="primary", disabled=bool(errs or validation)):
                    try:
                        with st.status("Training all credit models", expanded=True) as status:
                            model, met, best_name, all_metrics = train_all_credit(mapped, review_threshold=review_h, high_risk_threshold=high_h, hyperparams_map=hp_map, auto_threshold=optimize_thr)
                            status.update(label=f"Best model: {best_name}", state="complete")
                        st.session_state[f"credit_training_{company}"] = (mapped, mp, best_name, review_h, high_h, met)
                        st.success(f"✅ All models trained! Best: **{best_name}**")
                        with st.expander("All model comparison"):
                            comp_rows = []
                            for name, m in all_metrics.items():
                                if "error" in m: comp_rows.append({"model": name, "status": "Failed", "ROC_AUC": "-", "PR_AUC": "-", "F1_Score": "-", "Recall": "-", "Brier_Score": "-"})
                                else: comp_rows.append({"model": name, "ROC_AUC": m.get("ROC_AUC", 0), "PR_AUC": m.get("PR_AUC", 0), "F1_Score": m.get("F1_Score", 0), "Recall": m.get("Recall", 0), "Brier_Score": m.get("Brier_Score", 0), "threshold": m.get("threshold", "-")})
                            st.dataframe(pd.DataFrame(comp_rows), use_container_width=True, hide_index=True)
                            st.success(f"Auto-selected best model: **{best_name}** with ROC-AUC {met.get('ROC_AUC', 0):.4f}, PR-AUC {met.get('PR_AUC', 0):.4f}, F1 {met.get('F1_Score', 0):.4f}, optimal threshold {met.get('threshold', '-')}")
                    except Exception as e:
                        st.exception(f"Training all models failed: {e}")
                    if st.button("Grid search all models (find best params)", type="primary", disabled=bool(errs or validation)):
                        try:
                            with st.status("Running grid search across all models", expanded=True) as status:
                                top_results, all_ranked = grid_search_credit(mapped)
                                status.update(label="Grid search complete", state="complete")
                            with st.expander("Grid search results (top 5)"):
                                gs_rows = []
                                for name, m in all_ranked:
                                    gs_rows.append({"model": name, "F1": m.get("F1_Score", 0), "PR_AUC": m.get("PR_AUC", 0), "ROC_AUC": m.get("ROC_AUC", 0), "Recall": m.get("Recall", 0), "Brier": m.get("Brier_Score", 0), "grid_size": m.get("grid_size", "-"), "best_params": str(m.get("best_params", {}))[:120]})
                                st.dataframe(pd.DataFrame(gs_rows), use_container_width=True, hide_index=True)
                                best_gs = all_ranked[0]
                                st.success(f"Grid search best: **{best_gs[0]}** with F1 {best_gs[1].get('F1_Score', 0):.4f} | Use 'Train all' with this model type and hyperparams: {best_gs[1].get('best_params', {})}")
                        except Exception as e:
                            st.exception(f"Grid search failed: {e}")
    else:
        df = load_csv("Historical demand training data", "forecast_train")
        if df is not None:
            data_summary(df)
            mp, errs = mapping(df, FORECAST_FIELDS, "ft")
            mapped = apply_mapping(df, mp)
            validation = validate_forecast(mapped, True)
            for e in validation: st.error(e)
            auto_select = st.checkbox("Train all models and auto-select the best", value=False, key="fc_auto", help="Trains every available forecast model and picks the highest composite score.")
            if not auto_select:
                model_type = st.selectbox("Model", sorted(AVAILABLE_FORECAST_MODELS), key="forecast_model")
                if st.button("Train demand model", type="primary", disabled=bool(errs or validation)):
                    try:
                        with st.status("Training demand model", expanded=True) as s:
                            st.write("Creating chronological holdout")
                            model, met = train_forecast(mapped, model_type)
                            st.write("Saving version")
                            registry.save(company, "forecast", model, {"metrics": met, "mapping": mp, "data_summary": quality_report(mapped)})
                            s.update(label="Demand model saved", state="complete")
                        cards(met, ["MAE", "RMSE", "WAPE", "R2"])
                        st.success("✅ Demand model trained and saved!")
                    except Exception as e:
                        st.exception(f"Training failed: {e}")
            else:
                st.markdown("### Hyperparameters for each model (override defaults)")
                hp_cols = st.columns(len(AVAILABLE_FORECAST_MODELS))
                hp_map = {}
                for mt, col in zip(sorted(AVAILABLE_FORECAST_MODELS), hp_cols):
                    with col.expander(f"{mt} params", expanded=False):
                        if mt == "lightgbm":
                            n_est = col.number_input("n_estimators", 100, 2000, 500, key=f"fc_{mt}_n")
                            md = col.number_input("max_depth", 2, 12, 6, key=f"fc_{mt}_d")
                            lr = col.number_input("learning_rate", 0.005, 0.3, 0.03, format="%.3f", key=f"fc_{mt}_lr")
                            nl = col.number_input("num_leaves", 8, 128, 31, key=f"fc_{mt}_nl")
                            mcs = col.number_input("min_child_samples", 5, 100, 20, key=f"fc_{mt}_mcs")
                            hp_map[mt] = {"n_estimators": n_est, "max_depth": md, "learning_rate": lr, "num_leaves": nl, "min_child_samples": mcs}
                        elif mt == "boosted":
                            mi = col.number_input("max_iter", 50, 1000, 300, key=f"fc_{mt}_mi")
                            lr = col.number_input("learning_rate", 0.005, 0.3, 0.04, format="%.3f", key=f"fc_{mt}_lr")
                            md = col.number_input("max_depth", 2, 12, 7, key=f"fc_{mt}_d")
                            l2 = col.number_input("l2_regularization", 0.0, 10.0, 1.0, key=f"fc_{mt}_l2")
                            hp_map[mt] = {"max_iter": mi, "learning_rate": lr, "max_depth": md, "l2_regularization": l2}
                        elif mt == "randomforest":
                            n_est = col.number_input("n_estimators", 50, 1500, 500, key=f"fc_{mt}_n")
                            md = col.number_input("max_depth", 3, 30, 15, key=f"fc_{mt}_d")
                            ms = col.number_input("min_samples_split", 2, 20, 5, key=f"fc_{mt}_ms")
                            ml = col.number_input("min_samples_leaf", 1, 10, 2, key=f"fc_{mt}_ml")
                            hp_map[mt] = {"n_estimators": n_est, "max_depth": md, "min_samples_split": ms, "min_samples_leaf": ml}
                        elif mt == "baseline":
                            mi = col.number_input("alpha", 0.01, 100.0, 1.0, format="%.2f", key=f"fc_{mt}_a")
                            hp_map[mt] = {"alpha": mi}
                if st.button("Train all forecast models and select the best", type="primary", disabled=bool(errs or validation)):
                    try:
                        with st.status("Training all forecast models", expanded=True) as status:
                            model, met, best_name, all_metrics = train_all_forecast(mapped, hyperparams_map=hp_map)
                            status.update(label=f"Best model: {best_name}", state="complete")
                        cards(met, ["MAE", "RMSE", "WAPE", "R2"])
                        st.success(f"✅ All forecast models trained! Best: **{best_name}**")
                        with st.expander("All model comparison"):
                            comp_rows = []
                            for name, m in all_metrics.items():
                                if "error" in m: comp_rows.append({"model": name, "status": "Failed", "MAE": "-", "RMSE": "-", "R2": "-", "WAPE": "-"})
                                else: comp_rows.append({"model": name, "MAE": m.get("MAE", 0), "RMSE": m.get("RMSE", 0), "R2": m.get("R2", 0), "WAPE": m.get("WAPE", 0)})
                            st.dataframe(pd.DataFrame(comp_rows), use_container_width=True, hide_index=True)
                            st.success(f"Auto-selected best model: **{best_name}** with R2 {met.get('R2', 0):.4f}, MAE {met.get('MAE', 0):.4f}, RMSE {met.get('RMSE', 0):.4f}")
                    except Exception as e:
                        st.exception(f"Training all forecast models failed: {e}")
                    if st.button("Grid search all forecast models", type="primary", disabled=bool(errs or validation)):
                        try:
                            with st.status("Running forecast grid search", expanded=True) as status:
                                top_results, all_ranked = grid_search_forecast(mapped)
                                status.update(label="Forecast grid search complete", state="complete")
                            with st.expander("Forecast grid search results"):
                                gs_rows = []
                                for name, m in all_ranked:
                                    gs_rows.append({"model": name, "R2": m.get("R2", 0), "MAE": m.get("MAE", 0), "RMSE": m.get("RMSE", 0), "grid_size": m.get("grid_size", "-"), "best_params": str(m.get("best_params", {}))[:120]})
                                st.dataframe(pd.DataFrame(gs_rows), use_container_width=True, hide_index=True)
                                best_gs = all_ranked[0]
                                st.success(f"Forecast grid search best: **{best_gs[0]}** with R2 {best_gs[1].get('R2', 0):.4f}")
                        except Exception as e:
                            st.exception(f"Forecast grid search failed: {e}")


# ── Company policies ───────────────────────────────────────────────────────
elif page == "Company policies":
    title("Governance", "Company rules", "Personalize recommendations without changing model predictions.")
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


# ── Model history ──────────────────────────────────────────────────────────
elif page == "Model history":
    title("Lifecycle", "Model versions", "Inspect saved versions and choose the active model for each workflow.")
    for task in ["credit", "forecast"]:
        st.markdown(f"### {task.title()}")
        versions = registry.versions(company, task)
        if not versions:
            st.info("No saved versions.")
            continue
        rows = [{"version": v["version"], "saved_at": v["saved_at_utc"], **{k: value for k, value in v.get("metrics", {}).items() if isinstance(value, (int, float, str))}} for v in versions]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        chosen = st.selectbox("Activate version", [v["version"] for v in versions], key=f"version_{task}")
        if st.button("Set active", key=f"activate_{task}"):
            registry.activate(company, task, chosen)
            st.success("Active model updated.")


# ── Help ───────────────────────────────────────────────────────────────────
else:
    title("Product guide", "About", "A concise guide to the system boundaries and operating model.")
    st.markdown("""1. Choose a company workspace.
2. Train with validated historical data.
3. Review holdout metrics before operational use.
4. Analyze current records without retraining.
5. Require human review for consequential recommendations.
6. Use Model versions to inspect or reactivate prior models.""")
