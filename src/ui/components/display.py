from __future__ import annotations

import pandas as pd
import streamlit as st


def metric_cards(values: dict, labels: list[str]) -> None:
    """Render a row of metric cards from a dict and ordered label list."""
    cols = st.columns(len(labels))
    for col, name in zip(cols, labels):
        val = values.get(name, "--")
        if isinstance(val, float):
            val = f"{val:.3f}" if abs(val) < 10 else f"{val:.2f}"
        col.metric(name.replace("_", " "), val)


def risk_tier_badge(tier: str, score: float | None = None) -> None:
    """Render a standardized modern status badge for risk tiers."""
    tier_upper = str(tier).upper()
    if "HIGH" in tier_upper:
        color = "var(--danger, #ef4444)"
        bg = "rgba(239, 68, 68, 0.15)"
        icon = "bi-shield-fill-x"
        label = "High Risk"
    elif "MEDIUM" in tier_upper or "REVIEW" in tier_upper:
        color = "var(--warning, #f59e0b)"
        bg = "rgba(245, 158, 11, 0.15)"
        icon = "bi-exclamation-triangle-fill"
        label = "Medium Risk (Review)"
    else:
        color = "var(--success, #22c55e)"
        bg = "rgba(34, 197, 94, 0.15)"
        icon = "bi-shield-fill-check"
        label = "Low Risk"

    score_str = f" &bull; Score: {score:.1%}" if score is not None else ""
    st.markdown(
        f"""
        <div style="display:inline-flex; align-items:center; gap:0.5rem; background:{bg}; color:{color}; 
                    border:1px solid {color}44; border-radius:8px; padding:0.4rem 0.85rem; font-weight:600; font-size:0.92rem; margin: 0.4rem 0 0.8rem;">
            <i class="bi {icon}"></i>
            <span>{label}{score_str}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def result_metrics(metrics: dict, labels: list[str]) -> None:
    """Render a row of metric cards from a metrics dict."""
    metric_cards(metrics, labels)


def result_table(df: pd.DataFrame, height: int = 400, key: str = None) -> None:
    """Render a styled data table."""
    col_config = None
    if "risk_score" in df.columns:
        col_config = {
            "risk_score": st.column_config.ProgressColumn(
                "Risk score", min_value=0, max_value=1, format="%.0f%%"
            )
        }
    st.dataframe(
        df, width='stretch', hide_index=True,
        height=height, column_config=col_config,
    )


def result_chart(
    df: pd.DataFrame, column: str, chart_type: str = "bar",
    height: int = 300, key: str = None,
) -> None:
    """Render a chart from a DataFrame column."""
    if chart_type == "bar":
        st.bar_chart(df[column], height=height, key=key)
    elif chart_type == "line":
        st.line_chart(df[column], height=height, key=key)
    else:
        st.write(f"Chart type '{chart_type}' not yet supported.")


def download_button(
    data: pd.DataFrame, filename: str, label: str = "Download report",
) -> None:
    """Render a CSV download button."""
    csv_data = data.to_csv(index=False).encode()
    st.download_button(label, csv_data, filename, "text/csv")


def training_results(
    metrics: dict, test_rows: int = None,
    prevalence: float = None, false_negatives: int = None,
) -> None:
    """Render training result metrics with metadata."""
    metric_cards(
        metrics,
        ["ROC_AUC", "PR_AUC", "Accuracy", "F1_Score", "Precision", "Recall", "Brier_Score"],
    )
    if test_rows is not None:
        st.caption(
            f"Untouched holdout: {test_rows} rows "
            f"| Default prevalence: {(prevalence or 0):.1%} "
            f"| False negatives: {false_negatives}"
        )


def status_banner(kind: str, message: str) -> None:
    """Render a styled status banner with icon."""
    icons = {"success": "check", "warning": "alert", "error": "x-circle", "info": "info-circle"}
    icon = icons.get(kind, "info-circle")
    cls = f"status-{kind}"
    st.markdown(f'<div class="{cls}">{message}</div>', unsafe_allow_html=True)


def render_shap_bar(
    shap_indicators: list[dict],
    record_label: str = "",
    key_prefix: str = "shap",
) -> None:
    """Render a horizontal bar chart of SHAP feature contributions.

    Args:
        shap_indicators: List of dicts with keys "feature", "shap_value", "feature_value", "direction".
        record_label: Optional label shown as the chart title (e.g. customer ID).
        key_prefix: Unique prefix for Streamlit widget keys to avoid collisions.
    """
    if not shap_indicators:
        st.caption("No SHAP explanation available for this record.")
        return

    import pandas as pd

    # Build a DataFrame sorted by absolute SHAP value descending
    df = pd.DataFrame(shap_indicators)
    df["abs_shap"] = df["shap_value"].abs()
    df = df.sort_values("abs_shap", ascending=True)  # ascending for horizontal bar (bottom = highest)

    # Color: positive SHAP (increases risk) = red-ish, negative = green-ish
    colors = ["#d9534f" if v > 0 else "#5cb85c" for v in df["shap_value"]]

    title = f"Feature contributions for {record_label}" if record_label else "Feature contributions"
    st.caption(title)

    # Use Streamlit bar_chart on the absolute values with color context via caption
    chart_df = pd.DataFrame({"SHAP value": df["shap_value"].values}, index=df["feature"].values)
    st.bar_chart(chart_df, height=max(200, len(df) * 32))

    # Render direction legend
    st.caption("Red (positive) = increases risk | Green (negative) = decreases risk")


def render_shap_table(shap_indicators: list[dict]) -> None:
    """Render a tabular view of SHAP indicators with feature values and directions."""
    if not shap_indicators:
        return
    import pandas as pd
    df = pd.DataFrame(shap_indicators)
    df = df[["feature", "feature_value", "shap_value", "direction"]]
    df.columns = ["Feature", "Value", "SHAP contribution", "Direction"]
    st.dataframe(df, width='stretch', hide_index=True)
