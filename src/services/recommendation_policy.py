from __future__ import annotations

from src.services.company_profile import CompanyProfile


class RecommendationPolicy:
    """Applies explicit company rules to model recommendations without retraining."""

    def apply(self, recommendation: dict, profile: CompanyProfile) -> dict:
        result = dict(recommendation)
        actions = list(result.get("recommended_actions", result.get("action_plan", [])))
        blocked = [rule.lower() for rule in profile.forbidden_actions if rule.strip()]
        actions = [action for action in actions if not any(term in action.lower() for term in blocked)]
        actions.extend(rule for rule in profile.recommendation_rules if rule.strip() and rule not in actions)
        result["recommended_actions"] = actions
        result["company_policy"] = {
            "currency": profile.currency,
            "language": profile.language,
            "human_approval_required": profile.require_human_approval,
        }
        result["status"] = "REQUIRES_HUMAN_REVIEW" if profile.require_human_approval else "ADVISORY"
        return result
