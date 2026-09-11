from __future__ import annotations

import pandas as pd
import streamlit as st

from src.services.schema import (
    FORECAST_FIELDS,
    available_credit_fields,
    apply_mapping,
    validate_credit,
    validate_forecast,
    quality_report,
)
from src.services.audit import log_event, AuditEvent
from src.services.auth import current_user, current_role
from src.services.training import (
    train_credit,
    train_forecast,
    compare_credit_augmentation,
    train_all_credit,
    train_all_forecast,
    train_credit_with_optimal_threshold,
    grid_search_credit,
    grid_search_forecast,
)
from src.agents.credit_agent import AVAILABLE_CREDIT_MODELS
from src.agents.forecast_agent import AVAILABLE_FORECAST_MODELS
from src.ui.components.fields import csv_uploader, field_mapping
from src.ui.components.display import metric_cards


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _data_summary(df: pd.DataFrame) -> None:
    """Render a quality summary card row and a preview expander."""
    q = quality_report(df)
    metric_cards(q, ["rows", "columns", "duplicate_rows", "missing_cells"])
    with st.expander("Preview uploaded data"):
        st.dataframe(df.head(25), use_container_width=True, hide_index=True)
        st.caption(f"Missing data: {q['missing_percent']:.2f}%")


def _credit_hyperparams() -> dict:
    """Render per-model hyperparameter override expanders for credit models."""
    hp_cols = st.columns(len(AVAILABLE_CREDIT_MODELS))
    hp_map: dict = {}
    for mt, col in zip(sorted(AVAILABLE_CREDIT_MODELS), hp_cols):
        with col.expander(f"{mt} params", expanded=False):
            if mt == "xgboost":
                n_est = col.number_input("n_estimators", 100, 2000, 650, key=f"hp_{mt}_n")
                md = col.number_input("max_depth", 2, 12, 4, key=f"hp_{mt}_d")
                lr = col.number_input("learning_rate", 0.005, 0.3, 0.03, format="%.3f", key=f"hp_{mt}_lr")
                mcw = col.number_input("min_child_weight", 1, 20, 4, key=f"hp_{mt}_mcw")
                sub = col.number_input("subsample", 0.5, 1.0, 0.85, format="%.2f", key=f"hp_{mt}_sub")
                ctb = col.number_input("colsample_bytree", 0.5, 1.0, 0.85, format="%.2f", key=f"hp_{mt}_ctb")
                hp_map[mt] = {"n_estimators": n_est, "max_depth": md, "learning_rate": lr,
                              "min_child_weight": mcw, "subsample": sub, "colsample_bytree": ctb}
            elif mt == "lightgbm":
                n_est = col.number_input("n_estimators", 100, 2000, 600, key=f"hp_{mt}_n")
                md = col.number_input("max_depth", 2, 12, 6, key=f"hp_{mt}_d")
                lr = col.number_input("learning_rate", 0.005, 0.3, 0.03, format="%.3f", key=f"hp_{mt}_lr")
                nl = col.number_input("num_leaves", 8, 128, 31, key=f"hp_{mt}_nl")
                mcs = col.number_input("min_child_samples", 5, 100, 20, key=f"hp_{mt}_mcs")
                hp_map[mt] = {"n_estimators": n_est, "max_depth": md, "learning_rate": lr,
                              "num_leaves": nl, "min_child_samples": mcs}
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
                hp_map[mt] = {"n_estimators": n_est, "max_depth": md,
                              "min_samples_split": ms, "min_samples_leaf": ml}
            elif mt == "baseline":
                mi = col.number_input("max_iter", 100, 5000, 2500, key=f"hp_{mt}_mi")
                hp_map[mt] = {"max_iter": mi}
    return hp_map


