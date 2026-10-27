import numpy as np
import pandas as pd
from src.ui.app import _readable_factor_name, _display_factor_value


def test_readable_factor_labels():
    assert _readable_factor_name('total_open_amount') == 'Invoice amount'
    assert _readable_factor_name('business_code') == 'Business unit'
    assert _readable_factor_name('custom_field') == 'Custom Field'


def test_display_factor_values():
    assert _display_factor_value(7679.01) == '7,679.01'
    assert _display_factor_value(np.nan) == 'Not available'
