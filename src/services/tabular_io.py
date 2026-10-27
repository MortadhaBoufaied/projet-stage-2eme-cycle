from io import BytesIO
from pathlib import Path
import re
import pandas as pd

SUPPORTED_TABULAR_EXTENSIONS = ('csv', 'xls', 'xlsx')


def _date_series(series):
    """Parse Excel dates, ISO dates, or compact YYYYMMDD values."""
    raw = series.copy()
    numeric = pd.to_numeric(raw, errors='coerce')
    compact = numeric.round().astype('Int64').astype('string')
    parsed_compact = pd.to_datetime(compact, format='%Y%m%d', errors='coerce')
    parsed_general = pd.to_datetime(raw, errors='coerce')
    # Excel serial dates may appear as numbers smaller than YYYYMMDD.
    serial_mask = numeric.between(1, 80000, inclusive='both')
    parsed_serial = pd.to_datetime(numeric, unit='D', origin='1899-12-30', errors='coerce')
    result = parsed_general.where(~serial_mask, parsed_serial)
    return result.fillna(parsed_compact)


def derive_payment_targets(df):
    """Fill delay_days/is_late from settlement and due dates when possible.

    This is preparation logic only. clear_date, delay_days, and is_late must
    still be excluded from the model feature matrix to prevent leakage.
    """
    out = df.copy()
    normalized = {re.sub(r'[^a-z0-9]+', '', str(c).lower()): c for c in out.columns}
    clear_col = normalized.get('cleardate')
    due_col = normalized.get('dueindate') or normalized.get('duedate')
    if not clear_col or not due_col:
        return out
    clear = _date_series(out[clear_col])
    due = _date_series(out[due_col])
    known = clear.notna() & due.notna()
    calculated_delay = (clear - due).dt.days.clip(lower=0)
    if 'delaydays' in normalized:
        delay_col = normalized['delaydays']
        existing = pd.to_numeric(out[delay_col], errors='coerce')
        out[delay_col] = existing.where(existing.notna(), calculated_delay)
    else:
        delay_col = 'delay_days'
        out[delay_col] = calculated_delay.where(known)
    delay = pd.to_numeric(out[delay_col], errors='coerce')
    calculated_late = (delay > 0).astype('Int64').where(known)
    if 'islate' in normalized:
        late_col = normalized['islate']
        existing_late = pd.to_numeric(out[late_col], errors='coerce')
        out[late_col] = existing_late.where(existing_late.notna(), calculated_late)
    else:
        out['is_late'] = calculated_late
    return out


def read_tabular_bytes(data, filename):
    ext = Path(filename).suffix.lower()
    bio = BytesIO(data)
    if ext == '.csv':
        try:
            df = pd.read_csv(bio, sep=None, engine='python')
        except UnicodeDecodeError:
            bio.seek(0)
            df = pd.read_csv(bio, encoding='latin-1')
    elif ext in {'.xls', '.xlsx'}:
        engine = 'xlrd' if ext == '.xls' else 'openpyxl'
        df = pd.read_excel(bio, engine=engine)
        norm = [re.sub(r'[^A-Za-z0-9]', '', str(c)).upper() for c in df.columns]
        if sum(bool(re.fullmatch(r'X(?:[1-9]|1[0-9]|2[0-3])', c)) for c in norm) >= 3 and 'Y' in norm:
            bio.seek(0)
            df = pd.read_excel(bio, engine=engine, header=1)
    else:
        raise ValueError('Unsupported file type. Upload CSV, XLS, or XLSX.')
    df.columns = [str(c).strip() for c in df.columns]
    df = df.drop(columns=[c for c in df if c.lower().startswith('unnamed:')], errors='ignore')
    if df.empty:
        raise ValueError('The uploaded table has no data rows.')
    return derive_payment_targets(df)


def read_uploaded_table(file):
    data = file.getvalue() if hasattr(file, 'getvalue') else file.read()
    return read_tabular_bytes(data, file.name)
