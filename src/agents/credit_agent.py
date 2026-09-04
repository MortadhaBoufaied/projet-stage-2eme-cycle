from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier, ExtraTreesClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score, brier_score_loss,
                              confusion_matrix, f1_score, precision_score, recall_score,
                              roc_auc_score)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from src.config import RANDOM_STATE
from src.services.schema import CREDIT_FEATURES, CREDIT_TARGET, PAY_STATUS_FIELDS

AVAILABLE_CREDIT_MODELS = {"xgboost", "boosted", "lightgbm", "baseline", "randomforest", "extra_trees"}

DEFAULT_HYPERPARAMS = {
    "xgboost": {"n_estimators": 650, "max_depth": 4, "learning_rate": 0.03, "min_child_weight": 4, "subsample": 0.85, "colsample_bytree": 0.85, "reg_alpha": 0.15, "reg_lambda": 2.0, "gamma": 0.05},
    "lightgbm": {"n_estimators": 600, "max_depth": 6, "learning_rate": 0.03, "num_leaves": 31, "min_child_samples": 20, "subsample": 0.85, "colsample_bytree": 0.85, "reg_alpha": 0.1, "reg_lambda": 1.5},
    "boosted": {"max_iter": 350, "learning_rate": 0.035, "max_depth": 6, "l2_regularization": 1.0},
    "randomforest": {"n_estimators": 500, "max_depth": 12, "min_samples_split": 5, "min_samples_leaf": 2, "class_weight": "balanced"},
    "extra_trees": {"n_estimators": 500, "max_depth": 12, "min_samples_split": 5, "min_samples_leaf": 2, "class_weight": "balanced"},
    "baseline": {"max_iter": 2500},
}

