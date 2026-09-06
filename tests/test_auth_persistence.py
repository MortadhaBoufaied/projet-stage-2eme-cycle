from pathlib import Path
from types import SimpleNamespace

import src.services.auth as auth


def test_login_token_restores_session_and_logout_revokes_it(tmp_path, monkeypatch):
    auth.DB_PATH=Path(tmp_path)/'platform.db'
    auth.ADMIN_USERNAME='';auth.ADMIN_PASSWORD=''
    monkeypatch.setattr(auth.st,'session_state',{})
    auth.initialize()
    browser={'token':None}
    monkeypatch.setattr(auth,'set_token',lambda token:browser.update(token=token))
    monkeypatch.setattr(auth,'get_token',lambda:browser['token'])
    monkeypatch.setattr(auth,'clear_token',lambda:browser.update(token=None))

    assert auth.sign_up('Acme Finance','Analyst','analyst@acme.test','StrongPass123')
    assert auth.sign_in('analyst@acme.test','StrongPass123')
    assert browser['token'] and len(browser['token']) > 20
    token=browser['token']

    auth.st.session_state.clear()
    assert auth.restore_session()
    assert auth.current_user()=='analyst@acme.test'
    assert auth.is_authenticated()

    auth.sign_out()
    assert browser['token'] is None
    auth.st.session_state.clear()
    monkeypatch.setattr(auth,'get_token',lambda:token)
    assert not auth.restore_session()
