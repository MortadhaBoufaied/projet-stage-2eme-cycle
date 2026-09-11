"""Natural Language Generation service for financial summaries.

Uses OpenRouter API (OpenAI-compatible) when an API key is configured.
Falls back to deterministic template-based summaries when no key is available
or when the API call fails.
"""
from __future__ import annotations

import logging
from typing import Optional

from src.config import OPENROUTER_API_KEY, OPENROUTER_MODEL

_LOG = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

_CREDIT_SYSTEM = (
    "You are a senior financial analyst assistant embedded in an ERP system. "
    "Write concise, professional summaries for portfolio risk assessments. "
    "Use plain language suitable for a financial manager. No bullet lists; "
    "use short paragraphs. Do not fabricate data -- only reference the "
    "figures provided."
)

_CREDIT_USER = """\
Portfolio size: {n_records} customers
Risk distribution: {low} low-risk, {medium} medium-risk, {high} high-risk
Model: {model_type} | ROC-AUC: {roc_auc} | F1: {f1}
Top risk indicators (most common across portfolio): {indicators}

Write a 3-4 paragraph summary covering:
1. Overall portfolio risk posture
2. Key patterns in the risk indicators
3. Specific recommendations by risk tier
4. Suggested next steps for the financial manager
"""

_DEMAND_SYSTEM = (
    "You are a demand planning analyst assistant embedded in an ERP system. "
    "Write concise, professional summaries for demand forecast evaluations. "
    "Use plain language suitable for a supply-chain manager. No bullet lists; "
    "use short paragraphs. Do not fabricate data -- only reference the "
    "figures provided."
)

_DEMAND_USER = """\
Evaluation period: {n_periods} records evaluated
Forecast accuracy: MAE {mae}, RMSE {rmse}, WAPE {wape}, R2 {r2}
Anomalies detected: {anomalies} | Stockout risks: {stockouts}
Model: {model_type}

Write a 3-4 paragraph summary covering:
1. Overall forecast quality assessment
2. Anomaly and stockout risk patterns
3. Specific supply-chain recommendations
4. Suggested next steps for the supply-chain manager
"""

# ---------------------------------------------------------------------------
# Template fallback (no API call)
# ---------------------------------------------------------------------------


def _credit_template(records: list[dict], metrics: dict) -> str:
    """Deterministic template-based credit summary when no API key is set."""
    n = len(records)
    low = sum(1 for r in records if r.get("risk_tier") == "LOW_RISK")
    med = sum(1 for r in records if r.get("risk_tier") == "MEDIUM_RISK")
    high = sum(1 for r in records if r.get("risk_tier") == "HIGH_RISK")
    model_type = metrics.get("model_type", "N/A")
    roc = metrics.get("ROC_AUC", "N/A")
    f1 = metrics.get("F1_Score", "N/A")

    return (
        f"The portfolio contains {n} customer records evaluated using the "
        f"{model_type} credit risk model. The model achieves a ROC-AUC of "
        f"{roc} and an F1 score of {f1}. "
        f"Risk distribution: {low} low-risk, {med} medium-risk, and {high} "
        f"high-risk customers.\n\n"
        f"The majority of the portfolio ({low}/{n}) falls in the low-risk "
        f"category, indicating generally healthy credit behavior. However, "
        f"{high} customers are classified as high-risk and require immediate "
        f"attention.\n\n"
        f"Recommended actions: Review all high-risk accounts for potential "
        f"collection or restructuring. Schedule periodic monitoring for "
        f"medium-risk accounts. Maintain standard terms for low-risk "
        f"customers.\n\n"
        f"Next steps: Prioritize outreach to the {high} high-risk customers, "
        f"request updated financial statements, and update credit limits "
        f"based on the latest risk assessment."
    )