def _forecast_hyperparams() -> dict:
    """Render per-model hyperparameter override expanders for forecast models."""
    hp_cols = st.columns(len(AVAILABLE_FORECAST_MODELS))
    hp_map: dict = {}
    for mt, col in zip(sorted(AVAILABLE_FORECAST_MODELS), hp_cols):
        with col.expander(f"{mt} params", expanded=False):
            if mt == "lightgbm":
                n_est = col.number_input("n_estimators", 100, 2000, 500, key=f"fc_{mt}_n")
                md = col.number_input("max_depth", 2, 12, 6, key=f"fc_{mt}_d")
                lr = col.number_input("learning_rate", 0.005, 0.3, 0.03, format="%.3f", key=f"fc_{mt}_lr")
                nl = col.number_input("num_leaves", 8, 128, 31, key=f"fc_{mt}_nl")
                mcs = col.number_input("min_child_samples", 5, 100, 20, key=f"fc_{mt}_mcs")
                hp_map[mt] = {"n_estimators": n_est, "max_depth": md, "learning_rate": lr,
                              "num_leaves": nl, "min_child_samples": mcs}
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
                hp_map[mt] = {"n_estimators": n_est, "max_depth": md,
                              "min_samples_split": ms, "min_samples_leaf": ml}
            elif mt == "baseline":
                mi = col.number_input("alpha", 0.01, 100.0, 1.0, format="%.2f", key=f"fc_{mt}_a")
                hp_map[mt] = {"alpha": mi}
    return hp_map


# ---------------------------------------------------------------------------
# Credit risk training
# ---------------------------------------------------------------------------

def _render_credit_training(registry, mapped: pd.DataFrame, mp: dict, errs: list, validation: list, company: str) -> None:
    """Render the credit risk training sub-section."""

    auto_select = st.checkbox(
        "Train all models and auto-select the best",
        value=False,
        help="Trains every available credit model and picks the highest composite score.",
    )
    optimize_threshold = st.checkbox(
        "Auto-optimize review threshold for F1+PR-AUC",
        value=False,
        help="Sweeps thresholds on the untouched holdout to find the one maximizing F1 score.",
    )

    if not auto_select:
        _render_single_credit(registry, mapped, mp, errs, validation, company, optimize_threshold)
    else:
        _render_all_credit(registry, mapped, mp, errs, validation, company)


