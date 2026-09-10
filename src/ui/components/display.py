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


def result_metrics(metrics: dict, labels: list[str]) -> None:
    """Render a row of metric cards from a metrics dict."""
    metric_cards(metrics, labels)


def result_table(df: pd.DataFrame, height: int = 400, key: str = None) -> None:
    """Render a styled data table."""
    col_config = None
    if "risk_score" in df.columns:
        col_config = {
            "risk_score": st.column_config.ProgressColumn(
                "Risk score", min_value=0, max_value=1, format="%%"
            )
        }
    st.dataframe(
        df, use_container_width=True, hide_index=True,
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
            f"| Default prevalence: {prevalence:.1% if prevalence else 0:.1%} "
            f"| False negatives: {false_negatives}"
        )


def status_banner(kind: str, message: str) -> None:
    """Render a styled status banner with icon."""
    icons = {"success": "check", "warning": "alert", "error": "x-circle", "info": "info-circle"}
    icon = icons.get(kind, "info-circle")
    cls = f"status-{kind}"
    st.markdown(f'<div class="{cls}">{message}</div>', unsafe_allow_html=True)
