# ML Intelligence Center

A two-sided Streamlit platform for governed model training and simple company analysis.

## Product structure

- **Admin, four areas:** Dashboard, Training & Evaluation, Model Registry, Global Analyses.
- **Company, two pages:** Templates & Upload, Analysis & Results.
- **Models:** payment-risk classification and revenue/demand forecasting.
- **Governance:** deterministic metrics, structured SLM interpretation, saved model versions, explicit activation, tenant-isolated analyses, filtered exports.

## Architecture

`src/ui` contains presentation only. `src/services` separates authentication, stable schemas, validation, modeling, metrics, model registry, SLM interpretation, and company workspaces. Model artifacts are global and governed by Admin. Analysis artifacts are stored under `artifacts/workspaces/<company_id>/`.

## Installation

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run src/ui/app.py
```

On Windows, `RUN_PROJECT.bat` performs the same startup. Default local URL is `http://localhost:8501`.

## Environment

Set `ADMIN_EMAIL` and `ADMIN_PASSWORD`. Optional settings include `SESSION_MINUTES`, `MAX_UPLOAD_MB`, `SLM_ENDPOINT`, and `SLM_MODEL`. Never commit `.env`.

## Accounts and roles

The configured Admin account is created on startup. Companies create their own workspace from the login screen. Company accounts cannot reach training, algorithms, hyperparameters, or the model registry.

## Training

1. Sign in as Admin.
2. Open **Training & Evaluation**.
3. Select payment risk or demand forecasting.
4. Upload one or more CSV files with identical columns.
5. Review full-file validation.
6. Choose algorithms and train.
7. Compare validation metrics and inspect untouched test metrics.
8. Save the recommended version.
9. Activate it from **Model Registry**.

Classification uses stratified 70/15/15 partitions and selects by validation PR-AUC then F1. Forecasting uses chronological 70/15/15 partitions and selects by lowest validation WAPE. The untouched test partition is reported separately.

## Company analysis

1. Download an empty template from **Templates & Upload**.
2. Use the embedded field documentation to fill it.
3. Upload and validate it.
4. Open **Analysis & Results** and run the active saved model.
5. Review deterministic results and SLM or fallback interpretation.
6. Filter records.
7. Download CSV or Excel. Exports contain only current filtered rows.

## Supported schemas

### Payment risk

The model uses `LIMIT_BAL`, `AGE`, `EDUCATION`, `MARRIAGE`, `PAY_0`, `PAY_2` through `PAY_6`, `BILL_AMT1` through `BILL_AMT6`, and `PAY_AMT1` through `PAY_AMT6`. Training also requires `default_next_month`. `client_id` is retained for traceability but is not a model feature.

### Demand forecasting

Required fields are `date`, `store_id`, `product_id`, `category`, `region`, `inventory_level`, and `units_sold`. `units_ordered` and `price` are optional predictors. The included original training data is accepted through documented display-name aliases.

## Local SLM

The SLM receives only structured verified metrics and quality facts. It cannot change predictions or metrics. Configure an Ollama-compatible HTTP endpoint, for example:

```bash
ollama pull qwen2.5:1.5b
# Set SLM_ENDPOINT=http://127.0.0.1:11434/api/generate
```

If unavailable, a deterministic rule-based assessment is used and labelled as such.

## Tests

```bash
pytest
python -m compileall -q src
```

## Included data

`data/training/` contains the two user-provided training datasets. They are not automatically trained during company analysis. Admin explicitly trains, evaluates, saves, and activates models.

## Safety and limitations

Outputs are decision support, not guaranteed business decisions. Feature importance and predictive signals must not be interpreted as causation. A responsible employee must review consequential actions.
