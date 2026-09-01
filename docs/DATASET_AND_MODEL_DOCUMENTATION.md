# Synthetic Datasets & AI Financial Decision Support System

## Executive Overview
This project provides an end-to-end AI financial decision support solution designed for modern ERP systems (such as SAP S/4HANA, NetSuite, Dynamics 365). The system features:
1. **Synthetic Data Generation Engine**: Creates highly realistic, large-scale financial and operational datasets with non-linear correlations, multi-period seasonal demand patterns, weather anomalies, credit risk distributions, and injected behavioral shocks.
2. **Agent 1 — Cashflow / Revenue Forecast Agent**: Multi-horizon time-series forecasting model combining lag features, rolling statistics, calendar dynamics, and boosted trees (XGBoost/LightGBM) to forecast revenue, detect abnormal declines, and generate stockout alerts.
3. **Agent 2 — Credit Default / Payment Risk Assessment Agent**: High-precision risk scoring and classification model (Logistic Regression baseline & Boosted Classifier) with SHAP (SHapley Additive exPlanations) driver analysis.
4. **SLM Recommendation Engine**: Small Language Model decision protocol layer translating raw predictive scores and diagnostic drivers into actionable managerial ERP workflows.

---

## 1. Synthetic Datasets Specification

### Dataset 1: Retail Store Inventory Forecasting (`retail_inventory_forecasting.csv`)
- **Scale**: **72,000 daily entries** (10 Stores × 10 Products × 720 Days / 2 Years).
- **Primary Schema**:
  - `date` (`YYYY-MM-DD`): Daily timestamp covering 2024-01-01 to 2025-12-20.
  - `store_id` (`str`): `STORE_001` to `STORE_010`.
  - `product_id` (`str`): `PROD_001` to `PROD_010`.
  - `category` (`str`): Beverages, Electronics, Apparel, Grocery, Home.
  - `region` (`str`): North, South, East, West.
  - `units_sold` (`int`): Target variable representing daily sales units.
  - `inventory_level` (`int`): End-of-day stock level with dynamic reorder point logic.
  - `promotions_holidays` (`int`): Binary flag (1 if active promotion or holiday spike).
  - `weather_conditions` (`str`): Sunny, Rainy, Hot, Snowy, Stormy.
- **Generative Logic & Assumptions**:
  - **Base Category Demand**: Beverages (~180/day), Grocery (~250/day), Apparel (~90/day), Home (~60/day), Electronics (~45/day).
  - **Weekly & Annual Seasonality**: Sine/cosine annual curves (summer peak for Beverages; winter peak for Apparel) with weekend boost multiplier (1.25x).
  - **Holidays**: Black Friday / Cyber Monday (1.85x surge), Christmas (1.70x), Summer (1.40x).
  - **Weather Anomalies**:
    - `Hot`: +45% uplift on Beverages, -5% on Apparel.
    - `Rainy`: -15% retail foot traffic.
    - `Stormy`: -45% foot traffic drop across categories.
    - `Snowy`: +15% grocery panic-buying, -30% electronics/apparel.
  - **Inventory & Stockouts**: Simulated reorder point buffer (3 days of demand) with 1-day lead time replenishment. When inventory reaches 0, sales are capped at available stock to simulate real stockout loss.

---

### Dataset 2: Credit Default / Payment Risk (`credit_default_risk.csv`)
- **Scale**: **30,000 client accounts**.
- **Primary Schema**:
  - `client_id` (`str`): `CLI_000001` to `CLI_030000`.
  - `LIMIT_BAL` (`float`): Credit limit (10,000 to 1,000,000 NTD/USD).
  - `AGE` (`int`): Client age (21 to 75).
  - `EDUCATION` (`int`): 1=Graduate School, 2=University, 3=High School, 4=Others.
  - `MARRIAGE` (`int`): 1=Married, 2=Single, 3=Others.
  - `PAY_0` to `PAY_6` (`int`): Repayment status for past 6 months (-2=no balance, -1=paid in full, 0=revolving credit, 1..4=months payment delay).
  - `BILL_AMT1` to `BILL_AMT6` (`float`): Bill statement amounts for past 6 months.
  - `PAY_AMT1` to `PAY_AMT6` (`float`): Payment amounts made for past 6 months.
  - `default_next_month` (`int`): Target variable (0=No Default, 1=Default Next Month).
- **Generative Logic & Assumptions**:
  - **Credit Limit Distribution**: Log-normal distribution conditioned on education level and age.
  - **Repayment Status Transition**: Markovian delay probabilities linked to latent creditworthiness scale.
  - **Credit Utilization & Payment Ratios**: Beta-distributed credit utilization ratios (`BILL_AMT` / `LIMIT_BAL`). Payments reflect repayment codes (e.g. 100% bill paid for status -1; 10-30% paid for revolving status 0; 0-15% paid for delayed status 1+).
  - **Injected Anomalies**: 2% random financial shock default injection on historically clean client accounts to simulate sudden macro/microeconomic defaults.

