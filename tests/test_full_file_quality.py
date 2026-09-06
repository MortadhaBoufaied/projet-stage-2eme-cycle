import pandas as pd
from src.smoke_check import credit_data
from src.services.credit_data_quality import validate_credit_dataset

def test_validation_reviews_every_row_and_returns_every_problem_row():
    data=credit_data(240)
    data.loc[0,"AGE"]=175
    data.loc[239,"BILL_AMT1"]=-10
    valid,warnings,invalid=validate_credit_dataset(data,True)
    assert len(valid)+len(warnings)+len(invalid)==len(data)
    assert 2 in set(invalid.source_row_number)
    assert 241 in set(warnings.source_row_number)
    all_problems=pd.concat([warnings,invalid],ignore_index=True)
    assert len(all_problems)==len(warnings)+len(invalid)

def test_invalid_rows_can_be_skipped_without_hiding_report():
    data=credit_data(80);data.loc[0,"AGE"]=175
    valid,warnings,invalid=validate_credit_dataset(data,True)
    bad={int(x)-2 for x in invalid.source_row_number}
    usable=data.drop(index=list(bad)).reset_index(drop=True)
    assert len(invalid)==1 and len(usable)==79
