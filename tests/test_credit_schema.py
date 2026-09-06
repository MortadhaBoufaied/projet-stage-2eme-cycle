import pandas as pd
from src.services.schema import *

def uci_columns():
    return ['ID','LIMIT_BAL','SEX','EDUCATION','MARRIAGE','AGE','PAY_0','PAY_2','PAY_3','PAY_4','PAY_5','PAY_6'] + [f'BILL_AMT{i}' for i in range(1,7)] + [f'PAY_AMT{i}' for i in range(1,7)] + ['default.payment.next.month']

def test_uci_contract_has_no_pay1():
    fields=available_credit_fields(uci_columns(),True)
    assert 'PAY' + '_' + '1' not in fields
    mapping=suggest_mapping(uci_columns(),fields)
    assert 'PAY' + '_' + '1' not in mapping
    assert mapping['PAY_0']=='PAY_0' and mapping['PAY_2']=='PAY_2' and mapping['PAY_6']=='PAY_6'
    assert mapping['PAY_AMT6']=='PAY_AMT6'
    assert mapping['client_id']=='ID'
    assert mapping['default_next_month']=='default.payment.next.month'
    assert mapping_diagnostics(mapping,fields)[1]==[]

def test_apply_mapping_never_generates_columns():
    df=pd.DataFrame({'AGE':[30],'LIMIT_BAL':[1000]})
    out=apply_mapping(df,{})
    assert list(out.columns)==['AGE','LIMIT_BAL']