---

## 2. Agent Modeling & Benchmark Results

### Agent 1 — Revenue / Cashflow Forecast Agent
- **Evaluation Split**: Chronological 80% Train / 20% Test split (57,600 train rows, 14,400 test rows).
- **Metrics**: Mean Absolute Error (MAE), Root Mean Squared Error (RMSE).

| Model Architecture | MAE | RMSE | Notes |
| :--- | :---: | :---: | :--- |
| **Ridge Regression (Baseline)** | 30.16 | 44.07 | Uses seasonal lags + one-hot encodings |
| **Boosted Trees (XGBoost/LightGBM)** | **22.68** | **35.41** | **25% MAE reduction** via non-linear feature interactions |

---

### Agent 2 — Payment Risk Assessment Agent
- **Evaluation Split**: Stratified 80% Train / 20% Test split (24,000 train clients, 6,000 test clients).
- **Metrics**: ROC-AUC, F1-Score, Precision, Recall.

| Model Architecture | ROC-AUC | F1-Score | Precision | Recall | Notes |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Logistic Regression (Baseline)** | 0.9907 | 0.9641 | 0.9694 | 0.9589 | Highly interpretable odds ratio baseline |
| **Boosted Classifier (XGBoost/LightGBM)** | **0.9940** | **0.9635** | **0.9681** | **0.9589** | Exceptional non-linear risk separation |

---

## 3. Explainability & Diagnostics

### SHAP Risk Driver Analysis
Agent 2 integrates SHAP (`TreeExplainer`) to break down individual credit default risk probabilities into feature contributions:
1. **Top Positively Correlated Risk Drivers (Increase Default Probability)**:
   - High payment delay history in `PAY_0` and `PAY_1` (> 2 months delay).
   - High recent credit utilization ratio (`BILL_AMT1` / `LIMIT_BAL` > 0.85).
   - Low recent payment ratio (`PAY_AMT1` / `BILL_AMT1` < 0.10).
2. **Top Negatively Correlated Drivers (Decrease Default Probability)**:
   - High total credit limit (`LIMIT_BAL`).
   - Clean repayment status codes (`PAY_0` in [-1, -2]).
   - Higher education status (`EDUCATION` = 1).

The SHAP / Feature Impact summary chart is generated and saved as `outputs/shap_summary_credit.png`.

---

## 4. Small Language Model (SLM) Recommendation Layer

The SLM Recommendation Engine maps model outputs, anomaly alerts, and SHAP drivers into structured ERP decision payloads:

### Sample Revenue Forecast SLM Output (`outputs/forecast_sample_recommendations.json`)
```json
{
  "recommendation_id": "REC_REV_ALT_FC_000042",
  "store_id": "STORE_003",
  "product_id": "PROD_001",
  "urgency": "HIGH",
  "action_title": "Emergency Replenishment & Stock Buffer Adjustment (STORE_003 - PROD_001)",
  "executive_summary": "Current inventory level (34 units) at STORE_003 for Beverages (PROD_001) is insufficient to meet forecasted daily demand of 185 units. High risk of stockout within 48 hours.",
  "action_plan": [
    "Trigger expedited inter-store transfer of 555 units of PROD_001 from neighboring distribution hubs.",
    "Increase automated safety stock buffer by 25% for product category 'Beverages' during current peak demand window.",
    "Notify procurement to issue urgent purchase order (PO) with supplier to prevent revenue leakage."
  ],
  "estimated_financial_impact": "Mitigates potential lost daily sales of up to $8,325."
}
```

### Sample Credit Risk SLM Output (`outputs/credit_sample_recommendations.json`)
```json
{
  "recommendation_id": "REC_CRED_CLI_024001",
  "client_id": "CLI_024001",
  "risk_tier": "HIGH_RISK",
  "risk_score": 0.8745,
  "urgency": "HIGH",
  "action_title": "High Risk Default Prevention Protocol (CLI_024001)",
  "executive_summary": "Client CLI_024001 exhibits a high default probability of 87.5%. Key risk drivers include: PAY_0 (Increases Risk), utilization_ratio_1 (Increases Risk).",
  "action_plan": [
    "Freeze open credit lines for new purchase orders until outstanding balance is below 30% utilization.",
    "Require upfront cash deposit (minimum 50%) on all upcoming delivery fulfillment contracts.",
    "Assign designated ERP collections specialist for immediate personal outreach and payment restructuring.",
    "Transition client payment terms from Net 60 to Payment on Delivery (POD)."
  ],
  "credit_policy_changes": {
    "credit_limit_action": "Reduce Limit by 40%",
    "payment_terms": "POD / Immediate",
    "collateral_required": true
  }
}
```
