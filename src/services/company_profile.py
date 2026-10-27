from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from src.config import ARTIFACTS_DIR
from src.services.model_registry import safe_company_id


@dataclass
class CompanyProfile:
    company_id: str
    display_name: str = ""
    currency: str = "TND"
    language: str = "English"
    review_threshold: float = 0.50
    high_risk_threshold: float = 0.60
    require_human_approval: bool = True
    recommendation_rules: list[str] = field(default_factory=list)
    forbidden_actions: list[str] = field(default_factory=list)

    def validate(self):
        if not 0 < self.review_threshold <= self.high_risk_threshold < 1:
            raise ValueError("Thresholds must satisfy 0 < review <= high < 1")
        self.company_id = safe_company_id(self.company_id)
        return self


class CompanyProfileStore:
    def __init__(self, root: Path = ARTIFACTS_DIR):
        self.root = Path(root)

    def _path(self, company_id: str) -> Path:
        return self.root / safe_company_id(company_id) / "company_profile.json"

    def save(self, profile: CompanyProfile) -> Path:
        profile.validate()
        path = self._path(profile.company_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(profile), indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def load(self, company_id: str) -> CompanyProfile:
        path = self._path(company_id)
        if not path.exists():
            return CompanyProfile(company_id=safe_company_id(company_id))
        return CompanyProfile(**json.loads(path.read_text(encoding="utf-8"))).validate()
