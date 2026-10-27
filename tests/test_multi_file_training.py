import pandas as pd
import pytest
from src.services.multi_file_training import inspect_architecture,combine_compatible_files

def test_identical_architecture_combines_rows_and_tracks_source():
 a=pd.DataFrame({'date':['2024-01-01'],'units_sold':[1]});b=pd.DataFrame({'date':['2024-01-02'],'units_sold':[2]})
 ok,reports,_=inspect_architecture([('a.csv',a),('b.csv',b)])
 combined,_=combine_compatible_files([('a.csv',a),('b.csv',b)])
 assert ok and len(combined)==2 and set(combined._source_file)=={'a.csv','b.csv'}
def test_different_columns_are_rejected_before_combining():
 a=pd.DataFrame({'date':['2024-01-01'],'units_sold':[1]});b=pd.DataFrame({'date':['2024-01-02'],'revenue':[2]})
 ok,reports,_=inspect_architecture([('a.csv',a),('b.csv',b)])
 assert not ok and reports[1]['missing_columns']==['units_sold'] and reports[1]['extra_columns']==['revenue']
 with pytest.raises(ValueError):combine_compatible_files([('a.csv',a),('b.csv',b)])
def test_incompatible_types_are_rejected():
 a=pd.DataFrame({'units_sold':[1,2]});b=pd.DataFrame({'units_sold':['unknown','none']})
 ok,reports,_=inspect_architecture([('a.csv',a),('b.csv',b)])
 assert not ok and reports[1]['type_mismatches']
