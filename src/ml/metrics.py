import numpy as np
from sklearn.metrics import *
def classification(y,p,t=.5):
 y=np.asarray(y).astype(int);p=np.asarray(p,float);pred=(p>=t).astype(int);cm=confusion_matrix(y,pred,labels=[0,1]);tn,fp,fn,tp=cm.ravel();out={'accuracy':accuracy_score(y,pred),'precision':precision_score(y,pred,zero_division=0),'recall':recall_score(y,pred,zero_division=0),'f1':f1_score(y,pred,zero_division=0),'specificity':tn/(tn+fp) if tn+fp else None,'balanced_accuracy':balanced_accuracy_score(y,pred),'mcc':matthews_corrcoef(y,pred),'confusion_matrix':cm.tolist(),'tn':int(tn),'fp':int(fp),'fn':int(fn),'tp':int(tp),'prevalence':float(y.mean())}
 out['roc_auc']=roc_auc_score(y,p) if len(np.unique(y))>1 else None;out['pr_auc']=average_precision_score(y,p) if len(np.unique(y))>1 else None;return out
def regression(y,p):
 y=np.asarray(y,float);p=np.asarray(p,float);den=np.abs(y).sum();nz=y!=0
 return {'mae':mean_absolute_error(y,p),'mse':mean_squared_error(y,p),'rmse':mean_squared_error(y,p)**.5,'r2':r2_score(y,p) if len(y)>1 else None,'wape':np.abs(y-p).sum()/den if den else None,'mape':np.mean(np.abs((y[nz]-p[nz])/y[nz])) if nz.any() else None,'median_absolute_error':median_absolute_error(y,p)}