class CreditRiskAgent:
    def __init__(self, model_type="xgboost", review_threshold=.50, high_risk_threshold=.60, hyperparams=None):
        if model_type not in AVAILABLE_CREDIT_MODELS: raise ValueError(f"Unsupported model type: {model_type}. Available: {sorted(AVAILABLE_CREDIT_MODELS)}")
        if not 0 < review_threshold <= high_risk_threshold < 1: raise ValueError("Thresholds must satisfy 0 < review <= high < 1")
        self.model_type=model_type; self.review_threshold=float(review_threshold); self.high_risk_threshold=float(high_risk_threshold)
        self.hyperparams=hyperparams or {}; self.model=None; self.feature_names=[]; self.reference_medians={}

    @staticmethod
    def _engineer(df):
        d=df.copy(); bills=[f"BILL_AMT{i}" for i in range(1,7)]; payments=[f"PAY_AMT{i}" for i in range(1,7)]; delays=PAY_STATUS_FIELDS
        for c in ["LIMIT_BAL","AGE","EDUCATION","MARRIAGE",*bills,*payments,*delays]: d[c]=pd.to_numeric(d[c],errors="coerce")
        limit=d.LIMIT_BAL.abs().replace(0,np.nan); bill1=d.BILL_AMT1.abs().replace(0,np.nan); bill_total=d[bills].abs().sum(axis=1).replace(0,np.nan)
        d["utilization_ratio_1"]=d.BILL_AMT1/limit; d["utilization_ratio_mean"]=d[bills].mean(axis=1)/limit
        d["pay_ratio_1"]=d.PAY_AMT1/bill1; d["pay_ratio_mean"]=d[payments].sum(axis=1)/bill_total
        d["delay_months_max"]=d[delays].max(axis=1); d["delay_count"]=(d[delays]>0).sum(axis=1)
        d["bill_trend"]=d.BILL_AMT1-d.BILL_AMT6; d["payment_total"]=d[payments].sum(axis=1); d["bill_total"]=d[bills].sum(axis=1)
        return d.replace([np.inf,-np.inf],np.nan)

    def _build_model(self, X, y):
        hp=self.hyperparams; base=DEFAULT_HYPERPARAMS[self.model_type]
        merged={**base, **hp}
        if self.model_type=="baseline":
            estimator=Pipeline([("imputer",SimpleImputer(strategy="median")),("scaler",StandardScaler()),("model",LogisticRegression(max_iter=merged.get("max_iter",2500),class_weight="balanced",random_state=RANDOM_STATE))])
        elif self.model_type=="boosted":
            estimator=Pipeline([("imputer",SimpleImputer(strategy="median")),("model",HistGradientBoostingClassifier(max_iter=merged.get("max_iter",350),learning_rate=merged.get("learning_rate",.035),max_depth=merged.get("max_depth",6),l2_regularization=merged.get("l2_regularization",1.),random_state=RANDOM_STATE))])
        elif self.model_type=="lightgbm":
            negatives=max(int((y==0).sum()),1); positives=max(int((y==1).sum()),1); weight=negatives/positives
            estimator=Pipeline([("imputer",SimpleImputer(strategy="median")),("model",LGBMClassifier(n_estimators=merged.get("n_estimators",600),max_depth=merged.get("max_depth",6),learning_rate=merged.get("learning_rate",0.03),num_leaves=merged.get("num_leaves",31),min_child_samples=merged.get("min_child_samples",20),subsample=merged.get("subsample",0.85),colsample_bytree=merged.get("colsample_bytree",0.85),reg_alpha=merged.get("reg_alpha",0.1),reg_lambda=merged.get("reg_lambda",1.5),scale_pos_weight=weight,objective="binary",metric="auc",random_state=RANDOM_STATE,n_jobs=-1,verbose=-1))])
        elif self.model_type in ("randomforest","extra_trees"):
            clf_cls=RandomForestClassifier if self.model_type=="randomforest" else ExtraTreesClassifier
            estimator=Pipeline([("imputer",SimpleImputer(strategy="median")),("model",clf_cls(n_estimators=merged.get("n_estimators",500),max_depth=merged.get("max_depth",12),min_samples_split=merged.get("min_samples_split",5),min_samples_leaf=merged.get("min_samples_leaf",2),class_weight=merged.get("class_weight","balanced"),random_state=RANDOM_STATE,n_jobs=-1))])
        else:
            negatives=max(int((y==0).sum()),1); positives=max(int((y==1).sum()),1); weight=negatives/positives
            estimator=Pipeline([("imputer",SimpleImputer(strategy="median")),("model",XGBClassifier(n_estimators=merged.get("n_estimators",650),max_depth=merged.get("max_depth",4),learning_rate=merged.get("learning_rate",0.03),min_child_weight=merged.get("min_child_weight",4),subsample=merged.get("subsample",0.85),colsample_bytree=merged.get("colsample_bytree",0.85),reg_alpha=merged.get("reg_alpha",0.15),reg_lambda=merged.get("reg_lambda",2.0),gamma=merged.get("gamma",0.05),objective="binary:logistic",eval_metric="aucpr",scale_pos_weight=weight,tree_method="hist",random_state=RANDOM_STATE,n_jobs=-1))])
        self.model=estimator.fit(X,y); return self

    def fit(self, train_df):
        d=self._engineer(train_df); engineered=["utilization_ratio_1","utilization_ratio_mean","pay_ratio_1","pay_ratio_mean","delay_months_max","delay_count","bill_trend","payment_total","bill_total"]
        self.feature_names=[*CREDIT_FEATURES,*engineered]; X=d[self.feature_names]; y=pd.to_numeric(d[CREDIT_TARGET]).astype(int)
        self.reference_medians=X.median(numeric_only=True).fillna(0).to_dict()
        self._build_model(X,y); return self

    def predict_proba(self,df):
        if self.model is None: raise RuntimeError("Credit model is not fitted")
        return self.model.predict_proba(self._engineer(df)[self.feature_names])[:,1]
    def optimize_threshold(self, test_df, objective="f1"):
        y=pd.to_numeric(test_df[CREDIT_TARGET]).astype(int).to_numpy(); p=self.predict_proba(test_df)
        best_thr=0.5; best_score=-1; best_metrics=None
        for thr in [round(x*0.01,2) for x in range(5,96)]:
            pred=(p>=thr).astype(int)
            if pred.sum()==0 or pred.sum()==len(y): continue
            f1=f1_score(y,pred,zero_division=0); pr=average_precision_score(y,p); rec=recall_score(y,pred,zero_division=0); prec=precision_score(y,pred,zero_division=0)
            score=f1 if objective=="f1" else (pr+f1)/2
            if score>best_score: best_score=score; best_thr=thr; best_metrics={"F1_Score":round(float(f1),4),"PR_AUC":round(float(pr),4),"Recall":round(float(rec),4),"Precision":round(float(prec),4),"threshold":thr}
        return best_thr,best_metrics

    def predict_risk(self,df):
        p=self.predict_proba(df); tiers=np.where(p<self.review_threshold,"LOW_RISK",np.where(p<self.high_risk_threshold,"MEDIUM_RISK","HIGH_RISK")); return p,tiers.tolist()
    def evaluate(self,test_df):
        y=pd.to_numeric(test_df[CREDIT_TARGET]).astype(int).to_numpy(); p=self.predict_proba(test_df); pred=(p>=self.review_threshold).astype(int); cm=confusion_matrix(y,pred,labels=[0,1])
        return {"ROC_AUC":round(float(roc_auc_score(y,p)),4),"PR_AUC":round(float(average_precision_score(y,p)),4),"Accuracy":round(float(accuracy_score(y,pred)),4),"F1_Score":round(float(f1_score(y,pred,zero_division=0)),4),"Precision":round(float(precision_score(y,pred,zero_division=0)),4),"Recall":round(float(recall_score(y,pred,zero_division=0)),4),"Brier_Score":round(float(brier_score_loss(y,p)),4),"Confusion_Matrix":cm.tolist(),"true_negatives":int(cm[0,0]),"false_positives":int(cm[0,1]),"false_negatives":int(cm[1,0]),"true_positives":int(cm[1,1]),"default_prevalence":round(float(y.mean()),4),"n_test":len(y),"review_threshold":self.review_threshold}
    def explain(self,df,top_k=5):
        d=self._engineer(df); p,tiers=self.predict_risk(df); output=[]
        for pos,(_,row) in enumerate(d.iterrows()):
            indicators=[]
            for f in self.feature_names:
                value=float(row[f]) if pd.notna(row[f]) else 0.; median=float(self.reference_medians.get(f,0.)); scale=max(abs(median),1.)
                indicators.append((abs(value-median)/scale,{"feature":f,"feature_value":value,"relative_position":"Above training median" if value>median else "At or below training median"}))
            indicators.sort(key=lambda x:x[0],reverse=True)
            output.append({"client_id":str(df.iloc[pos]["client_id"]) if "client_id" in df.columns else str(df.index[pos]),"risk_score":round(float(p[pos]),4),"risk_tier":tiers[pos],"unusual_indicators":[x[1] for x in indicators[:top_k]]})
        return output


def compute_composite_score(metrics):
    pr_auc=metrics.get("PR_AUC",0); roc_auc=metrics.get("ROC_AUC",0); f1=metrics.get("F1_Score",0); recall=metrics.get("Recall",0); brier=metrics.get("Brier_Score",1)
    return (pr_auc*2 + roc_auc + f1 + recall - brier) / 5.0


def get_best_credit_model(models_metrics):
    best=None; best_score=-1
    for name,metrics in models_metrics.items():
        score=compute_composite_score(metrics)
        if score>best_score: best_score=score; best=name
    return best,best_score
