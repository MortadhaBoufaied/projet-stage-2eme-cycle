# Finance Decision Studio

Half-light Streamlit application for governed credit-risk and historical demand analysis.

## Setup
1. Copy `.env.example` to `.env` and change the administrator password.
2. Install requirements: `python -m pip install -r requirements.txt`.
3. Run validation: `python -m src.smoke_check`.
4. Start: `python -m streamlit run src/ui/app.py`.

## Mapping safety
Exact normalized matches are assigned before fuzzy suggestions. Financial families cannot cross-map: `PAY_0..PAY_6`, `BILL_AMT1..6`, and `PAY_AMT1..6` remain separate. `client_id` is optional and a stable row identifier is generated when missing.

## Credit repayment schema
The canonical repayment-status columns are `PAY_0`, `PAY_2`, `PAY_3`, `PAY_4`, `PAY_5`, and `PAY_6`. `PAY_1` is not required or generated. The mapping layer uses only uploaded source columns, except for an optional generated `client_id` when no identifier exists.

## UCI credit schema correction
The app reads the uploaded CSV headers at runtime. It does not generate default business columns. For the UCI credit-card dataset, repayment status is exactly `PAY_0`, `PAY_2`, `PAY_3`, `PAY_4`, `PAY_5`, and `PAY_6`. `PAY_1` is not requested, mapped, created, generated, or used by the model. A client identifier is mapped only when a real ID-like source column exists; otherwise the original dataframe index is displayed without modifying the input dataframe.

## Model selection and augmentation
Credit training now defaults to regularized XGBoost with class weighting. Logistic regression and sklearn histogram boosting remain available as transparent benchmarks. After baseline training, the UI can run a controlled augmentation experiment. Synthetic minority rows are created only inside the training partition, with discrete repayment fields copied exactly and small scale-aware perturbations restricted to continuous financial values. The same untouched holdout evaluates both models. The application recommends the augmented challenger only when the combined PR-AUC, ROC-AUC, Brier score, and recall checks improve; otherwise it keeps the original model.
