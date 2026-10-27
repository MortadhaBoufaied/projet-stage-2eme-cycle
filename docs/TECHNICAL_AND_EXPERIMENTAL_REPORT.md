# Technical and Experimental Report

## Scope
The prototype implements two governed financial decision-support agents: Payment Risk Assessment and Cashflow / Revenue / Demand Forecasting. It is an intelligence layer rather than a full ERP.

## Architecture
The Streamlit UI delegates authentication, validation, feature engineering, model training, model registry, inference, explainability, future projection, alerts, SLM interpretation, and tenant-isolated storage to services under `src/services`.

## Payment Risk Agent
The agent supports historical invoice input, leakage-safe customer history aggregates, probability scoring, LOW/MEDIUM/HIGH tiers, model-grounded local sensitivity factors, and human-reviewed recommendations.

## Forecast Agent
The agent supports administrator-selected numeric targets including demand, revenue, cash inflow, cash outflow, and net cashflow when those fields exist in training data. Evaluation remains chronological. The active model can generate recursive future-dated projections for a user-selected horizon, empirical residual-based uncertainty ranges, anomaly alerts, projected-decline alerts, stock exposure alerts, and negative net-cashflow alerts.

## Experimental Protocol
Classification uses separated train, validation, and test partitions, with chronological splitting when reliable event dates exist and stratified splitting otherwise. Forecasting uses chronological partitions. Model selection uses validation evidence only; untouched test metrics are reported after selection.

## Metrics
Payment risk reports PR-AUC, ROC-AUC, F1, recall, precision, specificity, balanced accuracy, MCC, and accuracy. Forecasting reports WAPE, RMSE, MAE, R2, MAPE, and median absolute error.

## Explainability and SLM
Predictions and metrics are deterministic model outputs. Optional administrator-authored column meanings are versioned with the model and supplied as semantic context. The SLM cannot change predictions. If unavailable, deterministic guidance is used.

## Governance and Limitations
Outputs are decision support, not automatic financial decisions. Human approval is required. Confidence ranges are empirical residual ranges, not guaranteed probabilistic intervals. Recursive long-horizon forecasts accumulate uncertainty and must be monitored against actual results.