def _render_single_credit(
    registry, mapped: pd.DataFrame, mp: dict, errs: list, validation: list,
    company: str, optimize_threshold: bool,
) -> None:
    """Single-model credit training flow."""
    a, b, c = st.columns(3)
    model_type = a.selectbox(
        "Model",
        sorted(AVAILABLE_CREDIT_MODELS),
        help="XGBoost and LightGBM are recommended for tabular data. "
        "Random Forest and Extra Trees are more interpretable but may have lower accuracy.",
    )
    review = b.slider(
        "Review threshold", 0.10, 0.85, 0.50, 0.05,
        help="Risk scores at or above this value are flagged for human review. "
        "Lower values flag more records for review (higher recall, more manual work).",
    )
    high = c.slider(
        "High-risk threshold", 0.20, 0.95, 0.60, 0.05,
        help="Risk scores at or above this value are classified as HIGH_RISK. "
        "Must be higher than the review threshold.",
    )

    if review > high:
        validation.append("threshold")
        st.error("Review threshold cannot exceed the high-risk threshold.")

    if st.button(
        "Train credit model",
        type="primary",
        disabled=bool(errs or validation),
        help="Trains the selected algorithm on the training split and evaluates on the "
        "untouched holdout. The trained model is saved as a new version.",
    ):
        try:
            with st.status("Training credit model", expanded=True) as status:
                if optimize_threshold:
                    st.write("Training with automatic threshold optimization")
                    model, met = train_credit_with_optimal_threshold(mapped, model_type, hyperparams=None)
                else:
                    model, met = train_credit(mapped, model_type,
                                              review_threshold=review, high_risk_threshold=high)
                st.write("Saving version")
                registry.save(company, "credit", model, {
                    "metrics": met, "mapping": mp,
                    "data_summary": quality_report(mapped), "experiment": "baseline",
                })
                log_event(
                    AuditEvent.MODEL_TRAIN,
                    username=current_user(), role=current_role(), company_id=company,
                    detail={"task": "credit", "model_type": model_type, "experiment": "baseline"},
                )
                status.update(label="Model saved", state="complete")
            st.session_state[f"credit_training_{company}"] = (mapped, mp, model_type, review, high, met)
            st.success("Credit model trained and saved!")
        except Exception as e:
            st.error(f"Training failed: {e}")

    trained = st.session_state.get(f"credit_training_{company}")
    if trained is None:
        return

    source, stored_mapping, stored_type, stored_review, stored_high, met = trained
    metric_cards(met, ["ROC_AUC", "PR_AUC", "Accuracy", "F1_Score", "Precision", "Recall", "Brier_Score"])
    st.caption(
        f"Untouched holdout: {met.get('test_rows')} rows "
        f"| Default prevalence: {met.get('default_prevalence', 0):.1%} "
        f"| False negatives: {met.get('false_negatives')}"
    )

    # -- Augmentation experiment ---------------------------------------------
    st.markdown("### Controlled data augmentation experiment")
    st.caption(
        "Synthetic minority-class examples are generated and added to the training partition. "
        "A baseline model (no augmentation) and an augmented challenger are both evaluated on "
        "the same untouched holdout, so the comparison is fair and the holdout is never modified."
    )
    x, y = st.columns(2)
    target_ratio = x.slider(
        "Minority-to-majority target ratio", 0.30, 1.00, 0.75, 0.05,
        help="Adds minority-class training examples until this ratio is reached.",
    )
    jitter = y.slider(
        "Continuous-value variation", 0.0, 0.10, 0.025, 0.005,
        help="Small scale-aware variation applied only to continuous monetary fields.",
    )

    if st.button("Run augmentation comparison", disabled=bool(errs or validation)):
        try:
            with st.status("Comparing on the same holdout", expanded=True) as status:
                st.write("Training baseline")
                result = compare_credit_augmentation(
                    source, stored_type,
                    review_threshold=stored_review,
                    high_risk_threshold=stored_high,
                    target_ratio=target_ratio,
                    jitter=jitter,
                )
                st.write("Training augmented challenger")
                status.update(label="Comparison complete", state="complete")
            st.session_state[f"augmentation_{company}"] = result
            st.success("Augmentation comparison complete!")
        except Exception as e:
            st.error(f"Augmentation experiment failed: {e}")

    experiment = st.session_state.get(f"augmentation_{company}")
    if experiment is None:
        return

    comparison = pd.DataFrame(experiment["comparison"])
    st.dataframe(comparison, use_container_width=True, hide_index=True)
    meta = experiment["augmentation"]
    st.caption(
        f"Synthetic training rows: {meta['synthetic_rows']} "
        f"| Training rows after augmentation: {meta['augmented_rows']} "
        f"| Holdout unchanged"
    )

    choice = experiment["recommended"]
    if choice == "augmented":
        st.success(
            "The augmented challenger improved the weighted validation objective "
            "without materially reducing recall."
        )
    else:
        st.warning(
            "Augmentation did not provide a reliable improvement. "
            "Keep the non-augmented baseline."
        )

    if st.button(f"Save recommended {choice} model", type="primary"):
        selected = experiment["augmented_model"] if choice == "augmented" else experiment["baseline_model"]
        selected_metrics = experiment["augmented_metrics"] if choice == "augmented" else experiment["baseline_metrics"]
        selected_metrics.update({
            "model_type": stored_type,
            "augmentation": meta if choice == "augmented" else {"synthetic_rows": 0},
            "selection": "same-holdout challenger comparison",
        })
        registry.save(company, "credit", selected, {
            "metrics": selected_metrics, "mapping": stored_mapping,
            "data_summary": quality_report(source), "experiment": choice,
        })
        log_event(
            AuditEvent.MODEL_TRAIN,
            username=current_user(), role=current_role(), company_id=company,
            detail={"task": "credit", "model_type": stored_type, "experiment": choice},
        )
        st.success("Recommended model version saved and activated.")


