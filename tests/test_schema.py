import pandas as pd
from src.services.schema import *
def test_uci_schema_and_no_generation():
    cols=['ID','LIMIT_BAL','AGE','EDUCATION','MARRIAGE']+PAY_STATUS_FIELDS+[f'BILL_AMT{i}' for i in range(1,7)]+[f'PAY_AMT{i}' for i in range(1,7)]+['default.payment.next.month']
    fields=available_credit_fields(cols,True);mapping=suggest_mapping(cols,fields);assert mapping_diagnostics(mapping,fields)[1]==[]
    assert 'PAY'+'_'+'1' not in fields
    df=pd.DataFrame({'AGE':[30]});assert list(apply_mapping(df,{}).columns)==['AGE']
