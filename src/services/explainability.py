from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance


def global_importance(model, X: pd.DataFrame, y=None, top_k: int = 10) -> list[dict]:
    """Model-based importance, with permutation fallback for any fitted pipeline."""
    if y is not None:
        result = permutation_importance(model, X, y, n_repeats=3, random_state=42, scoring="average_precision")
        values = result.importances_mean
        names = list(X.columns)
    else:
        final = model.named_steps.get("model", model) if hasattr(model, "named_steps") else model
        values = getattr(final, "feature_importances_", None)
        names = list(X.columns)
        if values is None or len(values) != len(names):
            return []
    order = np.argsort(np.abs(values))[::-1][:top_k]
    return [{"feature": names[i], "importance": float(values[i]), "direction": "increases predictive signal" if values[i] >= 0 else "reduces predictive signal"} for i in order]


def local_reason_codes(row: pd.Series, reference: dict, importance: list[dict], top_k: int = 5) -> list[dict]:
    output=[]
    for item in importance:
        feature=item["feature"]
        if feature not in row: continue
        value=row[feature]; baseline=reference.get(feature)
        output.append({"feature":feature,"value":None if pd.isna(value) else value,"reference":baseline,"importance":item["importance"],"evidence":"model importance plus observed feature value"})
        if len(output)>=top_k: break
    return output
