import pandas as pd
from src.services.model_contract import align_to_model

class LegacyModel:
    feature_names_in_ = [
        "business_code_CA02", "invoice_currency_USD", "document type_RV"
    ]

def test_legacy_dummies_are_rebuilt_from_normalized_raw_headers():
    raw = pd.DataFrame({
        " Business Code ": ["CA02", "U001"],
        "invoice-currency": ["USD", "CAD"],
        "document_type": ["RV", "X2"],
    })
    aligned, expected, missing, generated = align_to_model(raw, LegacyModel(), {})
    assert not missing
    assert aligned.loc[0, "business_code_CA02"] == 1
    assert aligned.loc[1, "business_code_CA02"] == 0
    assert aligned.loc[0, "invoice_currency_USD"] == 1
    assert aligned.loc[0, "document type_RV"] == 1
