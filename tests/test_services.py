"""Unit tests for backend services: audit, explainer, NLG, recommendation policy.

Covers: log_event/query_events, compute_shap_values, generate_credit_summary,
generate_demand_summary, RecommendationPolicy.apply, and edge cases.
"""
from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db_dir(tmp_path):
    """Redirect the shared SQLite DB to a temporary artifacts dir."""
    import src.services.db as db_mod
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    db_mod._DB_DIR = artifacts
    db_mod._DB_PATH = artifacts / "users.db"
    # Ensure audit_log table exists
    conn = sqlite3.connect(str(artifacts / "users.db"))
    conn.execute("""CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT, event_type TEXT, username TEXT, role TEXT,
        company_id TEXT, detail TEXT
    )""")
    conn.commit()
    conn.close()
    return artifacts


@pytest.fixture
def company_profile():
    """Return a standard CompanyProfile for policy tests."""
    from src.services.company_profile import CompanyProfile
    return CompanyProfile(
        company_id="testco",
        display_name="Test Company",
        currency="TND",
        language="English",
        review_threshold=0.5,
        high_risk_threshold=0.6,
        require_human_approval=False,
        recommendation_rules=[],
        forbidden_actions=[],
    )


# ---------------------------------------------------------------------------
# Audit service
# ---------------------------------------------------------------------------

class TestAuditService:
    def test_log_event_writes_to_db(self, db_dir):
        from src.services.audit import log_event, query_events
        log_event("auth.sign_in", username="alice", role="company", company_id="acme")
        events = query_events(event_type="auth.sign_in", limit=10)
        assert len(events) == 1
        assert events[0]["username"] == "alice"
        assert events[0]["event_type"] == "auth.sign_in"

    def test_query_events_returns_newest_first(self, db_dir):
        from src.services.audit import log_event, query_events
        log_event("auth.sign_in", username="alice", company_id="acme")
        log_event("auth.sign_in", username="bob", company_id="acme")
        events = query_events(limit=10)
        assert events[0]["username"] == "bob"
        assert events[1]["username"] == "alice"

    def test_query_events_filters_by_username(self, db_dir):
        from src.services.audit import log_event, query_events
        log_event("auth.sign_in", username="alice", company_id="acme")
        log_event("auth.sign_in", username="bob", company_id="acme")
        events = query_events(username="alice", limit=10)
        assert len(events) == 1
        assert events[0]["username"] == "alice"

    def test_query_events_filters_by_event_type(self, db_dir):
        from src.services.audit import log_event, query_events
        log_event("model.train", username="admin", company_id="acme")
        log_event("auth.sign_in", username="admin", company_id="acme")
        events = query_events(event_type="model.train", limit=10)
        assert len(events) == 1
        assert events[0]["event_type"] == "model.train"

    def test_query_events_limit_respected(self, db_dir):
        from src.services.audit import log_event, query_events
        for i in range(5):
            log_event("auth.sign_in", username=f"user{i}", company_id="acme")
        events = query_events(limit=2)
        assert len(events) == 2

    def test_log_event_with_detail(self, db_dir):
        from src.services.audit import log_event, query_events
        detail = {"model_type": "xgboost", "accuracy": 0.95}
        log_event("model.train", username="admin", detail=detail)
        events = query_events(limit=1)
        assert events[0]["detail"]["model_type"] == "xgboost"
        assert events[0]["detail"]["accuracy"] == 0.95

    def test_log_event_detail_none(self, db_dir):
        from src.services.audit import log_event, query_events
        log_event("auth.sign_in", username="alice")
        events = query_events(limit=1)
        assert "detail" not in events[0] or events[0].get("detail") is None

    def test_query_events_empty_returns_empty_list(self, db_dir):
        from src.services.audit import query_events
        events = query_events(limit=10)
        assert events == []

    def test_log_event_swallows_exceptions(self, db_dir):
        """log_event should never raise, even if DB is unavailable."""
        from src.services.audit import log_event
        import src.services.db as db_mod
        original = db_mod._DB_PATH
        db_mod._DB_PATH = Path("/nonexistent/DB.sqlite")
        try:
            log_event("auth.sign_in")  # should not raise
        finally:
            db_mod._DB_PATH = original

    def test_audit_event_constants(self):
        from src.services.audit import AuditEvent
        assert AuditEvent.AUTH_SIGN_IN == "auth.sign_in"
        assert AuditEvent.AUTH_SIGN_IN_FAIL == "auth.sign_in_fail"
        assert AuditEvent.AUTH_SIGN_UP == "auth.sign_up"
        assert AuditEvent.AUTH_SIGN_OUT == "auth.sign_out"
        assert AuditEvent.MODEL_TRAIN == "model.train"
        assert AuditEvent.MODEL_ACTIVATE == "model.activate"
        assert AuditEvent.POLICY_UPDATE == "policy.update"


