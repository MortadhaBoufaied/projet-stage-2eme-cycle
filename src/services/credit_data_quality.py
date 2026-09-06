from __future__ import annotations
import numpy as np
import pandas as pd
from src.services.schema import CREDIT_FEATURES, CREDIT_TARGET, CREDIT_ID, PAY_STATUS_FIELDS
BILLS=[f"BILL_AMT{i}" for i in range(1,7)]
PAYMENTS=[f"PAY_AMT{i}" for i in range(1,7)]
DIAGNOSTICS=["source_row_number",CREDIT_ID,"validation_status","issue_count","issue_codes","issue_details","suggested_action","correction_status","correction_note","field","original_value","corrected_value"]

def _add(store, mask, code, severity, message, action):
 for pos in np.flatnonzero(np.asarray(mask,dtype=bool)):
  store[pos].append((code,severity,message(pos),action))

def validate_credit_dataset(df,require_target=True):
 data=df.copy().reset_index(drop=True);n=len(data);issues=[[] for _ in range(n)]
 required=[CREDIT_ID,*CREDIT_FEATURES]+([CREDIT_TARGET] if require_target else [])
 missing=[c for c in required if c not in data]
 if missing: raise ValueError("Missing required columns: "+", ".join(missing))
 ids=data[CREDIT_ID].astype("string").fillna("").str.strip(); _add(issues,ids.eq(""),"MISSING_CLIENT_ID","ERROR",lambda i:"Client ID is missing.","Generate a documented technical ID or verify the source.")
 dup=ids.ne("") & ids.duplicated(False);_add(issues,dup,"DUPLICATE_CLIENT_ID","ERROR",lambda i:f"Client ID {ids.iat[i]} is duplicated.","Resolve duplicate identifiers against the source.")
 numeric={}
 for c in CREDIT_FEATURES+([CREDIT_TARGET] if require_target else []):
  raw=data[c]; num=pd.to_numeric(raw,errors="coerce");numeric[c]=num
  blank=raw.isna() | raw.astype("string").fillna("").str.strip().eq("")
  _add(issues,blank,"MISSING_REQUIRED_VALUE","ERROR",lambda i,c=c:f"{c} is missing.","Verify the value against the source.")
  _add(issues,(~blank)&num.isna(),"NON_NUMERIC_VALUE","ERROR",lambda i,c=c:f"{c} is not numeric.","Normalize only deterministic formatting or verify the source.")
 if require_target:_add(issues,numeric[CREDIT_TARGET].notna() & ~numeric[CREDIT_TARGET].isin([0,1]),"TARGET_NOT_BINARY","ERROR",lambda i:f"Target is {numeric[CREDIT_TARGET].iat[i]}, expected 0 or 1.","Verify the observed outcome.")
 age=numeric["AGE"];limit=numeric["LIMIT_BAL"]
 _add(issues,age.notna()&~age.between(18,110),"AGE_OUT_OF_RANGE","ERROR",lambda i:f"AGE is {age.iat[i]}.","Verify the source record.")
 _add(issues,limit.notna()&(limit<0),"NEGATIVE_CREDIT_LIMIT","ERROR",lambda i:f"LIMIT_BAL is {limit.iat[i]}.","Verify the source record.")
 for c in PAY_STATUS_FIELDS:
  v=numeric[c];_add(issues,v.notna()&~v.between(-2,8),"REPAYMENT_STATUS_OUT_OF_RANGE","WARNING",lambda i,c=c,v=v:f"{c} is {v.iat[i]}.","Confirm the repayment-status coding.")
 for c in BILLS:
  v=numeric[c];_add(issues,v.notna()&(v<0),"NEGATIVE_BILL_AMOUNT","WARNING",lambda i,c=c,v=v:f"{c} is negative ({v.iat[i]}).", "Confirm whether this is a credit, refund, overpayment, or adjustment. Do not automatically replace it with zero.")
  _add(issues,v.notna()&limit.gt(0)&(v.abs()>3*limit),"EXTREME_BILL_TO_LIMIT","WARNING",lambda i,c=c:f"{c} exceeds three times LIMIT_BAL.","Verify exposure and source units.")
 for c in PAYMENTS:
  v=numeric[c];_add(issues,v.notna()&limit.gt(0)&(v>3*limit),"VERY_LARGE_PAYMENT","WARNING",lambda i,c=c:f"{c} exceeds three times LIMIT_BAL.","Verify the payment and source units.")
 signatures=data[CREDIT_FEATURES].astype("string").fillna("<NA>").agg("|".join,axis=1)
 if require_target:
  conflicts=data.groupby(signatures,dropna=False)[CREDIT_TARGET].transform("nunique").gt(1);_add(issues,conflicts,"CONFLICTING_DUPLICATE_FEATURES","ERROR",lambda i:"Identical feature rows have conflicting target labels.","Reconcile labels against the source.")
 repeated=signatures.map(signatures.value_counts()).ge(5);_add(issues,repeated,"REPEATED_CUSTOMER_BEHAVIOR","WARNING",lambda i:f"This behavior profile repeats {int((signatures==signatures.iat[i]).sum())} times.","Confirm that the records represent legitimate distinct customers.")
 rows=[]
 for i,row in data.iterrows():
  its=issues[i];status="REJECTED" if any(x[1]=="ERROR" for x in its) else "REVIEW" if its else "PASS"
  diagnostic={"source_row_number":i+2,CREDIT_ID:str(row[CREDIT_ID]),"validation_status":status,"issue_count":len(its),"issue_codes":";".join(x[0] for x in its),"issue_details":" | ".join(f"{x[1]}: {x[2]}" for x in its),"suggested_action":" | ".join(dict.fromkeys(x[3] for x in its)),"correction_status":"VALID_AS_IS" if status=="PASS" else "","correction_note":"","field":"","original_value":"","corrected_value":""}
  diagnostic.update(row.to_dict());rows.append(diagnostic)
 annotated=pd.DataFrame(rows)
 def subset(status):
  part=annotated[annotated.validation_status.eq(status)].copy();cols=DIAGNOSTICS+[c for c in data.columns if c!=CREDIT_ID];return part.reindex(columns=cols)
 valid_rows,review_rows,rejected_rows=subset("PASS"),subset("REVIEW"),subset("REJECTED")
 reviewed_count=len(valid_rows)+len(review_rows)+len(rejected_rows)
 if reviewed_count!=len(data):raise RuntimeError(f"Validation coverage failure: reviewed {reviewed_count} of {len(data)} rows.")
 row_numbers=pd.concat([valid_rows.source_row_number,review_rows.source_row_number,rejected_rows.source_row_number],ignore_index=True)
 if len(row_numbers)!=len(data) or row_numbers.nunique()!=len(data):raise RuntimeError("Validation coverage failure: duplicate or missing source row numbers.")
 return valid_rows,review_rows,rejected_rows

