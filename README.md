# Finance Decision Studio

Governed ML platform for credit-risk scoring and cashflow/demand forecasting. Built with Streamlit (dark theme), SQLite-backed persistence, role-based access control (admin / company), SHAP explainability, and natural-language generation.

## Quick start

1. Copy `.env.example` to `.env` and set the administrator credentials.
2. Install dependencies: `python -m pip install -r requirements.txt`
3. Validate: `python -m src.smoke_check`
4. Launch: `python -m streamlit run src/ui/app.py`

## Provided sample data

Three CSV files are included in `data/`:

| File | Agent | Records | Description |
|------|-------|---------|-------------|
| `data/UCI_Credit_Card.csv` | Credit risk | 30,000 | UCI Credit Card default dataset — repayment status (`PAY_0`, `PAY_2`–`PAY_6`), bill amounts, payment amounts |
| `data/credit_default_risk.csv` | Credit risk | 30,000 | Synthetic credit-risk dataset with `client_id`, `LIMIT_BAL`, `AGE`, `EDUCATION`, `MARRIAGE`, repayment fields, `default_next_month` |
| `data/retail_inventory_forecasting.csv` | Demand forecast | 72,000 | Retail inventory data — `date`, `store_id`, `product_id`, `category`, `region`, `units_sold`, `inventory_level`, `promotions_holidays`, `weather_conditions` |

See `data/dataset_metadata.json` for dataset-level metadata.

## Data schema

### Credit-risk CSV columns (expected by the app)
- `client_id` (optional) — stable row identifier; auto-generated when missing
- `LIMIT_BAL` — credit limit
- `AGE` — age
- `EDUCATION` — education level
- `MARRIAGE` — marital status
- `PAY_0`, `PAY_2`, `PAY_3`, `PAY_4`, `PAY_5`, `PAY_6` — repayment status (note: `PAY_1` is **not** used)
- `BILL_AMT1`–`BILL_AMT6` — bill statement amounts (6 months)
- `PAY_AMT1`–`PAY_AMT6` — previous payment amounts (6 months)
- `default_next_month` (or similar target) — binary label

### Demand-forecast CSV columns (expected by the app)
- `date` — period date
- `store_id` — store identifier
- `product_id` — product identifier
- `category` — product category
- `region` — region
- `units_sold` — target value
- `inventory_level` — current stock
- `promotions_holidays` — promotion/holiday flag
- `weather_conditions` — weather condition

**Mapping safety**: Exact normalized matches are assigned before fuzzy suggestions. Financial families (`PAY_0..PAY_6`, `BILL_AMT1..6`, `PAY_AMT1..6`) cannot cross-map. `client_id` is optional and a stable row identifier is generated when missing.

## Features

### Credit-risk agent
1. Upload CSV or use sample data (`data/credit_default_risk.csv`, `data/UCI_Credit_Card.csv`)
2. Field auto-mapping with alias support
3. Train XGBoost (default), LightGBM, Boosted, Random Forest, Extra Trees, or Baseline
4. Single-model, train-all, or grid-search modes
5. Optional threshold optimization and controlled augmentation experiment
6. Evaluation metrics: ROC-AUC, PR-AUC, Accuracy, F1, Precision, Recall, Brier Score, confusion matrix
7. SHAP-based explainability per customer
8. AI natural-language portfolio summary (OpenRouter API or template fallback)
9. Recommendation engine applying company rules and forbidden-action keywords
10. Human-approval enforcement configurable in Policies

### Demand-forecast agent
1. Upload CSV or use sample data (`data/retail_inventory_forecasting.csv`)
2. Field auto-mapping
3. Train Boosted, LightGBM, Random Forest, or Baseline
4. Evaluation metrics: MAE, RMSE, WAPE, R2
5. Anomaly detection and stockout-risk flagging
6. **Forward projection** — iterative multi-step forecasting (7, 14, or 30 days ahead)
7. **Revenue estimation** — multiply predicted units by configured per-unit price
8. SHAP-based per-period feature contributions
9. AI natural-language demand evaluation summary
10. Recommendation engine with supply-chain actions

### Governance & operations
- **Training page** — train-all, model comparison, best composite-score selection
- **History page** — all model versions with one-click activate/rollback; admin fallback (company users see admin-trained models when they have none)
- **Policies page** — configure currency, language, thresholds, human approval, forbidden actions, recommendation rules, per-unit price
- **Audit log page** — append-only record of login, training, activation, and policy events; filterable by event type and username
- **Help page** — pipeline documentation, workflows, and quick reference

### Role-based access
| Role | Pages |
|------|-------|
| Admin | Dashboard, Credit, Demand, Predict, Training, Policies, History, Help, Audit |
| Company | Dashboard, Credit, Demand, Predict |

### Explainability & NLG
- SHAP via `src/services/explainer.py` — TreeExplainer (tree models), LinearExplainer (logistic), KernelExplainer (fallback)
- NLG via `src/services/nlg.py` — OpenRouter API (OpenAI-compatible) with deterministic template fallback

## Architecture

- `src/agents/` — `CreditRiskAgent`, `CashflowForecastAgent`
- `src/services/` — `audit`, `auth`, `company_profile`, `db`, `explainer`, `model_registry`, `nlg`, `recommendation_policy`, `schema`
- `src/ui/` — `app.py` (router), `components/` (display, fields, sidebar), `pages/` (9 modules), `login.py`
- `src/config.py` — `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `RANDOM_STATE`
- `src/services/db.py` — shared SQLite with users, model_versions, audit_log tables

## Setup

1. Copy `.env.example` to `.env` and change the administrator password.
2. Install requirements: `python -m pip install -r requirements.txt`.
3. Run validation: `python -m src.smoke_check`.
4. Start: `python -m streamlit run src/ui/app.py`.
