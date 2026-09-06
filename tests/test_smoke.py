from src.smoke_check import credit_data,forecast_data
from src.services.training import train_credit,train_forecast

def test_both_models_train():
    _,cm=train_credit(credit_data(160),'baseline')
    _,fm=train_forecast(forecast_data(),'baseline')
    assert cm['n_test']>0 and fm['n_test']>0