def _demand_template(metrics: dict, anomalies: int, stockouts: int, model_type: str) -> str:
    """Deterministic template-based demand summary when no API key is set."""
    mae = metrics.get("MAE", "N/A")
    rmse = metrics.get("RMSE", "N/A")
    wape = metrics.get("WAPE", "N/A")
    r2 = metrics.get("R2", "N/A")
    n_test = metrics.get("n_test", "N/A")

    return (
        f"The {model_type} forecast model was evaluated on {n_test} test "
        f"periods. Accuracy metrics: MAE {mae}, RMSE {rmse}, WAPE {wape}, "
        f"R2 {r2}. "
        f"The model detected {anomalies} anomalous demand periods and "
        f"{stockouts} stockout risk events.\n\n"
        f"An anomaly rate above 5% may indicate volatile demand patterns "
        f"or data quality issues that warrant investigation. Stockout risk "
        f"events suggest inventory levels were insufficient relative to "
        f"predicted demand.\n\n"
        f"Recommended actions: Investigate flagged anomalies for root causes "
        f"(promotions, weather, supply disruptions). Adjust reorder points "
        f"for products with recurring stockout risk. Consider increasing "
        f"safety stock for high-volatility items.\n\n"
        f"Next steps: Review anomaly root causes with the operations team, "
        f"update reorder parameters in the ERP, and retrain the model with "
        f"corrected data if systemic issues are found."
    )


# ---------------------------------------------------------------------------
# OpenRouter API call
# ---------------------------------------------------------------------------


def _call_openrouter(system_prompt: str, user_prompt: str) -> Optional[str]:
    """Call the OpenRouter chat completion endpoint. Returns None on failure."""
    if not OPENROUTER_API_KEY:
        return None

    try:
        import requests as _requests

        response = _requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://finance-decision-studio.local",
                "X-Title": "Finance Decision Studio",
            },
            json={
                "model": OPENROUTER_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": 800,
                "temperature": 0.3,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        _LOG.warning("OpenRouter API call failed, using template fallback: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_credit_summary(records: list[dict], metrics: dict) -> str:
    """Generate a financial summary for a scored credit portfolio.

    Args:
        records: List of result dicts with keys risk_score, risk_tier, etc.
        metrics: Model metrics dict with ROC_AUC, F1_Score, model_type, etc.

    Returns:
        A multi-paragraph natural language summary.
    """
    indicators = _extract_top_indicators(records)
    user_prompt = _CREDIT_USER.format(
        n_records=len(records),
        low=sum(1 for r in records if r.get("risk_tier") == "LOW_RISK"),
        medium=sum(1 for r in records if r.get("risk_tier") == "MEDIUM_RISK"),
        high=sum(1 for r in records if r.get("risk_tier") == "HIGH_RISK"),
        model_type=metrics.get("model_type", "N/A"),
        roc_auc=metrics.get("ROC_AUC", "N/A"),
        f1=metrics.get("F1_Score", "N/A"),
        indicators=indicators,
    )

    api_result = _call_openrouter(_CREDIT_SYSTEM, user_prompt)
    if api_result:
        return api_result

    return _credit_template(records, metrics)


def generate_demand_summary(metrics: dict, anomalies: int, stockouts: int, model_type: str = "N/A") -> str:
    """Generate a financial summary for a demand forecast evaluation.

    Args:
        metrics: Evaluation metrics dict with MAE, RMSE, WAPE, R2, n_test.
        anomalies: Number of detected anomaly periods.
        stockouts: Number of detected stockout risk events.
        model_type: Name of the model used.

    Returns:
        A multi-paragraph natural language summary.
    """
    user_prompt = _DEMAND_USER.format(
        n_periods=metrics.get("n_test", "N/A"),
        mae=metrics.get("MAE", "N/A"),
        rmse=metrics.get("RMSE", "N/A"),
        wape=metrics.get("WAPE", "N/A"),
        r2=metrics.get("R2", "N/A"),
        anomalies=anomalies,
        stockouts=stockouts,
        model_type=model_type,
    )

    api_result = _call_openrouter(_DEMAND_SYSTEM, user_prompt)
    if api_result:
        return api_result

    return _demand_template(metrics, anomalies, stockouts, model_type)


def _extract_top_indicators(records: list[dict], top_n: int = 5) -> str:
    """Extract the most frequent key indicator features across records."""
    from collections import Counter

    counter: Counter = Counter()
    for r in records:
        raw = r.get("key_indicators", "")
        if not isinstance(raw, str):
            continue
        for part in raw.split("|"):
            feature = part.strip().split(":")[0].strip()
            if feature:
                counter[feature] += 1

    if not counter:
        return "N/A"

    top = counter.most_common(top_n)
    return ", ".join(f"{feat} ({count} records)" for feat, count in top)
