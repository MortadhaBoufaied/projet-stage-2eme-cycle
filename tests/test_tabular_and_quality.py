from io import BytesIO
import pandas as pd
from src.smoke_check import credit_data
from src.services.tabular_io import read_tabular_bytes
from src.services.credit_data_quality import validate_credit_dataset,apply_correction_patch
def test_csv_xlsx_and_uci_header():
 d=pd.DataFrame({'A':[1]});assert len(read_tabular_bytes(d.to_csv(index=False).encode(),'a.csv'))==1
 raw=pd.DataFrame([['LIMIT_BAL','AGE','PAY_0','default payment next month'],[100,30,0,0]],columns=['X1','X2','X3','Y']);b=BytesIO();raw.to_excel(b,index=False);assert list(read_tabular_bytes(b.getvalue(),'a.xlsx').columns)[0]=='LIMIT_BAL'
def test_validation_and_patch():
 d=credit_data(40);d.loc[0,'AGE']=175;d.loc[1,'BILL_AMT1']=-1;v,w,r=validate_credit_dataset(d);assert len(v)+len(w)+len(r)==40 and 'AGE_OUT_OF_RANGE' in ';'.join(r.issue_codes)
 p=pd.DataFrame([{'source_row_number':2,'client_id':d.loc[0,'client_id'],'field':'AGE','corrected_value':35,'correction_status':'NORMALIZED'}]);fixed,n=apply_correction_patch(d,p);assert n==1 and fixed.loc[0,'AGE']==35
