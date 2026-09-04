from __future__ import annotations
import itertools
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from src.agents.credit_agent import CreditRiskAgent, get_best_credit_model, AVAILABLE_CREDIT_MODELS
from src.agents.forecast_agent import CashflowForecastAgent, get_best_forecast_model, AVAILABLE_FORECAST_MODELS
from src.services.augmentation import augment_credit_training_data
from src.config import RANDOM_STATE

DEFAULT_CREDIT_MODELS = ["xgboost", "lightgbm", "boosted", "randomforest", "extra_trees", "baseline"]
DEFAULT_FORECAST_MODELS = ["lightgbm", "boosted", "randomforest", "baseline"]

CREDIT_GRID_SEARCH_PARAMS = {
    "xgboost": [
        {"n_estimators": 500, "max_depth": 4, "learning_rate": 0.03, "min_child_weight": 3, "subsample": 0.8, "colsample_bytree": 0.8},
        {"n_estimators": 800, "max_depth": 3, "learning_rate": 0.02, "min_child_weight": 5, "subsample": 0.7, "colsample_bytree": 0.7},
        {"n_estimators": 600, "max_depth": 4, "learning_rate": 0.05, "min_child_weight": 1, "subsample": 0.9, "colsample_bytree": 0.9},
        {"n_estimators": 400, "max_depth": 5, "learning_rate": 0.03, "min_child_weight": 3, "subsample": 0.85, "colsample_bytree": 0.85},
        {"n_estimators": 700, "max_depth": 3, "learning_rate": 0.04, "min_child_weight": 4, "subsample": 0.75, "colsample_bytree": 0.8},
    ],
    "lightgbm": [
        {"n_estimators": 500, "max_depth": 6, "learning_rate": 0.03, "num_leaves": 31, "min_child_samples": 20},
        {"n_estimators": 600, "max_depth": 4, "learning_rate": 0.02, "num_leaves": 15, "min_child_samples": 30},
        {"n_estimators": 400, "max_depth": 8, "learning_rate": 0.04, "num_leaves": 63, "min_child_samples": 15},
        {"n_estimators": 700, "max_depth": 6, "learning_rate": 0.025, "num_leaves": 31, "min_child_samples": 25},
        {"n_estimators": 500, "max_depth": 5, "learning_rate": 0.05, "num_leaves": 15, "min_child_samples": 20},
    ],
    "boosted": [
        {"max_iter": 350, "learning_rate": 0.035, "max_depth": 6, "l2_regularization": 1.0},
        {"max_iter": 500, "learning_rate": 0.02, "max_depth": 8, "l2_regularization": 0.5},
        {"max_iter": 300, "learning_rate": 0.05, "max_depth": 4, "l2_regularization": 2.0},
        {"max_iter": 400, "learning_rate": 0.03, "max_depth": 6, "l2_regularization": 1.5},
        {"max_iter": 450, "learning_rate": 0.025, "max_depth": 7, "l2_regularization": 0.8},
    ],
    "randomforest": [
        {"n_estimators": 500, "max_depth": 12, "min_samples_split": 5, "min_samples_leaf": 2},
        {"n_estimators": 800, "max_depth": 10, "min_samples_split": 3, "min_samples_leaf": 1},
        {"n_estimators": 600, "max_depth": 15, "min_samples_split": 10, "min_samples_leaf": 4},
        {"n_estimators": 400, "max_depth": 8, "min_samples_split": 5, "min_samples_leaf": 2},
        {"n_estimators": 700, "max_depth": 12, "min_samples_split": 7, "min_samples_leaf": 3},
    ],
    "extra_trees": [
        {"n_estimators": 500, "max_depth": 12, "min_samples_split": 5, "min_samples_leaf": 2},
        {"n_estimators": 800, "max_depth": 10, "min_samples_split": 3, "min_samples_leaf": 1},
        {"n_estimators": 600, "max_depth": 15, "min_samples_split": 10, "min_samples_leaf": 4},
        {"n_estimators": 400, "max_depth": 8, "min_samples_split": 5, "min_samples_leaf": 2},
        {"n_estimators": 700, "max_depth": 12, "min_samples_split": 7, "min_samples_leaf": 3},
    ],
    "baseline": [
        {"max_iter": 1000},
        {"max_iter": 2500},
        {"max_iter": 5000},
        {"max_iter": 1500},
        {"max_iter": 3000},
    ],
}

