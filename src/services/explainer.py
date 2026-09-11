"""Centralized SHAP explanation service for the Finance Decision Studio.

Handles pipeline-aware SHAP computation for both credit (flat Pipeline)
and forecast (ColumnTransformer + Pipeline) models. Falls back to
median-deviation heuristic if SHAP computation fails.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _unwrap_sklearn_model(pipeline):
    """Extract the final estimator from an sklearn Pipeline.

    Returns (model_object, imputer_or_preprocessor) so callers can
    transform data through the preprocessing steps before explaining.
    """
    from sklearn.pipeline import Pipeline
    if not isinstance(pipeline, Pipeline):
        return pipeline, None
    steps = dict(pipeline.steps)
    # The last step is always the estimator
    model = pipeline.named_steps[pipeline.steps[-1][0]]
    # Collect preprocessing steps (all except the last)
    preprocessor = None
    if len(pipeline.steps) > 1:
        # Return a sub-pipeline of all steps except the last
        preprocessor_steps = pipeline.steps[:-1]
        preprocessor = Pipeline(preprocessor_steps)
    return model, preprocessor


def compute_shap_values(pipeline, X: pd.DataFrame, background_data: pd.DataFrame = None, top_k: int = 10):
    """Compute SHAP values for a trained sklearn pipeline.

    Args:
        pipeline: A fitted sklearn Pipeline (credit or forecast agent's model).
        X: The data to explain (one or more records).
        background_data: Background data for explainer initialization.
            For TreeExplainer this is optional. For KernelExplainer it is required.
        top_k: Number of top features to return per record.

    Returns:
        List of dicts, one per record, each containing:
        {
            "feature": str,
            "shap_value": float,
            "feature_value": float,
            "direction": "increases_risk" | "decreases_risk"
        }
        Returns None if SHAP computation fails (caller should use fallback).
    """
    try:
        import shap
        from sklearn.pipeline import Pipeline
        from sklearn.compose import ColumnTransformer

        # Unwrap the pipeline to get the model and preprocessor
        model, preprocessor = _unwrap_sklearn_model(pipeline)

        # Transform data through preprocessing if needed
        if preprocessor is not None:
            X_processed = preprocessor.transform(X)
            # Get feature names after transformation
            if hasattr(preprocessor, "get_feature_names_out"):
                feature_names = list(preprocessor.get_feature_names_out())
            else:
                feature_names = [f"feature_{i}" for i in range(X_processed.shape[1])]
        else:
            X_processed = X.values
            feature_names = list(X.columns)

        # Choose the right SHAP explainer based on model type
        explainer = _create_explainer(model, background_data, X_processed)

        # Compute SHAP values
        shap_values = explainer.shap_values(X_processed)

        # Handle different output formats from different explainers
        if isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
            # Binary classifier returns (n_records, n_features, 2) for class 0 and 1
            # Use class 1 (positive class / risk) values
            shap_values = shap_values[:, :, 1]
        elif isinstance(shap_values, list):
            # Some explainers return a list of arrays (one per class)
            shap_values = shap_values[1] if len(shap_values) > 1 else shap_values[0]

        # If background data was transformed, we need the original feature values
        if preprocessor is not None:
            original_names = list(X.columns)
            # For OHE features, aggregate SHAP values back to original columns
            if _has_onehot_encoder(preprocessor):
                shap_values, feature_names = _aggregate_ohe_shap(
                    shap_values, feature_names, preprocessor, X
                )
                X_display = X
            else:
                X_display = pd.DataFrame(X_processed, columns=feature_names, index=X.index)
        else:
            X_display = X

        # Build per-record explanation dicts
        results = []
        for record_idx in range(shap_values.shape[0]):
            record_shap = shap_values[record_idx]
            record_features = X_display.iloc[record_idx] if record_idx < len(X_display) else X_display.iloc[0]

            # Create (abs_shap_value, index) pairs and sort descending
            indexed = list(enumerate(record_shap))
            indexed.sort(key=lambda x: abs(x[1]), reverse=True)

            indicators = []
            for feat_idx, shap_val in indexed[:top_k]:
                feat_name = feature_names[feat_idx] if feat_idx < len(feature_names) else f"feature_{feat_idx}"
                feat_val = float(record_features.get(feat_name, 0)) if hasattr(record_features, "get") else float(record_features.iloc[feat_idx]) if feat_idx < len(record_features) else 0.0
                direction = "increases_risk" if shap_val > 0 else "decreases_risk"
                indicators.append({
                    "feature": feat_name,
                    "shap_value": round(float(shap_val), 6),
                    "feature_value": round(feat_val, 4),
                    "direction": direction,
                })
            results.append(indicators)

        return results

    except Exception:
        # SHAP computation failed -- caller should use fallback explain()
        return None


def _create_explainer(model, background_data, X_processed):
    """Create the appropriate SHAP explainer for the given model type."""
    import shap
    from sklearn.linear_model import LogisticRegression, Ridge

    model_type = type(model).__name__

    # Tree-based models get the fast TreeExplainer
    if hasattr(model, "estimators_") or model_type in (
        "XGBClassifier", "XGBRegressor",
        "LGBMClassifier", "LGBMRegressor",
        "HistGradientBoostingClassifier", "HistGradientBoostingRegressor",
        "RandomForestClassifier", "RandomForestRegressor",
        "ExtraTreesClassifier", "ExtraTreesRegressor",
    ):
        return shap.TreeExplainer(model)

    # Linear models get LinearExplainer
    if isinstance(model, (LogisticRegression, Ridge)):
        return shap.LinearExplainer(model, X_processed)

    # Fallback: use KernelExplainer with a background sample
    bg = background_data
    if bg is None or len(bg) == 0:
        bg = X_processed[:min(100, len(X_processed))]
    return shap.KernelExplainer(model.predict_proba if hasattr(model, "predict_proba") else model.predict, bg)


def _has_onehot_encoder(preprocessor):
    """Check if the preprocessor pipeline contains a OneHotEncoder."""
    from sklearn.compose import ColumnTransformer
    from sklearn.preprocessing import OneHotEncoder
    from sklearn.pipeline import Pipeline

    if isinstance(preprocessor, ColumnTransformer):
        for _, trans, _ in preprocessor.transformers_:
            if isinstance(trans, OneHotEncoder):
                return True
            if isinstance(trans, Pipeline):
                for _, step in trans.steps:
                    if isinstance(step, OneHotEncoder):
                        return True
    return False


def _aggregate_ohe_shap(shap_values, feature_names, preprocessor, X):
    """Aggregate SHAP values from OneHotEncoded features back to original columns.

    When a categorical column like 'region' is OHE into 'region_North', 'region_South',
    this sums the absolute SHAP values across all one-hot columns to produce a single
    SHAP value per original categorical feature.
    """
    from sklearn.compose import ColumnTransformer
    from sklearn.preprocessing import OneHotEncoder
    from sklearn.pipeline import Pipeline

    if not isinstance(preprocessor, ColumnTransformer):
        return shap_values, feature_names

    # Map each output feature index to its original column
    agg_shap = np.zeros((shap_values.shape[0], len(X.columns)))
    agg_names = list(X.columns)

    col_idx = 0
    for name, trans, columns in preprocessor.transformers_:
        if name == "remainder":
            # Passthrough columns go directly
            n_cols = len(columns) if hasattr(columns, "__len__") else 1
            for i in range(n_cols):
                if col_idx < shap_values.shape[1]:
                    # Find which original column this maps to
                    orig_col = columns[i] if isinstance(columns, (list, pd.Index)) else columns
                    if orig_col in X.columns:
                        orig_idx = list(X.columns).index(orig_col)
                        agg_shap[:, orig_idx] += np.abs(shap_values[:, col_idx])
                col_idx += 1
            continue

        if isinstance(trans, OneHotEncoder):
            # Sum SHAP values across all OHE columns for this categorical feature
            n_ohe_cols = shap_values.shape[1] - col_idx
            if isinstance(columns, (list, pd.Index)):
                n_ohe_cols = min(n_ohe_cols, sum(
                    len(trans.categories_[i]) if i < len(trans.categories_) else 1
                    for i in range(len(columns))
                ))
            # Aggregate: sum absolute SHAP values across OHE columns
            # Use the first original column name for the aggregated result
            if isinstance(columns, (list, pd.Index)) and len(columns) > 0:
                orig_col = columns[0]
                if orig_col in X.columns:
                    orig_idx = list(X.columns).index(orig_col)
                    end_idx = min(col_idx + n_ohe_cols, shap_values.shape[1])
                    agg_shap[:, orig_idx] = np.sum(np.abs(shap_values[:, col_idx:end_idx]), axis=1)
            col_idx += n_ohe_cols
        elif isinstance(trans, Pipeline):
            # Pipeline with imputer only (no OHE) -- pass through
            n_pipe_cols = shap_values.shape[1] - col_idx
            if isinstance(columns, (list, pd.Index)):
                for i, c in enumerate(columns):
                    if col_idx + i < shap_values.shape[1] and c in X.columns:
                        orig_idx = list(X.columns).index(c)
                        agg_shap[:, orig_idx] = shap_values[:, col_idx + i]
                col_idx += len(columns)
            else:
                col_idx += n_pipe_cols
        else:
            # SimpleImputer or other -- numeric columns pass through
            if isinstance(columns, (list, pd.Index)):
                for i, c in enumerate(columns):
                    if col_idx + i < shap_values.shape[1] and c in X.columns:
                        orig_idx = list(X.columns).index(c)
                        agg_shap[:, orig_idx] = shap_values[:, col_idx + i]
                col_idx += len(columns)
            else:
                col_idx += 1

    return agg_shap, agg_names
