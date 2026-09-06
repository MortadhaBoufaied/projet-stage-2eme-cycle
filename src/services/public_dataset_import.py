"""Optional controlled downloader for cataloged, directly downloadable CSV files."""
from __future__ import annotations
import io
import urllib.request
import pandas as pd
from .dataset_catalog import adapt, source

MAX_PUBLIC_DOWNLOAD_BYTES = 100 * 1024 * 1024


def download_catalog_csv(key: str, timeout: int = 45) -> pd.DataFrame:
    item = source(key)
    if not item.direct_download:
        raise ValueError("This catalog entry requires selecting a file on its documented source page.")
    request = urllib.request.Request(item.direct_download, headers={"User-Agent": "ML-Intelligence-Center/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        length = int(response.headers.get("Content-Length", "0") or 0)
        if length > MAX_PUBLIC_DOWNLOAD_BYTES:
            raise ValueError("Public dataset is larger than the controlled download limit.")
        payload = response.read(MAX_PUBLIC_DOWNLOAD_BYTES + 1)
    if len(payload) > MAX_PUBLIC_DOWNLOAD_BYTES:
        raise ValueError("Public dataset exceeded the controlled download limit.")
    try:
        frame = pd.read_csv(io.BytesIO(payload))
    except Exception as exc:
        raise ValueError(f"Downloaded content is not a readable CSV: {exc}") from exc
    if frame.empty:
        raise ValueError("Downloaded dataset is empty.")
    return adapt(frame, key)
