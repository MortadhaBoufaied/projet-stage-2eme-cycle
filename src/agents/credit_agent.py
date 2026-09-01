from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, average_precision_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.config import RANDOM_STATE
from src.services.schema import CREDIT_FEATURES, CREDIT_TARGET


class CreditRiskAgent:
    def __init__(self, model_type="boosted", review_threshold=0.50, high_risk_threshold=0.60):
        if model_type not in {"baseline", "boosted"}:
            raise ValueError("model_type must be baseline or boosted")
        if not 0 < review_threshold <= high_risk_threshold < 1:
            raise ValueError("Thresholds must satisfy 0 < review <= high < 1")
        self.model_type = model_type
        self.review_threshold = float(review_threshold)
        self.high_risk_threshold = float(high_risk_threshold)
        self.model = None
        self.feature_names = []
        self.reference_medians = {}

    @staticmethod
    def _engineer(df):
        data = df.copy()
        bills = [f"BILL_AMT{i}" for i in range(1, 7)]
        payments = [f"PAY_AMT{i}" for i in range(1, 7)]
        delays = [f"PAY_{i}" for i in range(7)]
        for column in ["LIMIT_BAL", "AGE", "EDUCATION", "MARRIAGE", *bills, *payments, *delays]:
            data[column] = pd.to_numeric(data[column], errors="coerce")
        limit = data["LIMIT_BAL"].abs().replace(0, np.nan)
        bill1 = data["BILL_AMT1"].abs().replace(0, np.nan)
        bill_total = data[bills].abs().sum(axis=1).replace(0, np.nan)
        data["utilization_ratio_1"] = data["BILL_AMT1"] / limit
        data["utilization_ratio_mean"] = data[bills].mean(axis=1) / limit
        data["pay_ratio_1"] = data["PAY_AMT1"] / bill1
        data["pay_ratio_mean"] = data[payments].sum(axis=1) / bill_total
        data["delay_months_max"] = data[delays].max(axis=1)
        data["delay_count"] = (data[delays] > 0).sum(axis=1)
        data["is_young"] = (data["AGE"] < 30).astype(int)
        data["is_grad_school"] = (data["EDUCATION"] == 1).astype(int)
        data["is_married"] = (data["MARRIAGE"] == 1).astype(int)
        return data.replace([np.inf, -np.inf], np.nan)

    def fit(self, train_df):
        data = self._engineer(train_df)
        engineered = ["utilization_ratio_1", "utilization_ratio_mean", "pay_ratio_1", "pay_ratio_mean", "delay_months_max", "delay_count", "is_young", "is_grad_school", "is_married"]
        self.feature_names = [*CREDIT_FEATURES, *engineered]
        x = data[self.feature_names]
        y = pd.to_numeric(data[CREDIT_TARGET], errors="raise").astype(int)
        self.reference_medians = x.median(numeric_only=True).fillna(0).to_dict()
        steps = [("imputer", SimpleImputer(strategy="median"))]
        if self.model_type == "baseline":
            steps += [("scaler", StandardScaler()), ("model", LogisticRegression(max_iter=2000, class_weight="balanced", random_state=RANDOM_STATE))]
        else:
            steps += [("model", HistGradientBoostingClassifier(max_iter=300, learning_rate=.04, max_depth=6, random_state=RANDOM_STATE))]
        self.model = Pipeline(steps).fit(x, y)
        return self

    def predict_proba(self, df):
        if self.model is None:
            raise RuntimeError("Credit model is not fitted")
        return self.model.predict_proba(self._engineer(df)[self.feature_names])[:, 1]

    def predict_risk(self, df):
        probabilities = self.predict_proba(df)
        tiers = np.where(probabilities < self.review_threshold, "LOW_RISK", np.where(probabilities < self.high_risk_threshold, "MEDIUM_RISK", "HIGH_RISK"))
        return probabilities, tiers.tolist()

    def evaluate(self, test_df):
        y = pd.to_numeric(test_df[CREDIT_TARGET], errors="raise").astype(int).to_numpy()
        probabilities = self.predict_proba(test_df)
        prediction = (probabilities >= self.review_threshold).astype(int)
        return {"ROC_AUC": round(float(roc_auc_score(y, probabilities)), 4), "PR_AUC": round(float(average_precision_score(y, probabilities)), 4), "Accuracy": round(float(accuracy_score(y, prediction)), 4), "F1_Score": round(float(f1_score(y, prediction, zero_division=0)), 4), "Precision": round(float(precision_score(y, prediction, zero_division=0)), 4), "Recall": round(float(recall_score(y, prediction, zero_division=0)), 4), "Confusion_Matrix": confusion_matrix(y, prediction).tolist(), "n_test": len(y)}

    def explain(self, df, top_k=5):
        data = self._engineer(df)
        probabilities, tiers = self.predict_risk(df)
        output = []
        for position, (_, row) in enumerate(data.iterrows()):
            indicators = []
            for feature in self.feature_names:
                value = float(row[feature]) if pd.notna(row[feature]) else 0.0
                median = float(self.reference_medians.get(feature, 0.0))
                indicators.append((abs(value - median), {"feature": feature, "feature_value": value, "relative_position": "Above training median" if value > median else "At or below training median"}))
            indicators.sort(key=lambda item: item[0], reverse=True)
            output.append({"client_id": str(df.iloc[position].get("client_id", position)), "risk_score": round(float(probabilities[position]), 4), "risk_tier": tiers[position], "unusual_indicators": [item[1] for item in indicators[:top_k]]})
        return output

    def explain_client_risk(self, client_df, top_k=5):
        return self.explain(client_df, top_k)
