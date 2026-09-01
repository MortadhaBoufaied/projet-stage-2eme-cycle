# ERP Financial Decision Support System: Synthetic Datasets & AI Agents

An end-to-end AI intelligence pipeline designed for ERP financial decision support. The project includes synthetic data generation, predictive time-series forecasting, credit default risk assessment, SHAP explainability, and Small Language Model (SLM) managerial recommendations.

---

## 📁 Repository Structure

```
finance-stage/
├── data/
│   ├── retail_inventory_forecasting.csv       # Dataset 1: ~72,000 daily retail records
│   ├── credit_default_risk.csv               # Dataset 2: ~30,000 credit client records
│   └── dataset_metadata.json                 # Synthetic generation metadata & parameters
├── src/
│   ├── data_generator/
│   │   ├── forecasting_generator.py           # Dataset 1 Generator (Seasonality, Weather, Promos)
│   │   └── credit_generator.py                # Dataset 2 Generator (Repayment History, Util, Anomalies)
│   ├── agents/
│   │   ├── forecast_agent.py                  # Agent 1: Cashflow / Revenue Forecast Agent
│   │   ├── credit_agent.py                    # Agent 2: Payment Risk Assessment Agent
│   │   └── slm_recommender.py                 # SLM Recommendation Engine Layer
│   └── utils/
├── models/
│   ├── forecast_baseline.pkl                 # Ridge Regressor Baseline
│   ├── forecast_lgb.pkl                      # Boosted Tree Regressor (Agent 1)
│   ├── credit_logreg.pkl                     # Logistic Regression Baseline
│   └── credit_lgb.pkl                        # Boosted Classifier (Agent 2)
├── outputs/
│   ├── forecast_evaluation.json              # MAE & RMSE performance metrics
│   ├── credit_evaluation.json                # ROC-AUC, F1, Precision, Recall metrics
│   ├── shap_summary_credit.png               # SHAP feature importance plot
│   ├── forecast_sample_recommendations.json  # SLM inventory & liquidity recommendations
│   └── credit_sample_recommendations.json    # SLM credit control recommendations
├── docs/
│   └── DATASET_AND_MODEL_DOCUMENTATION.md    # In-depth technical documentation
├── requirements.txt                          # Python dependencies
├── generate_and_train.py                     # Master execution pipeline
└── README.md
```

---

## 🚀 Quickstart Guide

### 1. Installation
Clone the repository and install the dependencies:
```bash
pip install -r requirements.txt
```

### 2. Run Master Pipeline
Execute the master pipeline to generate datasets, train models, save metrics, generate SHAP plots, and produce SLM recommendations:
```bash
python generate_and_train.py
```

---

## 📊 Summary of Model Performance

### Agent 1: Cashflow / Revenue Forecast Agent
- **Target**: Daily Sales Units & Revenue per Store/Product.
- **Evaluation Split**: Chronological Train (80%) / Test (20%).
- **Results**:
  - Baseline Ridge Regressor: MAE = `30.16`, RMSE = `44.07`
  - Boosted Tree Regressor: MAE = `22.68`, RMSE = `35.41` (**25% error reduction**)

### Agent 2: Credit Payment Risk Assessment Agent
- **Target**: Default Next Month (0/1).
- **Evaluation Split**: Stratified Holdout Train (80%) / Test (20%).
- **Results**:
  - Baseline Logistic Regression: ROC-AUC = `0.9907`, F1 = `0.9641`, Precision = `0.9694`, Recall = `0.9589`
  - Boosted Classifier: ROC-AUC = `0.9940`, F1 = `0.9635`, Precision = `0.9681`, Recall = `0.9589`

---

## 🧠 SLM Recommendation Layer

The SLM engine maps model outputs directly to ERP managerial action plans:
- **Revenue Anomalies**: Triggers stock buffer adjustments, expedited inventory transfers, or liquidity reserves during demand shocks.
- **Credit Risk Tiers**: Triggers automated credit policy actions:
  - **High Risk**: Cash deposit requirement (50%), credit line freeze, POD terms.
  - **Medium Risk**: Early payment discount (2/10 Net 30), credit limit cap at 85%.
  - **Low Risk**: Credit limit expansion (+20%), auto-approval of purchase orders.

---

## 📄 Documentation
For detailed generation formulas, feature schemas, and architectural diagrams, see [DATASET_AND_MODEL_DOCUMENTATION.md](file:///c:/Users/Taha/Desktop/finance-stage/docs/DATASET_AND_MODEL_DOCUMENTATION.md).
