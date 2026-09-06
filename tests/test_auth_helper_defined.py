from pathlib import Path
import ast

def test_auth_helper_defined_before_signin():
 p=Path(__file__).parents[1]/'src/services/auth.py';s=p.read_text();ast.parse(s)
 assert s.index('def _current_admin_credentials') < s.index('def sign_in')

def test_login_button_clickable():
 s=(Path(__file__).parents[1]/'src/ui/app.py').read_text()
 assert "form_submit_button('Sign in',type='primary',use_container_width=True)" in s
 assert 'pointer-events:auto!important' in s
