import pandas as pd
from src.smoke_check import credit_data
from src.services.credit_data_quality import validate_credit_dataset

def test_first_and_last_rows_are_scanned():
 d=credit_data(100);d.loc[0,"AGE"]=175;d.loc[99,"BILL_AMT1"]=-1
 v,w,r=validate_credit_dataset(d,True)
 assert len(v)+len(w)+len(r)==100
 assert 2 in set(r.source_row_number) and 101 in set(w.source_row_number)
 assert len(pd.concat([w,r]))==len(w)+len(r)


def test_every_row_appears_exactly_once_in_reviewed_output():
 d=credit_data(24000);d.loc[0,"AGE"]=175;d.loc[23999,"BILL_AMT1"]=-1
 v,w,r=validate_credit_dataset(d,True);reviewed=pd.concat([v,w,r],ignore_index=True)
 assert len(reviewed)==24000
 assert reviewed.source_row_number.nunique()==24000
 assert set(reviewed.source_row_number)==set(range(2,24002))
