from pathlib import Path
import pandas as pd
from src.services.hybrid_mapping import hybrid_suggest_mapping
def test_hybrid_mapper_masks_and_rejects_invention():
 df=pd.DataFrame({"sale_day":[1]*7,"email":["x@y.com"]*7})
 seen={}
 def slm(req,cols,sample):seen["sample"]=sample;return {"date":"sale_day","units_sold":"fake"}
 m,r=hybrid_suggest_mapping(df,["date","units_sold"],slm)
 assert m["date"]=="sale_day" and m["units_sold"]==""
 assert seen["sample"][0]["email"]=="[MASKED]" and len(seen["sample"])==5
def test_prompts_are_constrained_and_ui_integrated():
 a=Path("src/services/slm_assistant.py").read_text();u=Path("src/ui/app.py").read_text()
 assert "Never invent" in a and "human approval" in a and "map_unresolved_columns" in a
 assert "hybrid_suggest_mapping" in u and "accept_multiple_files=True" in u and "500 MB" in u
