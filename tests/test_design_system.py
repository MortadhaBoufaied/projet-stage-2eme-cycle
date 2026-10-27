from pathlib import Path
import ast

def source():return (Path(__file__).parents[1]/'src/ui/app.py').read_text(encoding='utf-8')

def test_ui_compiles_and_design_tokens_exist():
 s=source();ast.parse(s);assert '--blue:#0875b9' in s and '--yellow:#ffcd00' in s and 'app-brand' in s

def test_login_is_readable_and_clickable():
 s=source();assert 'pointer-events:auto!important' in s and "form_submit_button('Sign in',type='primary',use_container_width=True)" in s
 assert 'Clear decisions from complex financial data.' in s

def test_streamlit_white_top_decoration_removed():
 assert '[data-testid="stDecoration"]' in source()