def _render_all_credit(registry, mapped: pd.DataFrame, mp: dict, errs: list, validation: list, company: str) -> None:
    """Train-all-models credit training flow."""
    st.markdown("### Hyperparameters for each model (override defaults)")
    st.caption(
        "Expand any model to override its default hyperparameters. Leave collapsed "
        "to use the built-in tuned defaults."
    )
    hp_map = _credit_hyperparams()

    review_h = st.slider(
        "Review threshold (all models)", 0.10, 0.85, 0.50, 0.05, "review_all",
        help="Applied uniformly to all models. Risk scores at or above this value are "
        "flagged for human review.",
    )
    high_h = st.slider(
        "High-risk threshold (all models)", 0.20, 0.95, 0.60, 0.05, "high_all",
        help="Applied uniformly to all models. Risk scores at or above this value are "
        "classified as HIGH_RISK. Must be higher than the review threshold.",
    )
    optimize_thr = st.checkbox(
        "Auto-optimize threshold for each model",
        value=False,
        key="opt_thr_all",
        help="For each model, sweeps candidate thresholds on the holdout to find the one "
        "maximizing F1 and PR-AUC. Overrides the manual sliders above.",
    )

    if review_h > high_h:
        validation.append("threshold")
        st.error("Review threshold cannot exceed the high-risk threshold.")

    if st.button(
        "Train all models and select the best",
        type="primary",
        disabled=bool(errs or validation),
        help="Trains every available credit algorithm and selects the one with the "
        "best composite score (weighted ROC-AUC, F1, and PR-AUC). The winner is saved.",
    ):
        try:
            with st.status("Training all credit models", expanded=True) as status:
                model, met, best_name, all_metrics = train_all_credit(
                    mapped,
                    review_threshold=review_h,
                    high_risk_threshold=high_h,
                    hyperparams_map=hp_map,
                    auto_threshold=optimize_thr,
                )
                st.write("Saving best model version")
                registry.save(company, "credit", model, {
                    "metrics": met, "mapping": mp,
                    "data_summary": quality_report(mapped),
                    "experiment": f"train-all ({best_name})",
                    "model_type": best_name,
                })
                log_event(
                    AuditEvent.MODEL_TRAIN,
                    username=current_user(), role=current_role(), company_id=company,
                    detail={"task": "credit", "model_type": best_name, "experiment": f"train-all ({best_name})"},
                )
                status.update(label=f"Best model: {best_name}", state="complete")
            st.session_state[f"credit_training_{company}"] = (mapped, mp, best_name, review_h, high_h, met)
            st.success(f"All models trained! Best: **{best_name}**")

            with st.expander("All model comparison"):
                comp_rows = []
                for name, m in all_metrics.items():
                    if "error" in m:
                        comp_rows.append({
                            "model": name, "status": "Failed",
                            "ROC_AUC": "-", "PR_AUC": "-",
                            "F1_Score": "-", "Recall": "-", "Brier_Score": "-",
                        })
                    else:
                        comp_rows.append({
                            "model": name,
                            "ROC_AUC": m.get("ROC_AUC", 0),
                            "PR_AUC": m.get("PR_AUC", 0),
                            "F1_Score": m.get("F1_Score", 0),
                            "Recall": m.get("Recall", 0),
                            "Brier_Score": m.get("Brier_Score", 0),
                            "threshold": m.get("threshold", "-"),
                        })
                st.dataframe(pd.DataFrame(comp_rows), use_container_width=True, hide_index=True)
                st.success(
                    f"Auto-selected best model: **{best_name}** "
                    f"with ROC-AUC {met.get('ROC_AUC', 0):.4f}, "
                    f"PR-AUC {met.get('PR_AUC', 0):.4f}, "
                    f"F1 {met.get('F1_Score', 0):.4f}, "
                    f"optimal threshold {met.get('threshold', '-')}"
                )
        except Exception as e:
            st.error(f"Training all models failed: {e}")

        if st.button(
            "Grid search all models (find best params)",
            type="primary",
            disabled=bool(errs or validation),
            help="Exhaustively tests combinations of hyperparameters across all credit "
            "models. Returns the top-performing configurations ranked by F1 score.",
        ):
            try:
                with st.status("Running grid search across all models", expanded=True) as status:
                    top_results, all_ranked = grid_search_credit(mapped)
                    status.update(label="Grid search complete", state="complete")
                with st.expander("Grid search results (top 5)"):
                    gs_rows = []
                    for name, m in all_ranked:
                        gs_rows.append({
                            "model": name,
                            "F1": m.get("F1_Score", 0),
                            "PR_AUC": m.get("PR_AUC", 0),
                            "ROC_AUC": m.get("ROC_AUC", 0),
                            "Recall": m.get("Recall", 0),
                            "Brier": m.get("Brier_Score", 0),
                            "grid_size": m.get("grid_size", "-"),
                            "best_params": str(m.get("best_params", {}))[:120],
                        })
                    st.dataframe(pd.DataFrame(gs_rows), use_container_width=True, hide_index=True)
                    best_gs = all_ranked[0]
                    st.success(
                        f"Grid search best: **{best_gs[0]}** with F1 {best_gs[1].get('F1_Score', 0):.4f} "
                        f"| Use 'Train all' with this model type and hyperparams: "
                        f"{best_gs[1].get('best_params', {})}"
                    )
            except Exception as e:
                st.error(f"Grid search failed: {e}")


