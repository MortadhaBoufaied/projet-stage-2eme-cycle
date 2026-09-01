"""
Master Execution Pipeline for Financial Intelligence ERP System.

Generates datasets, trains baseline and boosted models, computes metrics,
generates SHAP explainability artifacts, and executes SLM recommendation generation.
"""

import os
import json
import numpy as np
import pandas as pd

from src.data_generator.forecasting_generator import generate_retail_forecasting_data
from src.data_generator.credit_generator import generate_credit_default_data
from src.agents.forecast_agent import CashflowForecastAgent
from src.agents.credit_agent import CreditRiskAgent
from src.agents.recommender import RecommendationEngine

def main():
    print("=" * 70)
    print("STARTING ERP FINANCIAL INTELLIGENCE PIPELINE")
    print("=" * 70)
    
    os.makedirs("data", exist_ok=True)
    os.makedirs("models", exist_ok=True)
    os.makedirs("outputs", exist_ok=True)
    os.makedirs("docs", exist_ok=True)
    
    # -------------------------------------------------------------------------
    # STEP 1: Generate Synthetic Datasets
    # -------------------------------------------------------------------------
    print("\n[Step 1/5] Generating Synthetic Datasets...")
    
    df_forecast, meta_forecast = generate_retail_forecasting_data(
        num_stores=10, num_products=10, num_days=720, random_seed=42
    )
    df_forecast.to_csv("data/retail_inventory_forecasting.csv", index=False)
    try:
        df_forecast.to_parquet("data/retail_inventory_forecasting.parquet", index=False)
        print(" -> Retail Inventory Parquet exported successfully.")
    except Exception as e:
        print(f" -> Retail Inventory Parquet export skipped: {e}")
    print(f" -> Retail Inventory Dataset: {len(df_forecast):,} records saved to CSV.")
    
    df_credit, meta_credit = generate_credit_default_data(
        num_clients=30000, random_seed=42
    )
    df_credit.to_csv("data/credit_default_risk.csv", index=False)
    try:
        df_credit.to_parquet("data/credit_default_risk.parquet", index=False)
        print(" -> Credit Default Parquet exported successfully.")
    except Exception as e:
        print(f" -> Credit Default Parquet export skipped: {e}")
    print(f" -> Credit Default Dataset: {len(df_credit):,} records saved to CSV.")
    
    # Save combined dataset metadata
    dataset_metadata = {
        "forecasting_dataset": meta_forecast,
        "credit_dataset": meta_credit
    }
    with open("data/dataset_metadata.json", "w") as f:
        json.dump(dataset_metadata, f, indent=2)
    print(" -> Dataset metadata saved to data/dataset_metadata.json.")

    # -------------------------------------------------------------------------
    # STEP 2: Train Agent 1 — Revenue / Cashflow Forecast Agent
    # -------------------------------------------------------------------------
    print("\n[Step 2/5] Training Agent 1: Revenue / Cashflow Forecast Agent...")
    
    # Time-series chronological split (80% train, 20% test)
    dates = sorted(df_forecast["date"].unique())
    split_idx = int(len(dates) * 0.8)
    split_date = dates[split_idx]
    
    train_fc = df_forecast[df_forecast["date"] < split_date].copy()
    test_fc = df_forecast[df_forecast["date"] >= split_date].copy()
    print(f" -> Forecast Train Period: {train_fc['date'].min()} to {train_fc['date'].max()} ({len(train_fc):,} rows)")
    print(f" -> Forecast Test Period:  {test_fc['date'].min()} to {test_fc['date'].max()} ({len(test_fc):,} rows)")
    
    # Baseline Model (Ridge)
    agent1_base = CashflowForecastAgent(model_type="baseline")
    agent1_base.fit(train_fc)
    eval1_base = agent1_base.evaluate(test_fc)
    agent1_base.save_model("models/forecast_baseline.pkl")
    
    # Boosted Model (XGBoost / LightGBM)
    agent1_boosted = CashflowForecastAgent(model_type="boosted")
    agent1_boosted.fit(train_fc)
    eval1_boosted = agent1_boosted.evaluate(test_fc)
    agent1_boosted.save_model("models/forecast_lgb.pkl")
    
    forecast_eval_results = {
        "agent": "Cashflow / Revenue Forecast Agent",
        "split": "Chronological Train (80%) / Test (20%)",
        "baseline_ridge": eval1_base,
        "boosted_model": eval1_boosted
    }
    with open("outputs/forecast_evaluation.json", "w") as f:
        json.dump(forecast_eval_results, f, indent=2)
        
    print(f" -> Agent 1 Baseline (Ridge):   MAE = {eval1_base['MAE']}, RMSE = {eval1_base['RMSE']}")
    print(f" -> Agent 1 Boosted (XGB/LGB):  MAE = {eval1_boosted['MAE']}, RMSE = {eval1_boosted['RMSE']}")

    # -------------------------------------------------------------------------
    # STEP 3: Train Agent 2 — Credit Default Risk Assessment Agent
    # -------------------------------------------------------------------------
    print("\n[Step 3/5] Training Agent 2: Credit Default Risk Assessment Agent...")
    
    # Random Stratified Split (80% train, 20% test)
    np.random.seed(42)
    shuffled_indices = np.random.permutation(len(df_credit))
    split_point = int(len(df_credit) * 0.8)
    
    train_cred = df_credit.iloc[shuffled_indices[:split_point]].copy()
    test_cred = df_credit.iloc[shuffled_indices[split_point:]].copy()
    print(f" -> Credit Train Set: {len(train_cred):,} clients | Test Set: {len(test_cred):,} clients")
    
    # Baseline Model (Logistic Regression)
    agent2_base = CreditRiskAgent(model_type="baseline")
    agent2_base.fit(train_cred)
    eval2_base = agent2_base.evaluate(test_cred)
    agent2_base.save_model("models/credit_logreg.pkl")
    
    # Boosted Model (XGBoost / LightGBM)
    agent2_boosted = CreditRiskAgent(model_type="boosted")
    agent2_boosted.fit(train_cred)
    eval2_boosted = agent2_boosted.evaluate(test_cred)
    agent2_boosted.save_model("models/credit_lgb.pkl")
    
    credit_eval_results = {
        "agent": "Payment Risk Assessment Agent",
        "split": "Random Holdout Train (80%) / Test (20%)",
        "baseline_logistic_regression": eval2_base,
        "boosted_model": eval2_boosted
    }
    with open("outputs/credit_evaluation.json", "w") as f:
        json.dump(credit_eval_results, f, indent=2)
        
    print(f" -> Agent 2 Baseline (LogReg): ROC-AUC = {eval2_base['ROC_AUC']}, F1 = {eval2_base['F1_Score']}, Precision = {eval2_base['Precision']}, Recall = {eval2_base['Recall']}")
    print(f" -> Agent 2 Boosted (XGB/LGB): ROC-AUC = {eval2_boosted['ROC_AUC']}, F1 = {eval2_boosted['F1_Score']}, Precision = {eval2_boosted['Precision']}, Recall = {eval2_boosted['Recall']}")

    # Generate SHAP / Feature Impact Plot
    print(" -> Generating SHAP / Feature Impact Summary Plot...")
    sample_test_shap = test_cred.head(500)
    agent2_boosted.save_shap_summary_plot(sample_test_shap, "outputs/shap_summary_credit.png")
    print(" -> Saved outputs/shap_summary_credit.png")

    # -------------------------------------------------------------------------
    # STEP 4: Run SLM Recommendation Engine Layer
    # -------------------------------------------------------------------------
    print("\n[Step 4/5] Executing SLM Recommendation Engine Layer...")
    recommender = RecommendationEngine()
    
    # Generate Forecast Anomaly Recommendations
    anomaly_df = agent1_boosted.detect_anomalies(test_fc)
    alerts = agent1_boosted.generate_alerts(anomaly_df, max_alerts=5)
    
    forecast_recs = []
    for alert in alerts:
        rec = recommender.generate_revenue_recommendation(alert)
        forecast_recs.append(rec)
        
    with open("outputs/forecast_sample_recommendations.json", "w") as f:
        json.dump(forecast_recs, f, indent=2)
    print(f" -> Generated {len(forecast_recs)} forecast SLM recommendations -> outputs/forecast_sample_recommendations.json")
    
    # Generate Credit Risk Recommendations for sample Low, Medium, High risk clients
    sample_clients = test_cred.head(10)
    explanations = agent2_boosted.explain_client_risk(sample_clients, top_k=5)
    
    credit_recs = []
    for exp in explanations:
        rec = recommender.generate_credit_recommendation(exp)
        credit_recs.append(rec)
        
    with open("outputs/credit_sample_recommendations.json", "w") as f:
        json.dump(credit_recs, f, indent=2)
    print(f" -> Generated {len(credit_recs)} credit SLM recommendations -> outputs/credit_sample_recommendations.json")

    # -------------------------------------------------------------------------
    # STEP 5: Completion Summary
    # -------------------------------------------------------------------------
    print("\n[Step 5/5] Pipeline Completed Successfully!")
    print("=" * 70)

if __name__ == "__main__":
    main()