FORECAST_GRID_SEARCH_PARAMS = {
    "lightgbm": [
        {"n_estimators": 500, "max_depth": 6, "learning_rate": 0.03, "num_leaves": 31, "min_child_samples": 20},
        {"n_estimators": 600, "max_depth": 4, "learning_rate": 0.02, "num_leaves": 15, "min_child_samples": 30},
        {"n_estimators": 400, "max_depth": 8, "learning_rate": 0.04, "num_leaves": 63, "min_child_samples": 15},
        {"n_estimators": 700, "max_depth": 6, "learning_rate": 0.025, "num_leaves": 31, "min_child_samples": 25},
        {"n_estimators": 500, "max_depth": 5, "learning_rate": 0.05, "num_leaves": 15, "min_child_samples": 20},
    ],
    "boosted": [
        {"max_iter": 350, "learning_rate": 0.04, "max_depth": 7, "l2_regularization": 1.0},
        {"max_iter": 500, "learning_rate": 0.02, "max_depth": 5, "l2_regularization": 0.5},
        {"max_iter": 300, "learning_rate": 0.06, "max_depth": 9, "l2_regularization": 2.0},
        {"max_iter": 400, "learning_rate": 0.03, "max_depth": 6, "l2_regularization": 1.5},
        {"max_iter": 450, "learning_rate": 0.025, "max_depth": 8, "l2_regularization": 0.8},
    ],
    "randomforest": [
        {"n_estimators": 500, "max_depth": 15, "min_samples_split": 5, "min_samples_leaf": 2},
        {"n_estimators": 800, "max_depth": 12, "min_samples_split": 3, "min_samples_leaf": 1},
        {"n_estimators": 600, "max_depth": 18, "min_samples_split": 10, "min_samples_leaf": 4},
        {"n_estimators": 400, "max_depth": 10, "min_samples_split": 5, "min_samples_leaf": 2},
        {"n_estimators": 700, "max_depth": 15, "min_samples_split": 7, "min_samples_leaf": 3},
    ],
    "baseline": [
        {"alpha": 0.1},
        {"alpha": 1.0},
        {"alpha": 10.0},
        {"alpha": 0.5},
        {"alpha": 5.0},
    ],
}

def fixed_credit_split(df,test_size=.2):
    return train_test_split(df,test_size=test_size,stratify=df['default_next_month'],random_state=RANDOM_STATE)

def train_credit(df,model_type='xgboost',test_size=.2,review_threshold=.5,high_risk_threshold=.6,augmentation=None,hyperparams=None):
    train,test=fixed_credit_split(df,test_size)
    augmentation_meta={"synthetic_rows":0,"original_rows":len(train),"augmented_rows":len(train)}
    fit_data=train
    if augmentation:
        fit_data,augmentation_meta=augment_credit_training_data(train,target_ratio=augmentation.get("target_ratio",.75),jitter=augmentation.get("jitter",.025))
    model=CreditRiskAgent(model_type,review_threshold,high_risk_threshold,hyperparams=hyperparams).fit(fit_data);metrics=model.evaluate(test)
    metrics.update({'split':'fixed stratified holdout','train_rows':len(train),'fit_rows':len(fit_data),'test_rows':len(test),'model_type':model_type,'augmentation':augmentation_meta})
    return model,metrics

def train_credit_with_optimal_threshold(df,model_type='xgboost',test_size=.2,augmentation=None,hyperparams=None,objective="f1"):
    train,test=fixed_credit_split(df,test_size)
    augmentation_meta={"synthetic_rows":0,"original_rows":len(train),"augmented_rows":len(train)}
    fit_data=train
    if augmentation:
        fit_data,augmentation_meta=augment_credit_training_data(train,target_ratio=augmentation.get("target_ratio",.75),jitter=augmentation.get("jitter",.025))
    model=CreditRiskAgent(model_type,0.5,0.9,hyperparams=hyperparams).fit(fit_data)
    optimal_threshold,optimal_metrics=model.optimize_threshold(test,objective=objective)
    model.review_threshold=optimal_threshold; model.high_risk_threshold=max(optimal_threshold+0.1,0.6)
    metrics=model.evaluate(test)
    metrics.update(optimal_metrics)
    metrics.update({'split':'fixed stratified holdout','train_rows':len(train),'fit_rows':len(fit_data),'test_rows':len(test),'model_type':model_type,'augmentation':augmentation_meta})
    return model,metrics

