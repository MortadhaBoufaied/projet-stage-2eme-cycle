import pandas as pd

from src.services.client_history_input import editor_columns, empty_editor_frame


def test_editor_uses_contract_customer_identifier_and_all_fields():
    raw = ["business_code", "cust_number", "buisness_year", "posting_date", "total_open_amount"]
    columns = editor_columns(raw)
    assert columns[0] == "record_type"
    assert "cust_number" in columns
    assert "client_id" not in columns
    assert set(raw).issubset(columns)
    assert {"clear_date", "delay_days", "is_late"}.issubset(columns)


def test_empty_editor_populates_real_customer_column():
    frame = empty_editor_frame(["cust_number", "posting_date"], 3)
    assert frame["cust_number"].tolist() == ["customer_1"] * 3
    assert frame["record_type"].tolist() == ["History", "History", "Current"]
