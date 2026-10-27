class RecommendationEngine:
    def credit(self, item):
        tier=item["risk_tier"]
        actions={"HIGH_RISK":["Request manual credit review.","Reduce exposure and tighten payment terms.","Increase collection monitoring."],"MEDIUM_RISK":["Send early reminders.","Monitor repayment behavior monthly.","Consider an early-payment incentive."],"LOW_RISK":["Maintain standard controls.","Consider normal commercial terms."]}[tier]
        return {"risk_tier":tier,"risk_score":item["risk_score"],"recommended_actions":actions,"note":"Decision support only. A responsible employee should review the recommendation."}
    def forecast(self, row):
        actions=[]
        if int(row.get("is_stockout_risk",0)): actions.append("Review replenishment and safety-stock levels.")
        if int(row.get("is_anomaly",0)): actions.append("Investigate the demand deviation, promotion, weather, pricing, and data quality.")
        return actions or ["No exceptional action detected."]
