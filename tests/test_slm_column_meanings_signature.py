import inspect
import pandas as pd
from src.services.flexible_schema import analyze_dataframe, enhance_schema_with_slm, enhance_schema_with_slm_forecast, slm_schema_suggestion

def test_signatures_accept_column_meanings():
    for fn in (enhance_schema_with_slm, enhance_schema_with_slm_forecast, slm_schema_suggestion):
        assert "column_meanings" in inspect.signature(fn).parameters

def test_rule_fallback_accepts_meanings():
    df=pd.DataFrame({"amount":[1,2,3],"is_late":[0,1,0]})
    result=enhance_schema_with_slm(df, analyze_dataframe(df), column_meanings={"amount":"Outstanding invoice amount"})
    assert result is not None