def grid_search_credit(df,test_size=.2,augmentation=None,top_n=5):
    train,test=fixed_credit_split(df,test_size)
    augmentation_meta={"synthetic_rows":0,"original_rows":len(train),"augmented_rows":len(train)}
    fit_data=train
    if augmentation:
        fit_data,augmentation_meta=augment_credit_training_data(train,target_ratio=augmentation.get("target_ratio",.75),jitter=augmentation.get("jitter",.025))
    results={}
    for model_type in DEFAULT_CREDIT_MODELS:
        param_grid=CREDIT_GRID_SEARCH_PARAMS[model_type]
        best_score=-1; best_params=None; best_metrics=None; best_model=None
        total=len(param_grid)
        for i,params in enumerate(param_grid):
            try:
                agent=CreditRiskAgent(model_type,0.5,0.9,hyperparams=params).fit(fit_data)
                metrics=agent.evaluate(test)
                score=metrics.get("F1_Score",0)*0.5+metrics.get("PR_AUC",0)*0.5
                if score>best_score:
                    best_score=score; best_params=params; best_metrics=metrics; best_model=agent
            except Exception:
                continue
        if best_model is not None:
            best_model.review_threshold=best_metrics.get("threshold",0.5)
            best_model.high_risk_threshold=max(best_model.review_threshold+0.1,0.6)
            final_metrics=best_model.evaluate(test)
            final_metrics.update(best_metrics)
            final_metrics.update({"best_params":best_params,"grid_size":total,"model_type":model_type,"augmentation":augmentation_meta})
            results[model_type]=final_metrics
    ranked=sorted(results.items(),key=lambda x:(x[1].get("F1_Score",0)*0.5+x[1].get("PR_AUC",0)*0.5),reverse=True)
    top_n_results=dict(ranked[:top_n])
    return top_n_results,ranked

def grid_search_forecast(df,test_size=.2,top_n=5):
    featured=CashflowForecastAgent().create_features(df)
    dates=np.array(sorted(featured['date'].dropna().unique()))
    if len(dates)<10:raise ValueError('Forecast grid search requires at least 10 distinct dates.')
    cut=dates[max(1,int(len(dates)*(1-test_size)))];train=featured[featured.date<cut].copy();test=featured[featured.date>=cut].copy()
    featured_train=train; featured_test=test
    results={}
    for model_type in DEFAULT_FORECAST_MODELS:
        param_grid=FORECAST_GRID_SEARCH_PARAMS[model_type]
        best_score=-1; best_params=None; best_metrics=None; best_model=None
        total=len(param_grid)
        for i,params in enumerate(param_grid):
            try:
                agent=CashflowForecastAgent(model_type,hyperparams=params).fit(featured_train)
                metrics=agent.evaluate_featured(featured_test)
                score=metrics.get("R2",0)*0.5+(1-metrics.get("MAE",999)/100)*0.5
                if score>best_score:
                    best_score=score; best_params=params; best_metrics=metrics; best_model=agent
            except Exception:
                continue
        if best_model is not None:
            final_metrics=best_model.evaluate_featured(featured_test)
            final_metrics.update(best_metrics)
            final_metrics.update({"best_params":best_params,"grid_size":total,"model_type":model_type})
            results[model_type]=final_metrics
    ranked=sorted(results.items(),key=lambda x:x[1].get("R2",0),reverse=True)
    top_n_results=dict(ranked[:top_n])
    return top_n_results,ranked

