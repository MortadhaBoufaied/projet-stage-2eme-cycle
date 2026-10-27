import pandas as pd
from src.services.financial_features import add_revenue_cashflow_fields, add_customer_history
from src.agents.financial_forecast_agent import FinancialForecastAgent


def test_revenue_and_cashflow_targets():
    d=pd.DataFrame({'units_sold':[2,3],'price':[10,20],'cash_inflow':[30,50],'cash_outflow':[5,10]})
    out=add_revenue_cashflow_fields(d)
    assert out.revenue.tolist()==[20,60]
    assert out.net_cashflow.tolist()==[25,40]


def test_customer_history_is_past_only():
    d=pd.DataFrame({'cust_number':['A','A','A'],'posting_date':['2026-01-01','2026-02-01','2026-03-01'],'is_late':[1,0,1],'total_open_amount':[100,200,300]})
    out=add_customer_history(d)
    assert out.previous_invoice_count.tolist()==[0,1,2]
    assert out.previous_late_invoice_count.tolist()==[0,1,1]


def test_financial_summary():
    agent=FinancialForecastAgent();result=agent.assess([10,12],[9,11],opening_cash=100,minimum_cash=20)
    summary=agent.summary(result,'net_cashflow')
    assert summary['forecast_total']==20
    assert 'managerial_summary' in summary
