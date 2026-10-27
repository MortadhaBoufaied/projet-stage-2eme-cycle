from __future__ import annotations
import pandas as pd

def raw_model_features(model, metadata):
    features = list((metadata or {}).get('features') or [])
    if not features and hasattr(model, 'feature_names_in_'):
        features = list(model.feature_names_in_)
    return features

def prepare_model_input(frame: pd.DataFrame, model, metadata):
    """Return raw training columns. Never require one-hot output columns from uploads."""
    features = raw_model_features(model, metadata)
    if not features:
        raise ValueError('The active model has no saved raw feature contract. Retrain and save it again.')
    missing = [name for name in features if name not in frame.columns]
    if missing:
        raise ValueError('Missing required raw columns: ' + ', '.join(missing))
    return frame.loc[:, features].copy()