# ---------------------------------------------------------------------------
# Explainer service
# ---------------------------------------------------------------------------

class TestExplainerService:
    def test_compute_shap_values_returns_none_on_exception(self):
        """SHAP computation on a non-fitted model should return None, not crash."""
        from src.services.explainer import compute_shap_values
        model = MagicMock()
        model.predict_proba.return_value = np.array([[0.3], [0.7]])
        model.steps = []
        type(model).__name__ = "UnknownModel"
        X = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        result = compute_shap_values(model, X)
        assert result is None

    def test_compute_shap_values_with_tree_explainer(self):
        """TreeExplainer path returns a list of per-record indicator dicts."""
        from src.services.explainer import compute_shap_values
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.datasets import make_classification

        X, y = make_classification(n_samples=100, n_features=5, random_state=42)
        df = pd.DataFrame(X, columns=["f0", "f1", "f2", "f3", "f4"])
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(df, y)

        result = compute_shap_values(model, df, top_k=3)
        assert result is not None
        assert len(result) == len(df)
        for record in result:
            assert len(record) <= 3
            for ind in record:
                assert "feature" in ind
                assert "shap_value" in ind
                assert "feature_value" in ind
                assert "direction" in ind
                assert ind["direction"] in ("increases_risk", "decreases_risk")

    def test_compute_shap_values_top_k_respected(self):
        """top_k parameter limits the number of indicators per record."""
        from src.services.explainer import compute_shap_values
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.datasets import make_classification

        X, y = make_classification(n_samples=50, n_features=10, random_state=42)
        df = pd.DataFrame(X, columns=[f"f{i}" for i in range(10)])
        model = RandomForestClassifier(n_estimators=5, random_state=42)
        model.fit(df, y)

        result = compute_shap_values(model, df, top_k=2)
        assert result is not None
        for record in result:
            assert len(record) <= 2


# ---------------------------------------------------------------------------
# NLG service
# ---------------------------------------------------------------------------

class TestNlgService:
    def test_generate_credit_summary_returns_string(self):
        """generate_credit_summary always returns a non-empty string."""
        from src.services.nlg import generate_credit_summary
        records = [
            {"risk_score": 0.3, "risk_tier": "LOW_RISK"},
            {"risk_score": 0.7, "risk_tier": "HIGH_RISK"},
        ]
        metrics = {"model_type": "xgboost", "ROC_AUC": 0.92, "F1_Score": 0.88}
        result = generate_credit_summary(records, metrics)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_credit_summary_without_api_key(self, monkeypatch):
        """When no API key is configured, the template fallback is used."""
        from src.services.nlg import generate_credit_summary
        monkeypatch.setattr("src.config.OPENROUTER_API_KEY", "")
        records = [{"risk_score": 0.2, "risk_tier": "LOW_RISK"}]
        metrics = {"model_type": "lightgbm", "ROC_AUC": 0.85, "F1_Score": 0.80}
        result = generate_credit_summary(records, metrics)
        assert isinstance(result, str)
        assert len(result) > 20

    def test_generate_demand_summary_returns_string(self):
        """generate_demand_summary always returns a non-empty string."""
        from src.services.nlg import generate_demand_summary
        metrics = {"MAE": 5.0, "RMSE": 7.0, "WAPE": 0.15, "R2": 0.9, "n_test": 30}
        result = generate_demand_summary(metrics, anomalies=3, stockouts=1, model_type="boosted")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_demand_summary_without_api_key(self, monkeypatch):
        """When no API key is configured, the template fallback is used."""
        from src.services.nlg import generate_demand_summary
        monkeypatch.setattr("src.config.OPENROUTER_API_KEY", "")
        metrics = {"MAE": 5.0, "RMSE": 7.0, "WAPE": 0.15, "R2": 0.9, "n_test": 30}
        result = generate_demand_summary(metrics, anomalies=3, stockouts=1)
        assert isinstance(result, str)
        assert "forecast model" in result.lower()

    def test_generate_credit_summary_template_content(self, monkeypatch):
        """Template fallback should include risk tier counts."""
        from src.services.nlg import generate_credit_summary
        monkeypatch.setattr("src.config.OPENROUTER_API_KEY", "")
        records = [
            {"risk_score": 0.2, "risk_tier": "LOW_RISK"},
            {"risk_score": 0.5, "risk_tier": "MEDIUM_RISK"},
            {"risk_score": 0.8, "risk_tier": "HIGH_RISK"},
        ]
        metrics = {"model_type": "xgboost", "ROC_AUC": 0.9, "F1_Score": 0.85}
        result = generate_credit_summary(records, metrics)
        assert "low-risk" in result.lower()


