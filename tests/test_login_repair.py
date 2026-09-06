from pathlib import Path
import os
from src.config import _load_env

def test_env_loader_bom_quotes_override(tmp_path):
 p=tmp_path/'.env';p.write_text('\ufeffADMIN_EMAIL = "Admin@Test.com"\nADMIN_PASSWORD = \'Secret123\'\n',encoding='utf-8')
 os.environ['ADMIN_EMAIL']='stale@test.com';v=_load_env(p,True)
 assert v['ADMIN_EMAIL']=='Admin@Test.com' and os.environ['ADMIN_EMAIL']=='Admin@Test.com'

def test_signin_button_not_disabled_by_widget_state():
 s=(Path(__file__).parents[1]/'src/ui/app.py').read_text()
 assert "form_submit_button('Sign in',type='primary',use_container_width=True)" in s
 assert 'pointer-events:auto!important' in s
 assert '[data-testid="stDecoration"]' in s
