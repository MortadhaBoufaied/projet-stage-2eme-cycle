from __future__ import annotations
import pandas as pd
import streamlit as st


def result_metrics(metrics: dict, labels: list[str]) -> None:
    """Render a row of metric cards from a metrics dict."""
    from src.ui.components.layout import metric_cards
    metric_cards(metrics, labels)


def result_table(df: pd.DataFrame, height: int = 400, key: str = None) -> None:
    """Render a styled data table."""
    st.dataframe(df, use_container_width=True, hide_index=True, height=height,
                  column_config={"risk_score": st.column_config.ProgressColumn("Risk score", min_value=0, max_value=1, format="%.") if "risk_score" in df.columns else None} if "risk_score" in df.columns else None)


def result_chart(df: pd.DataFrame, column: str, chart_type: str = "bar", height: int = 300, key: str = None) -> None:
    """Render a chart from a DataFrame column."""
    if chart_type == "bar":
        st.bar_chart(df[column], height=height, key=key)
    elif chart_type == "line":
        st.line_chart(df[column], height=height, key=key)
    else:
        st.write(f"Chart type '{chart_type}' not yet supported.")


def download_button(data: pd.DataFrame, filename: str, label: str = "Download report") -> None:
    """Render a CSV download button."""
    csv_data = data.to_csv(index=False).encode()
    st.download_button(label, csv_data, filename, "text/csv")


def training_results(metrics: dict, test_rows: int = None, prevalence: float = None, false_negatives: int = None) -> None:
    """Render training result metrics with metadata."""
    from src.ui.components.layout import metric_cards
    metric_cards(metrics, ["ROC_AUC", "PR_AUC", "Accuracy", "F1_Score", "Precision", "Recall", "Brier_Score"])
    if test_rows is not None:
        st.caption(f"Untouched holdout: {test_rows} rows · Default prevalence: {prevalence:.1% if prevalence else 0:.1%} · False negatives: {false_negatives}")


def status_banner(kind: str, message: str) -> None:
    """Render a styled status banner with icon."""
    icons = {"success": "✅", "warning": "⚠️", "error": "❌", "info": "ℹ️"}
    icon = icons.get(kind, "ℹ️")
    cls = f"status-{kind}"
    st.markdown(f'<div class="{cls}">{icon} {message}</div>', unsafe_allow_html=True)