# ---------------------------------------------------------------------------
# Recommendation policy
# ---------------------------------------------------------------------------

class TestRecommendationPolicy:
    def test_apply_adds_company_policy(self, company_profile):
        from src.services.recommendation_policy import RecommendationPolicy
        policy = RecommendationPolicy()
        recommendation = {"recommended_actions": ["request_docs"], "status": "PENDING"}
        result = policy.apply(recommendation, company_profile)
        assert "company_policy" in result
        assert result["company_policy"]["currency"] == "TND"
        assert result["status"] == "ADVISORY"

    def test_apply_blocks_forbidden_actions(self, company_profile):
        """Forbidden action keywords should be stripped from recommendations."""
        from src.services.recommendation_policy import RecommendationPolicy
        from src.services.company_profile import CompanyProfile
        profile = CompanyProfile(
            company_id="testco", forbidden_actions=["approve"],
            recommendation_rules=[], require_human_approval=False,
        )
        policy = RecommendationPolicy()
        recommendation = {"recommended_actions": ["request_additional_docs", "approve_loan"]}
        result = policy.apply(recommendation, profile)
        actions = result["recommended_actions"]
        assert not any("approve" in a.lower() for a in actions)

    def test_apply_adds_recommendation_rules(self, company_profile):
        """Custom recommendation rules should be added to actions."""
        from src.services.recommendation_policy import RecommendationPolicy
        from src.services.company_profile import CompanyProfile
        profile = CompanyProfile(
            company_id="testco", recommendation_rules=["auto_review"],
            forbidden_actions=[], require_human_approval=False,
        )
        policy = RecommendationPolicy()
        recommendation = {"recommended_actions": []}
        result = policy.apply(recommendation, profile)
        assert "auto_review" in result["recommended_actions"]

    def test_apply_sets_human_review_when_required(self, company_profile):
        """When require_human_approval is True, status should be REQUIRES_HUMAN_REVIEW."""
        from src.services.recommendation_policy import RecommendationPolicy
        from src.services.company_profile import CompanyProfile
        profile = CompanyProfile(
            company_id="testco", require_human_approval=True,
            recommendation_rules=[], forbidden_actions=[],
        )
        policy = RecommendationPolicy()
        recommendation = {"recommended_actions": ["request_docs"]}
        result = policy.apply(recommendation, profile)
        assert result["status"] == "REQUIRES_HUMAN_REVIEW"

    def test_apply_does_not_duplicate_rules(self, company_profile):
        """Rules already present in actions should not be duplicated."""
        from src.services.recommendation_policy import RecommendationPolicy
        from src.services.company_profile import CompanyProfile
        profile = CompanyProfile(
            company_id="testco", recommendation_rules=["auto_review"],
            forbidden_actions=[], require_human_approval=False,
        )
        policy = RecommendationPolicy()
        recommendation = {"recommended_actions": ["auto_review"]}
        result = policy.apply(recommendation, profile)
        assert result["recommended_actions"].count("auto_review") == 1

    def test_apply_returns_new_dict_not_mutated(self, company_profile):
        """apply() should not mutate the input recommendation dict."""
        from src.services.recommendation_policy import RecommendationPolicy
        policy = RecommendationPolicy()
        original = {"recommended_actions": ["request_docs"]}
        policy.apply(original, company_profile)
        assert original == {"recommended_actions": ["request_docs"]}
