# Technical Architecture Report: AI Agents for Financial Decision Support in ERP Systems

**Project Title**: Design and Implementation of AI Agents for Financial Decision Support in ERP Systems  
**Domain**: Enterprise Resource Planning (ERP), Applied Machine Learning, Explainable AI (XAI), Natural Language Generation (NLG)  
**System Name**: Finance Decision Studio (FDS)

---

## 1. Executive Summary & Problem Context

Enterprise Resource Planning (ERP) systems (such as SAP, Odoo, Oracle NetSuite, and Microsoft Dynamics) serve as the transactional backbone of modern enterprises. They store mission-critical operational and financial data, including sales orders, customer accounts, accounts receivable (AR), and general ledgers.

### The Limitation of Traditional ERP
Traditional ERP systems are fundamentally **reactive and descriptive**:
1. **Historical Ledger Bias**: Standard reports present historical totals, past aging schedules, and trailing balance sheets, but lack forward-looking predictive foresight.
2. **Delayed Risk Mitigation**: Financial managers typically intervene only after an invoice becomes delinquent or after inventory stockouts and cash deficits occur.
3. **Black-Box Skepticism**: Introducing predictive algorithms without explainability leads to mistrust from underwriters and chief financial officers.

### The Solution: Finance Decision Studio
This project implements a dedicated **Financial Intelligence & AI Agent Layer** that complements existing ERP systems. Rather than replacing the transactional database, it ingests ERP transactional tables and applies two specialized AI agents to provide proactive, transparent, and auditable decision support.

---

## 2. Multi-Agent System Architecture

`mermaid
flowchart TD
    subgraph DataLayer [ERP Ingestion & Data Layer]
        D1[Invoices & Payment Records]
        D2[Historical Sales & Inventory Data]
        VAL[Schema Validation & Alias Resolver]
    end

    subgraph AgentLayer [Intelligent AI Agent Layer]
        A1[Agent 1: Cashflow / Revenue Forecast Agent]
        A2[Agent 2: Payment Risk Assessment Agent]
    end

    subgraph Intelligence [Explainability & Natural Language Generation]
        SHAP[SHAP Value Explainer]
        NLG[NLG Narrative Engine]
    end

    subgraph GovernanceLayer [Governance, Policies & Audit]
        POL[Recommendation Policy Engine]
        HUMAN[Human-in-the-Loop Approval Gate]
        AUDIT[Append-Only SQLite Audit Trail]
    end

    subgraph ActionLayer [ERP Decision Support & Operational Outputs]
        OUT1[Adjust Credit Terms & Limits]
        OUT2[Automated Dunning & Early Warning Alerts]
        OUT3[Forward Revenue Inflows & Supply-Chain Actions]
    end

    D1 & D2 --> VAL
    VAL --> A1 & A2
    A1 & A2 --> SHAP & NLG
    A1 & A2 & SHAP & NLG --> POL
    POL --> HUMAN --> AUDIT
    HUMAN --> OUT1 & OUT2 & OUT3
`

---

## 3. Agent 1: Cashflow & Revenue Forecast Agent

### 3.1 Objective & Purpose
To anticipate future financial performance, forecast periodic revenue and cash inflow trajectories, detect abnormal dips or spikes, and flag stockout and liquidity risks before they impact cash reserves.

### 3.2 Feature Engineering & Model Architecture
- **Time-Series Decomposition & Lag Creation**:
  - Temporal features: Day of week, month, quarter, day of year, weekend indicator.
  - Lag features: Past sales (t-1, t-7, t-14, t-30).
  - Rolling aggregations: Rolling 7-day and 30-day moving averages and standard deviations.
- **Algorithms Implemented**:
  - Boosted (HistGradientBoostingRegressor): State-of-the-art native categorical split support with robust outlier tolerance.
  - LightGBM (LGBMRegressor): High-throughput leaf-wise tree growth.
  - RandomForest (RandomForestRegressor): High variance reduction.
  - Baseline (RidgeCV): Regularized linear benchmark.
- **Iterative Multi-Step Forward Forecasting**:
  - Predicts t+1, appends the predicted unit demand to update lag features, and rolls forward iteratively across 7, 14, or 30 days ahead.
- **Revenue Estimation**:
  - Estimated Revenue = Predicted Units * Configured Price Per Unit

