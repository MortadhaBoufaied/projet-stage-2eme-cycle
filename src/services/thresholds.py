from __future__ import annotations
import numpy as np
from sklearn.metrics import precision_score,recall_score,f1_score,confusion_matrix

def threshold_report(y,probabilities,miss_cost=10.,false_alert_cost=1.,review_cost=.1):
    rows=[];y=np.asarray(y,dtype=int);p=np.asarray(probabilities,float)
    for threshold in np.arange(.10,.801,.01):
        pred=(p>=threshold).astype(int);tn,fp,fn,tp=confusion_matrix(y,pred,labels=[0,1]).ravel();reviews=int(pred.sum())
        cost=fn*miss_cost+fp*false_alert_cost+reviews*review_cost
        rows.append({"threshold":round(float(threshold),2),"precision":precision_score(y,pred,zero_division=0),"recall":recall_score(y,pred,zero_division=0),"f1":f1_score(y,pred,zero_division=0),"false_positives":int(fp),"false_negatives":int(fn),"reviews":reviews,"estimated_cost":round(float(cost),2)})
    return rows,min(rows,key=lambda r:r["estimated_cost"])
