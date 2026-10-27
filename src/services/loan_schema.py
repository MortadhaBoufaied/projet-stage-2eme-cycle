from __future__ import annotations
import pandas as pd
LOAN_ID='LoanID';LOAN_TARGET='Default'
LOAN_NUMERIC=['Age','Income','LoanAmount','CreditScore','MonthsEmployed','NumCreditLines','InterestRate','LoanTerm','DTIRatio']
LOAN_CATEGORICAL=['Education','EmploymentType','MaritalStatus','HasMortgage','HasDependents','LoanPurpose','HasCoSigner']
LOAN_FEATURES=LOAN_NUMERIC+LOAN_CATEGORICAL
LOAN_FIELDS=[LOAN_ID,*LOAN_FEATURES,LOAN_TARGET]
def is_loan_schema(columns,require_target=False):
 needed=set(LOAN_FEATURES+([LOAN_TARGET] if require_target else []));return len(needed & set(columns)) >= int(len(needed)*.8)
def validate_loan(df,require_target=True):
 required=LOAN_FEATURES+([LOAN_TARGET] if require_target else []);errors=[f'Missing column: {c}' for c in required if c not in df]
 if errors:return errors
 for c in LOAN_NUMERIC:
  if pd.to_numeric(df[c],errors='coerce').isna().any():errors.append(f'{c} contains missing or non-numeric values.')
 if require_target:
  y=pd.to_numeric(df[LOAN_TARGET],errors='coerce');
  if y.isna().any() or not set(y.unique()).issubset({0,1}) or y.nunique()<2:errors.append('Default must contain both binary classes 0 and 1.')
 if (~pd.to_numeric(df.Age,errors='coerce').between(18,100)).any():errors.append('Age must be between 18 and 100.')
 if (pd.to_numeric(df.Income,errors='coerce')<=0).any():errors.append('Income must be positive.')
 if (~pd.to_numeric(df.CreditScore,errors='coerce').between(300,850)).any():errors.append('CreditScore must be between 300 and 850.')
 return list(dict.fromkeys(errors))
