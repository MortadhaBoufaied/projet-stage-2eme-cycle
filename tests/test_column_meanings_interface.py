import inspect

from src.services.modeling import train_credit, train_forecast


def test_training_functions_accept_column_meanings():
    credit_parameters = inspect.signature(train_credit).parameters
    forecast_parameters = inspect.signature(train_forecast).parameters
    assert "column_meanings" in credit_parameters
    assert "column_meanings" in forecast_parameters
