import tempfile
from pathlib import Path
import pandas as pd
import src.services.company_workspace as ws
from src.services.schema import *

def test_schema_does_not_generate_columns():
    df=pd.DataFrame({'AGE':[30]});assert list(apply_mapping(df,{}).columns)==['AGE'];assert 'PAY'+'_'+'1' not in CREDIT_FEATURES

def test_analysis_and_case_storage():
    with tempfile.TemporaryDirectory() as td:
        ws.DB=Path(td)/'workspace.db'
        result=pd.DataFrame({'client_id':['A','B'],'risk_score':[.8,.1],'risk_tier':['HIGH_RISK','LOW_RISK']})
        aid=ws.save_analysis('company','sample.csv',result)
        assert aid and len(ws.analyses('company'))==1 and len(ws.cases('company'))==1
        case=ws.cases('company')[0];ws.update_case('company',case['id'],'CLOSED','Monitor','Reviewed')
        assert ws.cases('company','CLOSED')[0]['decision']=='Monitor'
