from pathlib import Path
import os
ROOT=Path(__file__).resolve().parents[1]
for line in (ROOT/'.env').read_text(encoding='utf-8').splitlines() if (ROOT/'.env').exists() else []:
    if line.strip() and not line.lstrip().startswith('#') and '=' in line:
        k,v=line.split('=',1); os.environ.setdefault(k.strip(),v.strip().strip('"').strip("'"))
ARTIFACTS=ROOT/'artifacts'; ARTIFACTS.mkdir(exist_ok=True)
DB=ROOT/'data'/'platform.db'
RANDOM_STATE=42
MAX_UPLOAD_MB=int(os.getenv('MAX_UPLOAD_MB','500'))