# ---------------------------------------------------------------------------
# Demand (forecast) training
# ---------------------------------------------------------------------------

def _render_demand_training(registry, mapped: pd.DataFrame, mp: dict, errs: list, validation: list, company: str) -> None:
    """Render the demand training sub-section."""

    auto_select = st.checkbox(
        "Train all models and auto-select the best",
        value=False,
        key="fc_auto",
        help="Trains every available forecast model and picks the highest composite score.",
    )

    if not auto_select:
        _render_single_forecast(registry, mapped, mp, errs, validation, company)
    else:
        _render_all_forecast(registry, mapped, mp, errs, validation, company)


def _render_single_forecast(
    registry, mapped: pd.DataFrame, mp: dict, errs: list, validation: list, company: str,
) -> None:
    """Single-model forecast training flow."""
    model_type = st.selectbox(
        "Model",
        sorted(AVAILABLE_FORECAST_MODELS),
        key="forecast_model",
        help="LightGBM and Boosted Trees are recommended for demand forecasting. "
        "Random Forest is more interpretable. Baseline uses simple regularization.",
    )

    if st.button(
        "Train demand model",
        type="primary",
        disabled=bool(errs or validation),
        help="Trains the selected algorithm on the training split and evaluates on the "
        "chronological holdout. The trained model is saved as a new version.",
    ):
        try:
            with st.status("Training demand model", expanded=True) as s:
                st.write("Creating chronological holdout")
                model, met = train_forecast(mapped, model_type)
                st.write("Saving version")
                registry.save(company, "forecast", model, {
                    "metrics": met, "mapping": mp,
                    "data_summary": quality_report(mapped),
                })
                log_event(
                    AuditEvent.MODEL_TRAIN,
                    username=current_user(), role=current_role(), company_id=company,
                    detail={"task": "forecast", "model_type": model_type, "experiment": "baseline"},
                )
                s.update(label="Demand model saved", state="complete")
            metric_cards(met, ["MAE", "RMSE", "WAPE", "R2"])
            st.success("Demand model trained and saved!")
        except Exception as e:
            st.error(f"Training failed: {e}")


def _render_all_forecast(registry, mapped: pd.DataFrame, mp: dict, errs: list, validation: list, company: str) -> None:
    """Train-all-models forecast training flow."""
    st.markdown("### Hyperparameters for each model (override defaults)")
    st.caption(
        "Expand any model to override its default hyperparameters. Leave collapsed "
        "to use the built-in tuned defaults."
    )
    hp_map = _forecast_hyperparams()

    if st.button(
        "Train all forecast models and select the best",
        type="primary",
        disabled=bool(errs or validation),
        help="Trains every available forecast algorithm and selects the one with the "
        "best composite score. The winner is saved as a new version.",
    ):
        try:
            with st.status("Training all forecast models", expanded=True) as status:
                model, met, best_name, all_metrics = train_all_forecast(mapped, hyperparams_map=hp_map)
                st.write("Saving best model version")
                registry.save(company, "forecast", model, {
                    "metrics": met, "mapping": mp,
                    "data_summary": quality_report(mapped),
                    "experiment": f"train-all ({best_name})",
                    "model_type": best_name,
                })
                log_event(
                    AuditEvent.MODEL_TRAIN,
                    username=current_user(), role=current_role(), company_id=company,
                    detail={"task": "forecast", "model_type": best_name, "experiment": f"train-all ({best_name})"},
                )
                status.update(label=f"Best model: {best_name}", state="complete")
            metric_cards(met, ["MAE", "RMSE", "WAPE", "R2"])
            st.success(f"All forecast models trained! Best: **{best_name}**")

            with st.expander("All model comparison"):
                comp_rows = []
                for name, m in all_metrics.items():
                    if "error" in m:
                        comp_rows.append({
                            "model": name, "status": "Failed",
                            "MAE": "-", "RMSE": "-", "R2": "-", "WAPE": "-",
                        })
                    else:
                        comp_rows.append({
                            "model": name,
                            "MAE": m.get("MAE", 0),
                            "RMSE": m.get("RMSE", 0),
                            "R2": m.get("R2", 0),
                            "WAPE": m.get("WAPE", 0),
                        })
                st.dataframe(pd.DataFrame(comp_rows), use_container_width=True, hide_index=True)
                st.success(
                    f"Auto-selected best model: **{best_name}** "
                    f"with R2 {met.get('R2', 0):.4f}, "
                    f"MAE {met.get('MAE', 0):.4f}, "
                    f"RMSE {met.get('RMSE', 0):.4f}"
                )
        except Exception as e:
            st.error(f"Training all forecast models failed: {e}")

        if st.button(
            "Grid search all forecast models",
            type="primary",
            disabled=bool(errs or validation),
            help="Exhaustively tests combinations of hyperparameters across all forecast "
            "models. Returns the top-performing configurations ranked by R2 score.",
        ):
            try:
                with st.status("Running forecast grid search", expanded=True) as status:
                    top_results, all_ranked = grid_search_forecast(mapped)
                    status.update(label="Forecast grid search complete", state="complete")
                with st.expander("Forecast grid search results"):
                    gs_rows = []
                    for name, m in all_ranked:
                        gs_rows.append({
                            "model": name,
                            "R2": m.get("R2", 0),
                            "MAE": m.get("MAE", 0),
                            "RMSE": m.get("RMSE", 0),
                            "grid_size": m.get("grid_size", "-"),
                            "best_params": str(m.get("best_params", {}))[:120],
                        })
                    st.dataframe(pd.DataFrame(gs_rows), use_container_width=True, hide_index=True)
                    best_gs = all_ranked[0]
                    st.success(
                        f"Forecast grid search best: **{best_gs[0]}** "
                        f"with R2 {best_gs[1].get('R2', 0):.4f}"
                    )
            except Exception as e:
                st.error(f"Forecast grid search failed: {e}")


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------