def compare_credit_augmentation(df,model_type='xgboost',test_size=.2,review_threshold=.5,high_risk_threshold=.6,target_ratio=.75,jitter=.025):
    train,test=fixed_credit_split(df,test_size)
    base=CreditRiskAgent(model_type,review_threshold,high_risk_threshold).fit(train);base_metrics=base.evaluate(test)
    enlarged,meta=augment_credit_training_data(train,target_ratio,jitter)
    augmented=CreditRiskAgent(model_type,review_threshold,high_risk_threshold).fit(enlarged);aug_metrics=augmented.evaluate(test)
    keys=["ROC_AUC","PR_AUC","F1_Score","Precision","Recall","Brier_Score"]
    comparison=[{"metric":k,"before":base_metrics[k],"after":aug_metrics[k],"change":round(aug_metrics[k]-base_metrics[k],4)} for k in keys]
    score=(aug_metrics["PR_AUC"]-base_metrics["PR_AUC"])*2+(aug_metrics["ROC_AUC"]-base_metrics["ROC_AUC"])+(base_metrics["Brier_Score"]-aug_metrics["Brier_Score"])*.5
    accepted=score>0 and aug_metrics["Recall"]>=base_metrics["Recall"]-.02
    return {"baseline_model":base,"augmented_model":augmented,"baseline_metrics":base_metrics,"augmented_metrics":aug_metrics,"comparison":comparison,"augmentation":meta,"recommended":"augmented" if accepted else "baseline","decision_score":round(float(score),5)}

def train_forecast(df,model_type='boosted',test_size=.2):
    featured=CashflowForecastAgent(model_type).create_features(df);dates=np.array(sorted(featured['date'].dropna().unique()))
    if len(dates)<10:raise ValueError('Forecast training requires at least 10 distinct dates.')
    cut=dates[max(1,int(len(dates)*(1-test_size)))];train=featured[featured.date<cut].copy();test=featured[featured.date>=cut].copy()
    if train.empty or test.empty:raise ValueError('Chronological split produced an empty partition.')
    model=CashflowForecastAgent(model_type).fit(train);metrics=model.evaluate_featured(test);metrics.update({'split':'chronological holdout','cutoff_date':str(pd.Timestamp(cut).date()),'train_rows':len(train),'test_rows':len(test)});return model,metrics


def train_all_credit(df,test_size=.2,review_threshold=.5,high_risk_threshold=.6,augmentation=None,hyperparams_map=None,auto_threshold=False):
    models_metrics={}; models_agents={}
    train_fn=train_credit_with_optimal_threshold if auto_threshold else train_credit
    for model_type in DEFAULT_CREDIT_MODELS:
        hp=(hyperparams_map or {}).get(model_type,None)
        try:
            if auto_threshold:
                model,metrics=train_fn(df,model_type,test_size,augmentation=augmentation,hyperparams=hp)
            else:
                model,metrics=train_fn(df,model_type,test_size,review_threshold,high_risk_threshold,augmentation,hyperparams=hp)
            models_metrics[model_type]=metrics; models_agents[model_type]=model
        except Exception as e:
            models_metrics[model_type]={"error":str(e),"ROC_AUC":0,"PR_AUC":0,"F1_Score":0,"Recall":0,"Brier_Score":1}
    best_name,best_score=get_best_credit_model(models_metrics)
    return models_agents[best_name],models_metrics[best_name],best_name,models_metrics


def train_all_forecast(df,test_size=.2,hyperparams_map=None):
    featured=CashflowForecastAgent().create_features(df);dates=np.array(sorted(featured['date'].dropna().unique()))
    if len(dates)<10:raise ValueError('Forecast training requires at least 10 distinct dates.')
    cut=dates[max(1,int(len(dates)*(1-test_size)))];train=featured[featured.date<cut].copy();test=featured[featured.date>=cut].copy()
    if train.empty or test.empty:raise ValueError('Chronological split produced an empty partition.')
    featured_train=train; featured_test=test
    models_metrics={}; models_agents={}
    for model_type in DEFAULT_FORECAST_MODELS:
        hp=(hyperparams_map or {}).get(model_type,None)
        try:
            agent=CashflowForecastAgent(model_type,hyperparams=hp).fit(featured_train)
            metrics=agent.evaluate_featured(featured_test)
            models_metrics[model_type]=metrics; models_agents[model_type]=agent
        except Exception as e:
            models_metrics[model_type]={"error":str(e),"MAE":999,"RMSE":999,"R2":0,"WAPE":999}
    best_name,best_score=get_best_forecast_model(models_metrics)
    return models_agents[best_name],models_metrics[best_name],best_name,models_metrics
