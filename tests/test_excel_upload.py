from pathlib import Path
from src.services.tabular_io import read_tabular_bytes


def test_generated_payment_workbook_is_accepted():
    path = Path(__file__).parents[1] / 'examples' / 'payments_risk_train.xlsx'
    df = read_tabular_bytes(path.read_bytes(), path.name)
    assert len(df) == 40000
    assert {'delay_days', 'is_late'}.issubset(df.columns)
    assert int(df['is_late'].sum()) == 16764
    assert int(df['delay_days'].max()) == 204
