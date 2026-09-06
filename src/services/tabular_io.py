from io import BytesIO
from pathlib import Path
import re,pandas as pd
SUPPORTED_TABULAR_EXTENSIONS=('csv','xls','xlsx')
def read_tabular_bytes(data,filename):
 ext=Path(filename).suffix.lower();bio=BytesIO(data)
 if ext=='.csv':
  df=pd.read_csv(bio)
 elif ext in {'.xls','.xlsx'}:
  engine='xlrd' if ext=='.xls' else 'openpyxl';df=pd.read_excel(bio,engine=engine)
  norm=[re.sub(r'[^A-Za-z0-9]','',str(c)).upper() for c in df.columns]
  if sum(bool(re.fullmatch(r'X(?:[1-9]|1[0-9]|2[0-3])',c)) for c in norm)>=3 and 'Y' in norm:
   bio.seek(0);df=pd.read_excel(bio,engine=engine,header=1)
 else:raise ValueError('Unsupported file type. Upload CSV, XLS, or XLSX.')
 df.columns=[str(c).strip() for c in df.columns];df=df.drop(columns=[c for c in df if c.lower().startswith('unnamed:')],errors='ignore')
 if df.empty:raise ValueError('The uploaded table has no data rows.')
 return df
def read_uploaded_table(file):return read_tabular_bytes(file.getvalue() if hasattr(file,'getvalue') else file.read(),file.name)
