from pathlib import Path
import ast

def test_current_admin_credentials_exists_before_signin():
 source=(Path(__file__).parents[1]/'src/services/auth.py').read_text(encoding='utf-8')
 ast.parse(source)
 assert 'def _current_admin_credentials():' in source
 assert source.index('def _current_admin_credentials():') < source.index('def sign_in(username,password):')

def test_helper_is_self_contained():
 source=(Path(__file__).parents[1]/'src/services/auth.py').read_text(encoding='utf-8')
 assert "env_path=PROJECT_ROOT/'.env'" in source
 assert "encoding='utf-8-sig'" in source
