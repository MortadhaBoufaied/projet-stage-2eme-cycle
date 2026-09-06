from pathlib import Path

def test_login_and_signup_accept_boolean_auth_results():
 source=(Path(__file__).parents[1]/'src/ui/app.py').read_text(encoding='utf-8')
 assert 'def _auth_result' in source
 assert '_auth_result(sign_in(email,password)' in source
 assert '_auth_result(value' in source
 assert 'ok,msg=sign_in' not in source

def test_auth_design_and_navigation_links_are_present():
 source=(Path(__file__).parents[1]/'src/ui/app.py').read_text(encoding='utf-8')
 for text in ['Welcome back','Secure access','Create a company account','Back to sign in','For your security, the session expires automatically after inactivity.']:
  assert text in source
