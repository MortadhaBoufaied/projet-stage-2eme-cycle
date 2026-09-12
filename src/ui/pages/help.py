from __future__ import annotations
import streamlit as st


def render(registry, recommender, profiles, company) -> None:
    """Render the help page."""

    st.markdown(
        '<div class="page-header"><h1>How the system works</h1>'
        '<p class="lead">Finance Decision Studio is a governed ML platform that turns historical data '
        'into credit risk scores and demand forecasts, with full version control, '
        'explainability, and human oversight.</p></div>',
        unsafe_allow_html=True,
    )

    # -- Mission ----------------------------------------------------------------
    st.markdown("### Mission & ERP Context")
    st.markdown(
        "Traditional Enterprise Resource Planning (ERP) systems (e.g. SAP, Odoo, Oracle NetSuite) "
        "excel at recording and reporting historical transactions, invoices, and payments. "
        "However, they are inherently reactive: financial managers often only react after revenues decline "
        "or invoices turn delinquent.\n\n"
        "**Finance Decision Studio** acts as the dedicated **Financial Intelligence & AI Agent Layer** on top of ERP ledgers. "
        "It deploys two specialized AI agents to transition financial management from reactive bookkeeping "
        "to proactive, transparent, and explainable decision support:\n"
        "- **Agent 1 — Cashflow / Revenue Forecast Agent**: Anticipates future revenue trajectories, detects abnormal downturns, and flags stockout/cashflow vulnerability.\n"
        "- **Agent 2 — Payment Risk Assessment Agent**: Analyzes credit behavior and repayment histories to estimate delayed payment probabilities across customers and invoices."
    )

    st.markdown("""
    ```mermaid
    flowchart LR
        subgraph ERP ["ERP System (e.g., Odoo, SAP)"]
            T[Sales Orders & Invoices]
            C[Customer Payment Ledger]
        end

        subgraph AI ["Finance Decision Studio (AI Agent Layer)"]
            A1["Agent 1: Cashflow / Revenue Forecast (HistGradientBoosting / LightGBM)"]
            A2["Agent 2: Payment Risk Assessment (XGBoost / LightGBM / RF)"]
            XAI["Explainability (SHAP Values)"]
            NLG["Natural Language Generation (Executive Narrative)"]
            POL["Governance & Decision Policies"]
        end

        subgraph OUT ["Managerial Decision Support"]
            D1[Revenue Forecast & Inflow Schedules]
            D2[Credit Term Adjustment & Pre-approval]
            D3[Proactive Dunning & Collection Alerts]
        end

        T --> A1
        C --> A2
        A1 & A2 --> XAI --> POL
        A1 & A2 --> NLG --> POL
        POL --> D1 & D2 & D3
    ```
    """)

    # -- Sample data ------------------------------------------------------------
    st.markdown("### Sample data")
    st.markdown(
        "Three CSV datasets are provided in `data/` and can be loaded directly or uploaded "
        "as your own files. Each file corresponds to one of the two AI agents."
    )
    st.markdown("""
    | Dataset | File | Agent | Records |
    |---------|------|-------|---------|
    | UCI Credit Card | `data/UCI_Credit_Card.csv` | Credit risk | 30,000 |
    | Synthetic credit risk | `data/credit_default_risk.csv` | Credit risk | 30,000 |
    | Retail inventory forecasting | `data/retail_inventory_forecasting.csv` | Demand forecast | 72,000 |
    """)
    st.markdown(
        "Metadata for the datasets is available in `data/dataset_metadata.json`. "
        "See the **Data schema** section below for the exact column names expected by each agent."
    )

    # -- Pipeline ---------------------------------------------------------------
    st.markdown("### The decision pipeline")
    st.markdown(
        "Each workflow follows the same five-stage pipeline. Every stage produces "
        "artifacts that are inspectable and reversible."
    )

    st.markdown("""
    | Stage | What happens | Where to find it |
    |-------|-------------|------------------|
    | **1. Upload data** | CSV records are parsed, profiled for quality (rows, missing cells, duplicates), and previewed. | Credit risk or Demand page |
    | **2. Map fields** | Column headers are matched to required fields via auto-suggestion. An exact-match / alias / invalid-family report flags problems before training. | Credit risk or Demand page |
    | **3. Validate** | The mapped dataset is checked for structural completeness and minimum row thresholds. Blocking errors prevent downstream steps. | Credit risk or Demand page |
    | **4. Train** | A model is trained on the labeled partition and evaluated on an untouched chronological holdout. Metrics (ROC-AUC, F1, MAE, R2, etc.) and a confusion breakdown are returned. | Training page |
    | **5. Deploy** | The trained model version is saved to the company workspace. The active version is the one used for live predictions. One-click rollback is available. | History page |
    """)

    st.markdown(
        "After deployment, the Credit risk and Demand pages run the **active model** "
        "against new uploads without retraining. Recommendations are generated by the "
        "governance engine, which applies your company rules on top of the raw prediction."
    )

    # -- Data schema ------------------------------------------------------------
    st.markdown("### Data schema")
    st.markdown("**Credit-risk CSV columns** (expected by the Credit risk page):")
    st.markdown("""
    - `client_id` (optional) — stable row identifier; auto-generated when missing
    - `LIMIT_BAL` — credit limit
    - `AGE` — age
    - `EDUCATION` — education level
    - `MARRIAGE` — marital status
    - `PAY_0`, `PAY_2`, `PAY_3`, `PAY_4`, `PAY_5`, `PAY_6` — repayment status
      (note: `PAY_1` is not used or generated)
    - `BILL_AMT1`–`BILL_AMT6` — bill statement amounts (6 months)
    - `PAY_AMT1`–`PAY_AMT6` — previous payment amounts (6 months)
    - `default_next_month` — binary target label
    """)
    st.markdown("**Demand-forecast CSV columns** (expected by the Demand page):")
    st.markdown("""
    - `date` — period date
    - `store_id` — store identifier
    - `product_id` — product identifier
    - `category` — product category
    - `region` — region
    - `units_sold` — target value to forecast
    - `inventory_level` — current stock level
    - `promotions_holidays` — promotion/holiday flag
    - `weather_conditions` — weather condition
    """)
    st.markdown(
        "**Mapping safety**: Exact normalized matches are assigned before fuzzy suggestions. "
        "Financial families (`PAY_0..PAY_6`, `BILL_AMT1..6`, `PAY_AMT1..6`) cannot cross-map. "
        "`client_id` is optional and a stable row identifier is generated when missing."
    )

    # -- Credit risk ------------------------------------------------------------
    st.markdown("### Credit risk workflow")
    st.markdown(
        "Upload labeled historical credit records. The system trains a classifier that "
        "outputs a risk score (0-1) and a tier (LOW / MEDIUM / HIGH) per customer. "
        "SHAP-based explainability highlights the features driving each score with "
        "quantified contribution values. The recommendation engine suggests actions "
        "(e.g. request additional documents, approve with conditions) filtered through "
        "your company's mandatory rules and forbidden-action keywords. An AI Summary "
        "section generates a natural language portfolio assessment using an LLM when "
        "an API key is configured, or a template-based summary otherwise."
    )
    st.markdown("**Available models**: XGBoost (default), LightGBM, Boosted, Random Forest, Extra Trees, Baseline (Logistic Regression).")
    st.markdown("**Evaluation metrics**: ROC-AUC, PR-AUC, Accuracy, F1, Precision, Recall, Brier Score, confusion matrix.")
    st.markdown("**Optional features**: Threshold optimization to maximize F1/PR-AUC, controlled augmentation experiment.")

    # -- Demand workflow --------------------------------------------------------
    st.markdown("### Demand workflow")
    st.markdown(
        "Upload historical sales or consumption data. The system trains a regressor that "
        "forecasts unit demand per period and flags anomalies and stockout risks. "
        "Evaluation metrics (MAE, RMSE, WAPE, R2) quantify forecast accuracy. "
        "SHAP-based explainability shows per-period feature contributions. "
        "The recommendation engine surfaces supply-chain actions such as pre-order "
        "triggers or safety-stock adjustments. A forward projection section allows "
        "iterative multi-step forecasting (7, 14, or 30 days ahead). "
        "Revenue projection multiplies predicted units by the configured per-unit price "
        "to estimate future revenue trends. An AI Summary section generates a natural "
        "language evaluation narrative."
    )
    st.markdown("**Available models**: Boosted (HistGradientBoosting), LightGBM, Random Forest, Baseline (Ridge).")
    st.markdown("**Evaluation metrics**: MAE, RMSE, WAPE, R2.")
    st.markdown("**Forward projection**: Iterative multi-step forecasting feeding predictions back as lag features.")
    st.markdown("**Revenue estimation**: `estimated_revenue = predicted_units * price_per_unit`.")

    # -- Training ---------------------------------------------------------------
    st.markdown("### Training and model selection")
    st.markdown(
        "The Training page supports single-model, train-all, and grid-search modes. "
        "In train-all mode every available algorithm (XGBoost, LightGBM, Random Forest, "
        "Boosted Trees, etc.) is trained and the best composite score wins. "
        "Optional threshold optimization sweeps decision boundaries on the holdout to "
        "maximize F1 and PR-AUC. A controlled augmentation experiment can be run to "
        "measure whether synthetic minority-class examples improve recall without "
        "degrading precision."
    )

    # -- Governance -------------------------------------------------------------
    st.markdown("### Governance and versioning")
    st.markdown(
        "Each saved model version records its metrics, hyperparameters, data summary, "
        "and experiment type. The History page lists all versions and allows one-click "
        "activation or rollback. The Policies page lets administrators define mandatory "
        "recommendation rules, forbidden action keywords, whether human approval is "
        "required, and the per-unit price for revenue projections."
    )
    st.markdown("**Admin fallback**: Company users automatically see admin-trained models when they have no models of their own. `load_latest_with_admin_fallback()` handles this transparently.")

    # -- Audit -----------------------------------------------------------------
    st.markdown("### Audit logging")
    st.markdown(
        "Every security-relevant and operational event is recorded in an append-only "
        "audit log: login attempts, sign-ups, sign-outs, model training runs, model "
        "activations, and policy changes. Administrators can filter and review these "
        "events from the Audit log page."
    )

    # -- Explainability & NLG ---------------------------------------------------
    st.markdown("### Explainability (SHAP)")
    st.markdown(
        "The `src/services/explainer.py` module provides pipeline-aware SHAP computation. "
        "Tree-based models (XGBoost, LightGBM, Random Forest, HistGradientBoosting) use "
        "`TreeExplainer`. Linear models use `LinearExplainer`. All other models fall back "
        "to `KernelExplainer` with a background sample. For forecast models with "
        "`ColumnTransformer` preprocessing, SHAP values are aggregated back to original "
        "feature names via `_aggregate_ohe_shap`."
    )

    st.markdown("### Natural Language Generation")
    st.markdown(
        "The `src/services/nlg.py` module generates natural-language summaries. When an "
        "OpenRouter API key is configured (via `OPENROUTER_API_KEY` in `.env`), the "
        "system calls the OpenRouter chat completion endpoint. When no key is present, "
        "deterministic template-based summaries are used instead."
    )

    # -- Role-based access ------------------------------------------------------
    st.markdown("### Role-based access")
    st.markdown("""
    | Role | Available pages |
    |------|-----------------|
    | Admin | Dashboard, Credit, Demand, Predict, Training, Policies, History, Help, Audit |
    | Company | Dashboard, Credit, Demand, Predict |
    """)
    st.markdown(
        "Access is controlled via session state (`ROLE_KEY`, `COMPANY_KEY`) set during "
        "sign-in. The sidebar automatically shows the correct navigation items for the "
        "current role."
    )

    # -- Quick reference --------------------------------------------------------
    st.markdown("### Quick reference")

    st.markdown("""
    1. **Configure workspace** -- Set company name, currency, approval requirements, and unit price on the Policies page.
    2. **Upload training data** -- Provide labeled historical records on the Training page (or load a sample dataset).
    3. **Map and validate fields** -- Confirm the auto-suggested column mapping; resolve any invalid-family errors.
    4. **Train a model** -- Choose single-model, train-all, or grid-search. Review holdout metrics before saving.
    5. **Activate the model** -- Use the History page to set the newly trained version as the active model.
    6. **Run predictions** -- Upload new records on Credit risk or Demand. The active model scores them without retraining.
    7. **Review SHAP explanations** -- Per-record feature contribution charts show what drives each prediction.
    8. **Read the AI Summary** -- Natural language portfolio or demand assessment generated via LLM or template fallback.
    9. **Project forward** -- On the Demand page, run iterative multi-step forecasts for 7, 14, or 30 days ahead.
    10. **Estimate revenue** -- Convert unit forecasts to revenue projections using the configured per-unit price.
    11. **Review recommendations** -- The governance engine applies company rules. Human approval can be enforced.
    12. **Audit events** -- Administrators can review login, training, activation, and policy events on the Audit log page.
    13. **Roll back if needed** -- History keeps every version. Reactivate a prior model at any time.
    """)

    st.markdown("---")
    st.markdown(
        "<small>Built for organizations that need auditable, versioned ML decisions "
        "with human oversight at every consequential step.</small>",
        unsafe_allow_html=True,
    )