def apply_correction_patch(original,patch):
 required={"source_row_number",CREDIT_ID,"correction_status"};missing=required-set(patch.columns)
 if missing:raise ValueError("Patch is missing: "+", ".join(sorted(missing)))
 out=original.copy().reset_index(drop=True);excluded=set();applied=0
 for _,r in patch.iterrows():
  pos=int(r["source_row_number"])-2
  if pos<0 or pos>=len(out):raise ValueError(f"source_row_number {pos+2} is outside the dataset.")
  if str(r[CREDIT_ID])!=str(out.at[pos,CREDIT_ID]):raise ValueError(f"Patch key mismatch at source row {pos+2}.")
  status=str(r["correction_status"]).strip().upper();field=str(r.get("field","")).strip()
  if status in {"AUTO_CORRECTED","NORMALIZED"}:
   if field not in out.columns:raise ValueError(f"Unknown correction field: {field}")
   if pd.isna(r.get("corrected_value")):raise ValueError(f"Missing corrected_value for row {pos+2}.")
   out.at[pos,field]=r["corrected_value"];applied+=1
  elif status=="EXCLUDE_FROM_TRAINING":excluded.add(pos);applied+=1
  elif status not in {"VALID_AS_IS","NEEDS_SOURCE_VERIFICATION"}:raise ValueError(f"Unsupported correction_status: {status}")
 return out.drop(index=list(excluded)).reset_index(drop=True),applied
