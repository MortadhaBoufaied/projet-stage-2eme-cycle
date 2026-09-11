from __future__ import annotations
from src.ui.pages import dashboard, credit, demand, training, policies, history, help, audit

PAGE_MAP = {
    "dashboard": dashboard,
    "credit": credit,
    "demand": demand,
    "training": training,
    "policies": policies,
    "history": history,
    "help": help,
    "audit": audit,
}

PAGE_TITLES = {
    "dashboard": "Dashboard",
    "credit": "Credit risk analysis",
    "demand": "Demand forecast",
    "training": "Training and model selection",
    "policies": "Company rules and policies",
    "history": "Model versions",
    "help": "Help and pipeline overview",
    "audit": "Audit log",
}
