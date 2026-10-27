import src.services.browser_storage as storage


def test_browser_token_reader_is_invoked_only_once(monkeypatch):
    state = {}
    calls = []
    monkeypatch.setattr(storage.st, "session_state", state)
    monkeypatch.setattr(storage, "streamlit_js_eval", lambda **kwargs: calls.append(kwargs) or None)
    assert storage.get_token() is None
    assert storage.get_token() is None
    assert len(calls) == 1
    assert calls[0]["key"] == "read_remember_token"


def test_sign_out_does_not_call_browser_reader(monkeypatch):
    import src.services.auth as auth
    monkeypatch.setattr(auth.st, "session_state", {})
    monkeypatch.setattr(auth, "get_token", lambda: (_ for _ in ()).throw(AssertionError("must not read")))
    monkeypatch.setattr(auth, "clear_token", lambda: None)
    auth.sign_out()
