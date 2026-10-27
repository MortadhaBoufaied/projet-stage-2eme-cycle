import inspect
import pandas as pd
from src.services.flexible_schema import analyze_dataframe, enhance_schema_with_slm, enhance_schema_with_slm_forecast, slm_schema_suggestion

def test_all_schema_slm_functions_accept_column_meanings():
    for fn in (slm_schema_suggestion, enhance_schema_with_slm, enhance_schema_with_slm_forecast):
        assert 'column_meanings' in inspect.signature(fn).parameters

def test_credit_fallback_accepts_column_meanings_without_endpoint(monkeypatch):
    monkeypatch.delenv('AI_ENDPOINT', raising=False)
    df=pd.DataFrame({'amount':[10,20,30], 'is_late':[0,1,0]})
    result=enhance_schema_with_slm(df, analyze_dataframe(df), column_meanings={'amount':'Invoice value'})
    assert result is not None

def test_forecast_fallback_accepts_column_meanings_without_endpoint(monkeypatch):
    monkeypatch.delenv('AI_ENDPOINT', raising=False)
    df=pd.DataFrame({'units_sold':[10,20,30], 'price':[2,3,4]})
    result=enhance_schema_with_slm_forecast(df, analyze_dataframe(df), column_meanings={'units_sold':'Observed demand'})
    assert result is not None
