import pandas as pd
import pytest
from src.services.dataset_catalog import adapt, assert_compatible, dataframe_fingerprint, overlap_report


def test_uci_adapter_maps_target_and_identifier():
    frame = adapt(pd.DataFrame({'ID':[1], 'default.payment.next.month':[0]}), 'uci_credit_card')
    assert {'client_id','default_next_month','dataset_source'} <= set(frame.columns)


def test_incompatible_schema_families_are_rejected():
    with pytest.raises(ValueError, match='incompatible schema families'):
        assert_compatible(['uci_credit_card','german_credit'])


def test_fingerprint_is_order_independent():
    first = pd.DataFrame({'client_id':['A','B'], 'x':[1,2]})
    second = first.iloc[::-1].reset_index(drop=True)
    assert dataframe_fingerprint(first) == dataframe_fingerprint(second)


def test_overlap_blocks_duplicate_rows():
    first = pd.DataFrame({'client_id':['A','B'], 'x':[1,2]})
    second = pd.DataFrame({'client_id':['B','C'], 'x':[9,3]})
    report = overlap_report([first,second], ['client_id'])
    assert report['overlapping_rows'] == 1 and not report['safe_to_merge']
