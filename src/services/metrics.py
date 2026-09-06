import numpy as np
from sklearn.metrics import *
def classification(y,p,threshold=.5):
    y=np.asarray(y); p=np.asarray(p); pred=(p>=threshold).astype(int); cm=confusion_matrix(y,pred,labels=[0,1]); tn,fp,fn,tp=cm.ravel(); safe=lambda a,b: None if b==0 else float(a/b)
    out={'Accuracy':float(accuracy_score(y,pred)),'Precision':float(precision_score(y,pred,zero_division=0)),'Recall':float(recall_score(y,pred,zero_division=0)),'F1':float(f1_score(y,pred,zero_division=0)),'Specificity':safe(tn,tn+fp),'Balanced Accuracy':float(balanced_accuracy_score(y,pred)),'MCC':float(matthews_corrcoef(y,pred)),'PR-AUC':None,'ROC-AUC':None,'TP':int(tp),'TN':int(tn),'FP':int(fp),'FN':int(fn),'Confusion Matrix':cm.tolist(),'Positive prevalence':float(np.mean(y==1))}
    if len(np.unique(y))>1: out['ROC-AUC']=float(roc_auc_score(y,p)); out['PR-AUC']=float(average_precision_score(y,p))
    return out
def regression(y,p):
    y=np.asarray(y,float); p=np.asarray(p,float); e=y-p; denom=np.abs(y).sum(); nonzero=y!=0
    return {'MAE':float(mean_absolute_error(y,p)),'MSE':float(mean_squared_error(y,p)),'RMSE':float(mean_squared_error(y,p)**.5),'R2':float(r2_score(y,p)) if len(y)>1 else None,'WAPE':float(np.abs(e).sum()/denom) if denom else None,'MAPE':float(np.mean(np.abs(e[nonzero]/y[nonzero]))) if nonzero.any() else None,'Median Absolute Error':float(median_absolute_error(y,p))}