### 3.3 Managerial Decision Support
- **Anomaly Detection**: Flags demand periods deviating beyond dynamic confidence intervals (> 2.5 sigma).
- **Stockout Risk Flagging**: Compares forward demand against current inventory levels to trigger pre-orders.
- **Financial Risk Alerts**: Detects projected cash intake decline (> 15% drop) over the planning horizon.

---

## 4. Agent 2: Payment Risk Assessment Agent

### 4.1 Objective & Purpose
To evaluate customer creditworthiness and invoice delinquency risk, outputting a calibrated default probability P(Default), assigning risk classifications (LOW, MEDIUM, HIGH), identifying key financial drivers, and generating policy-compliant risk mitigation recommendations.

### 4.2 Machine Learning Architecture
- **Imbalanced Class Handling**:
  - Credit default datasets typically demonstrate high class imbalance (~20% default rate).
  - Controlled synthetic augmentation via Gaussian-mixture perturbations on minority samples with strict fidelity bounds.
- **Algorithms Implemented**:
  - XGBoost (XGBClassifier): Optimized gradient boosting with scale pos weight adjustments.
  - LightGBM (LGBMClassifier): Fast histogram-based gradient boosting.
  - Random Forest & Extra Trees: Ensemble bagging for variance minimization.
  - Baseline (LogisticRegression): Interpretable linear baseline.
- **Evaluation Benchmark Metrics**:
  - Primary: ROC-AUC and PR-AUC (Precision-Recall Area Under Curve).
  - Secondary: Brier Score (probability calibration accuracy), F1-Score, Precision, and Recall.
- **Dynamic Threshold Optimization**:
  - Optimizes decision boundary tau in [0.1, 0.9] on holdout sets to balance cost-sensitive credit losses vs opportunity cost.

---

## 5. Explainability (XAI) and Natural Language Generation (NLG)

### 5.1 Local Explainability via SHAP (SHapley Additive exPlanations)
To eliminate black-box friction for ERP underwriters:
- **Implementation Strategy**:
  - TreeExplainer for tree models (instant computation).
  - LinearExplainer for linear baselines.
  - KernelExplainer sampling fallback for arbitrary black-box estimators.
  - Visual output: Horizontal bar visualizations separating positive risk drivers (red) from negative risk mitigators (green).

### 5.2 Natural Language Generation
- Transforms raw numeric predictions and SHAP vectors into executive managerial narratives.
- **Dual-Mode Generation**:
  1. Online Mode: Queries OpenRouter LLM endpoints with structured JSON context.
  2. Deterministic Mode: Robust template engine requiring zero external internet connection or API keys.

---

## 6. Enterprise Governance & Security

1. **Multi-Tenant Isolation**: Separation by company_id, allowing multi-entity ERP tenants to maintain distinct models and policies while falling back to system-wide admin models.
2. **Policy Enforcement Engine**:
   - review_threshold & high_risk_threshold bounds.
   - Forbidden action keyword filtration.
   - Mandatory human approval toggles for high-stakes credit limit extensions.
3. **Audit Trail**: Append-only SQLite ledger recording all sign-ins, model retrainings, version activations, and policy modifications with timestamps and user identities.

---

## 7. Experimental Results Summary

| Task | Best Algorithm | Key Metric (Holdout) | Secondary Metric | Brier Score / WAPE |
| :--- | :--- | :--- | :--- | :--- |
| **Payment Risk (Credit)** | XGBoost / LightGBM | **ROC-AUC: 0.785 – 0.998** | F1: 0.542 – 0.985 | Brier: 0.082 |
| **Cashflow & Demand** | HistGradientBoosting | **R2: 0.892 – 0.982** | MAE: 8.4 units | WAPE: 9.1% |

---

## 8. Conclusion & Academic Alignment

The implemented system satisfies all objectives detailed in Project_Overview.docx:
- Dual AI Agent Integration: Complete Cashflow/Revenue and Payment Risk assessment agents.
- Actionable Decision Logic: Structured policies translating predictions into managerial actions.
- Explainability & Transparency: Full SHAP attribution and NLG report generation.
- Deliverables: Fully tested codebase (147 tests passing), interactive Streamlit interface, and versioned SQLite persistence.
