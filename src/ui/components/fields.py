from __future__ import annotations
import pandas as pd
import streamlit as st
from src.services.schema import suggest_mapping, available_credit_fields, CREDIT_ID


def csv_uploader(label: str, key: str, accepted_types: list[str] = None, help: str | None = None) -> pd.DataFrame | None:
    """Render a CSV file uploader and return the parsed DataFrame or None."""
    if accepted_types is None:
        accepted_types = ["csv"]
    f = st.file_uploader(label, type=accepted_types, key=key, help=help)
    if not f:
        return None
    try:
        return pd.read_csv(f, sep=None, engine="python")
    except Exception as e:
        st.error(f"Could not read the file: {e}")
        return None


def field_mapping(df: pd.DataFrame, fields: list[str], key: str) -> tuple[dict, list]:
    """Render field mapping UI with auto-suggestions. Returns (mapping_dict, error_list)."""
    guesses = suggest_mapping(df.columns, fields)
    result: dict[str, str] = {}
    choices = [""] + list(df.columns)
    errors: list[str] = []

    with st.expander("Validate field mapping", expanded=True):
        st.caption("Exact matches are reserved first. Payment status, bill amount, and payment amount families cannot be mixed.")
        a, b = st.columns(2)
        for i, field in enumerate(fields):
            guess = guesses.get(field, "")
            col = a if i % 2 == 0 else b
            result[field] = col.selectbox(
                field, choices,
                index=choices.index(guess) if guess in choices else 0,
                key=f"{key}_{field}",
                help="Optional. A stable row ID is generated when missing." if field == CREDIT_ID else None,
            )
        rows, errs = mapping_diagnostics(result, fields)
        report = pd.DataFrame(rows)
        exact = int((report.Status == "Exact").sum())
        aliases = int((report.Status == "Alias").sum())
        missing = int((report.Status == "Missing").sum())
        invalid = int((report.Status == "Invalid family").sum())
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Exact", exact)
        c2.metric("Aliases", aliases)
        c3.metric("Missing", missing)
        c4.metric("Invalid", invalid)
        st.dataframe(report, width='stretch', hide_index=True,
                      column_config={"Confidence": st.column_config.ProgressColumn("Confidence", min_value=0, max_value=1, format="%.0f%%")})
        unused = [c for c in df.columns if c not in {v for v in result.values() if v}]
        if unused:
            st.caption("Unused source columns: " + ", ".join(map(str, unused)))
    for err in errs:
        errors.append(err)
    for err in errors:
        st.error(err)
    return result, errors


def mapping_diagnostics(mapping: dict, fields: list[str]) -> tuple[list[dict], list[str]]:
    """Return rows and errors for the mapping diagnostic table."""
    from src.services.schema import mapping_diagnostics as _md
    rows, errors = _md(mapping, fields)
    return rows, errors


def model_select(options: list[str], key: str, label: str = "Model") -> str:
    """Render a model selection dropdown."""
    return st.selectbox(label, options, key=key)


def model_select_from_registry(registry, company: str, task: str, key: str, label: str = "Model") -> tuple[str, str] | None:
    """Render a model selector that defaults to the active/trained model.

    Lists all versions for the company/task (falling back to admin models).
    The active model is selected by default; users can switch to any
    previously trained version.

    Returns (version, source_company) for the selected version,
    or None if no trained models exist.
    """
    versions = registry.versions(company, task)
    if not versions:
        st.selectbox(label, ["No trained model"], key=key, disabled=True)
        return None

    # Build display names: "v3 (active)" or "v2"
    options = []
    for v in versions:
        tag = " (active)" if v.get("is_active") else ""
        options.append(f"v{v['version']}{tag}")

    # Default to the active model index
    default_idx = next(
        (i for i, v in enumerate(versions) if v.get("is_active")),
        0,
    )
    selected = st.selectbox(label, options, index=default_idx, key=key)

    # Return the (version, source_company) for the selected version
    for v in versions:
        tag = " (active)" if v.get("is_active") else ""
        if selected == f"v{v['version']}{tag}":
            return (v["version"], company)

    return (versions[default_idx]["version"], company)


def slider_pair(label_low: str, label_high: str, low_default: float, high_default: float) -> tuple[float, float]:
    """Render two linked sliders for low/high threshold pairs."""
    left, right = st.columns(2)
    low = left.slider(label_low, 0.10, 0.85, low_default, 0.05)
    high = right.slider(label_high, 0.20, 0.95, high_default, 0.05)
    return low, high


def checkbox_group(options: list[str], key_prefix: str) -> list[bool]:
    """Render a row of checkboxes. Returns list of booleans."""
    results = []
    for opt in options:
        results.append(st.checkbox(opt, key=f"{key_prefix}_{opt}"))
    return results
