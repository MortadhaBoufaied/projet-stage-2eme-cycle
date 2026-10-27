from __future__ import annotations
import numpy as np
import pandas as pd
from src.services.loan_schema import LOAN_FIELDS

GOOD={"fully paid"}
BAD={"charged off","default","late (31-120 days)","late (16-30 days)"}

def _num(s):
    return pd.to_numeric(s.astype(str).str.replace('%','',regex=False).str.replace(',','',regex=False),errors='coerce')
def _years(s):
    return pd.to_numeric(s.astype(str).str.extract(r'(\d+)')[0],errors='coerce').fillna(0)
def _fico(df):
    lo=_num(df.get('fico_range_low',pd.Series(np.nan,index=df.index)))
    hi=_num(df.get('fico_range_high',pd.Series(np.nan,index=df.index)))
    return (lo+hi)/2

def accepted_to_loan_schema(df:pd.DataFrame,require_target=True):
    """Convert LendingClub accepted-loan columns into the isolated loan-default schema."""
    out=pd.DataFrame(index=df.index)
    out['LoanID']=df.get('id',pd.Series(df.index,index=df.index)).astype(str)
    out['Age']=_num(df.get('age',pd.Series(40,index=df.index))).fillna(40)
    out['Income']=_num(df.get('annual_inc',pd.Series(np.nan,index=df.index)))
    out['LoanAmount']=_num(df.get('loan_amnt',pd.Series(np.nan,index=df.index)))
    fico=_fico(df);out['CreditScore']=fico.fillna(650)
    out['MonthsEmployed']=(_years(df.get('emp_length',pd.Series('0',index=df.index)))*12).clip(0,600)
    out['NumCreditLines']=_num(df.get('total_acc',df.get('open_acc',pd.Series(np.nan,index=df.index))))
    out['InterestRate']=_num(df.get('int_rate',pd.Series(np.nan,index=df.index)))
    out['LoanTerm']=_num(df.get('term',pd.Series('',index=df.index)).astype(str).str.extract(r'(\d+)')[0])
    out['DTIRatio']=_num(df.get('dti',pd.Series(np.nan,index=df.index)))
    out['Education']='Unknown'
    out['EmploymentType']=df.get('emp_title',pd.Series('Unknown',index=df.index)).fillna('Unknown').astype(str)
    out['MaritalStatus']='Unknown'
    out['HasMortgage']=df.get('home_ownership',pd.Series('Unknown',index=df.index)).astype(str).str.upper().eq('MORTGAGE').map({True:'Yes',False:'No'})
    out['HasDependents']='Unknown'
    out['LoanPurpose']=df.get('purpose',pd.Series('Unknown',index=df.index)).fillna('Unknown').astype(str)
    out['HasCoSigner']=df.get('application_type',pd.Series('Individual',index=df.index)).astype(str).str.lower().ne('individual').map({True:'Yes',False:'No'})
    if require_target:
        if 'loan_status' not in df: raise ValueError('This file has no loan_status. Rejected LendingClub applications cannot train a repayment-default model because no repayment outcome exists.')
        status=df['loan_status'].astype(str).str.strip().str.lower()
        keep=status.isin(GOOD|BAD);out=out.loc[keep].copy();status=status.loc[keep]
        out['Default']=status.isin(BAD).astype(int)
    return out[LOAN_FIELDS if require_target else LOAN_FIELDS[:-1]]

def combine_training_files(files):
    frames=[];notes=[]
    for name,df in files:
        try:
            converted=accepted_to_loan_schema(df,True)
            if len(converted): frames.append(converted);notes.append(f'{name}: {len(converted):,} matured accepted loans used')
            else: notes.append(f'{name}: no matured outcomes were usable')
        except ValueError as exc: notes.append(f'{name}: excluded, {exc}')
    if not frames: raise ValueError('No trainable accepted-loan rows were found. Upload accepted LendingClub CSV files containing loan_status.')
    return pd.concat(frames,ignore_index=True).drop_duplicates('LoanID'),notes
