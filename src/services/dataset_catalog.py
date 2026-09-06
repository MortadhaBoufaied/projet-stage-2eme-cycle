"""Governed catalog and schema adapters for supported public datasets.

The application never silently combines datasets. Each source declares a schema family,
training task, target, license/source page, and deterministic column mapping.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Iterable
import json
import pandas as pd


@dataclass(frozen=True)
class DatasetSource:
    key: str
    name: str
    task: str
    schema_family: str
    target: str
    source_page: str
    direct_download: str
    notes: str
    column_mapping: dict[str, str]


CATALOG = {
    "uci_credit_card": DatasetSource(
        key="uci_credit_card",
        name="UCI Default of Credit Card Clients",
        task="credit",
        schema_family="uci_credit_v1",
        target="default_next_month",
        source_page="https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients",
        direct_download="https://huggingface.co/datasets/scikit-learn/credit-card-clients/resolve/main/UCI_Credit_Card.csv?download=true",
        notes="Direct CSV mirror. Normalize the ID and target names. Do not append if the same UCI rows already exist in another file.",
        column_mapping={"ID": "client_id", "default.payment.next.month": "default_next_month"},
    ),
    "german_credit": DatasetSource(
        key="german_credit",
        name="German Credit Data",
        task="credit",
        schema_family="german_credit_v1",
        target="default",
        source_page="https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data",
        direct_download="https://raw.githubusercontent.com/tkseneee/Dataset/master/credit-default.csv",
        notes="Different feature architecture. Train a separate model and never concatenate with UCI credit rows.",
        column_mapping={},
    ),
    "retail_sku_weekly": DatasetSource(
        key="retail_sku_weekly",
        name="Retail SKU Weekly Demand",
        task="forecast",
        schema_family="retail_sku_weekly_v1",
        target="units_sold",
        source_page="https://demandprediction.github.io/dataset.html",
        direct_download="",
        notes="Weekly SKU demand. Select the downloadable raw file on the source page; inventory fields are not fabricated.",
        column_mapping={"week": "date", "SKU": "product_id", "weekly sales": "units_sold", "vendor": "store_id"},
    ),
    "retail_transactions": DatasetSource(
        key="retail_transactions",
        name="Retail Sales Transactions",
        task="forecast",
        schema_family="retail_transactions_v1",
        target="revenue",
        source_page="https://github.com/Seunfunmee/Retail-Sales-Data-Set",
        direct_download="https://raw.githubusercontent.com/Seunfunmee/Retail-Sales-Data-Set/main/Retail%20Sales%20Data%20Set.csv",
        notes="Aggregate transactions by date and category before revenue or unit forecasting.",
        column_mapping={"Transaction ID": "transaction_id", "Date": "date", "Product Category": "category", "Quantity": "units_sold", "Price per Unit": "price", "Total Amount": "revenue"},
    ),
}


def source(key: str) -> DatasetSource:
    if key not in CATALOG:
        raise KeyError(f"Unknown dataset source: {key}")
    return CATALOG[key]


def catalog_frame() -> pd.DataFrame:
    return pd.DataFrame([asdict(item) for item in CATALOG.values()])


def adapt(df: pd.DataFrame, key: str) -> pd.DataFrame:
    item = source(key)
    mapped = df.rename(columns=item.column_mapping).copy()
    mapped.columns = [str(column).strip() for column in mapped.columns]
    mapped["dataset_source"] = key
    return mapped


def schema_family(key: str) -> str:
    return source(key).schema_family


def assert_compatible(keys: Iterable[str]) -> str:
    keys = list(keys)
    if not keys:
        raise ValueError("Select at least one dataset source.")
    families = {schema_family(key) for key in keys}
    if len(families) != 1:
        names = ", ".join(sorted(families))
        raise ValueError(f"Datasets use incompatible schema families ({names}) and must train separate specialized models.")
    return next(iter(families))


def dataframe_fingerprint(df: pd.DataFrame, identity_columns: Iterable[str] | None = None) -> str:
    """Order-independent fingerprint used to detect repeated datasets or overlapping rows."""
    work = df.copy()
    if identity_columns:
        columns = [column for column in identity_columns if column in work.columns]
        if columns:
            work = work[columns]
    work = work.fillna("<NA>").astype(str)
    row_hashes = pd.util.hash_pandas_object(work, index=False).sort_values().astype(str)
    return sha256("\n".join(row_hashes).encode("utf-8")).hexdigest()


def overlap_report(frames: list[pd.DataFrame], identity_columns: Iterable[str] | None = None) -> dict:
    fingerprints = [dataframe_fingerprint(frame, identity_columns) for frame in frames]
    duplicate_files = len(fingerprints) - len(set(fingerprints))
    seen: set[int] = set()
    overlaps = 0
    for frame in frames:
        work = frame[list(identity_columns)] if identity_columns and all(c in frame for c in identity_columns) else frame
        hashes = set(pd.util.hash_pandas_object(work.fillna("<NA>").astype(str), index=False).tolist())
        overlaps += len(seen.intersection(hashes))
        seen.update(hashes)
    return {"files": len(frames), "duplicate_files": duplicate_files, "overlapping_rows": overlaps, "safe_to_merge": duplicate_files == 0 and overlaps == 0}


def write_catalog(path: str | Path) -> None:
    Path(path).write_text(json.dumps({k: asdict(v) for k, v in CATALOG.items()}, indent=2), encoding="utf-8")
