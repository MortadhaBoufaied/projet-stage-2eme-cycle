import pandas as pd
from src.services.lending_club import combine_training_files
from src.services.model_registry import ModelRegistry

def sample():
 return pd.DataFrame({'id':['a','b'],'annual_inc':[50000,60000],'loan_amnt':[10000,12000],'fico_range_low':[680,700],'fico_range_high':[684,704],'emp_length':['5 years','10+ years'],'total_acc':[8,10],'int_rate':['12%','9%'],'term':['36 months','60 months'],'dti':[15,20],'home_ownership':['RENT','MORTGAGE'],'purpose':['debt_consolidation','car'],'application_type':['Individual','Joint App'],'loan_status':['Fully Paid','Charged Off']})

def test_two_files_are_combined():
 df,notes=combine_training_files([('one.csv',sample()),('two.csv',sample().assign(id=['c','d']))])
 assert len(df)==4 and set(df.Default)=={0,1} and len(notes)==2

def test_registry_tasks_are_isolated(tmp_path):
 r=ModelRegistry(tmp_path)
 assert r._task_dir('c','forecast') != r._task_dir('c','lending_club_default')