def render(registry, recommender, profiles, company) -> None:
    """Render the training page."""

    st.markdown(
        '<div class="page-header"><h1>Training</h1>'
        '<p class="lead">Train a new model from labeled historical data. The system splits your data '
        'into a training partition and an untouched chronological holdout, trains on the former, '
        'and evaluates on the latter to produce unbiased performance metrics. Trained models are '
        'saved as versioned artifacts and can be activated from the History page.</p></div>',
        unsafe_allow_html=True,
    )

    task = st.radio(
        "Model family",
        ["Credit risk", "Demand"],
        horizontal=True,
        help="Credit risk trains a classifier that outputs a risk score per customer. "
        "Demand trains a regressor that forecasts unit demand per period.",
    )
    validation: list = []

    if task == "Credit risk":
        st.markdown(
            "#### Credit risk training pipeline"
        )
        st.caption(
            "Upload labeled credit records (historical loan or account data with known outcomes). "
            "The pipeline validates the data, trains a classifier, and evaluates on an untouched "
            "holdout to produce ROC-AUC, F1, precision, recall, and Brier score."
        )
        df = csv_uploader(
            "Labeled credit history",
            "credit_train",
            help="CSV with historical credit records. Must include the target label column "
            "(default or non-default) and feature columns used during field mapping.",
        )
        if df is None:
            return
        _data_summary(df)
        fields = available_credit_fields(df.columns, True)
        mp, errs = field_mapping(df, fields, "ct_v4")
        mapped = apply_mapping(df, mp)
        validation = validate_credit(mapped, True)
        for e in validation:
            st.error(e)
        _render_credit_training(registry, mapped, mp, errs, validation, company)
    else:
        st.markdown(
            "#### Demand forecast training pipeline"
        )
        st.caption(
            "Upload historical demand records (period, product, units sold, and optional features). "
            "The pipeline validates the data, trains a regressor on the training split, and "
            "evaluates on the chronological holdout to produce MAE, RMSE, WAPE, and R2."
        )
        df = csv_uploader(
            "Historical demand training data",
            "forecast_train",
            help="CSV with historical demand records. Must include a date column and a "
            "units-sold or quantity column. Optional features improve accuracy.",
        )
        if df is None:
            return
        _data_summary(df)
        mp, errs = field_mapping(df, FORECAST_FIELDS, "ft")
        mapped = apply_mapping(df, mp)
        validation = validate_forecast(mapped, True)
        for e in validation:
            st.error(e)
        _render_demand_training(registry, mapped, mp, errs, validation, company)
