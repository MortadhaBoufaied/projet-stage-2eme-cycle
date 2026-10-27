from __future__ import annotations
import math

CLASSIFICATION_WEIGHTS = {
    'PR-AUC': 0.18, 'ROC-AUC': 0.14, 'F1': 0.14, 'Recall': 0.14,
    'Precision': 0.10, 'Balanced Accuracy': 0.12, 'MCC': 0.12,
    'Accuracy': 0.06,
}

def _value(metrics, key, default=0.0):
    value = metrics.get(key, default)
    try:
        value = float(value)
        return value if math.isfinite(value) else default
    except (TypeError, ValueError):
        return default

def classification_score(metrics):
    """Composite validation score using all useful classification metrics."""
    score = sum(weight * _value(metrics, key) for key, weight in CLASSIFICATION_WEIGHTS.items())
    # Penalize poor probability quality when available. Brier ranges from 0 (best) to 1.
    if metrics.get('Brier Score') is not None:
        score += 0.06 * (1.0 - _value(metrics, 'Brier Score', 1.0))
    # Avoid recommending a model that obtains a good average while failing either class.
    floor = min(_value(metrics, 'Recall'), _value(metrics, 'Specificity'), _value(metrics, 'Precision'))
    score -= 0.12 * max(0.0, 0.55 - floor)
    return float(score)

def rank_classification_runs(runs):
    for run in runs:
        run['selection_score'] = classification_score(run['validation'])
        run['selection_basis'] = dict(CLASSIFICATION_WEIGHTS)
    return sorted(runs, key=lambda r: (r['selection_score'], r['validation'].get('PR-AUC') or -1), reverse=True)
