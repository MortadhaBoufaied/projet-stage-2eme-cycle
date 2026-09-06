import importlib
import sqlite3


def test_legacy_eight_column_user_table_migrates(tmp_path, monkeypatch):
    db = tmp_path / 'legacy.db'
    connection = sqlite3.connect(db)
    connection.execute('''CREATE TABLE users(
        user_id TEXT, email TEXT, password_hash TEXT, role TEXT,
        tenant_id TEXT, full_name TEXT, is_active INTEGER, created TEXT)''')
    connection.execute("INSERT INTO users VALUES(?,?,?,?,?,?,?,?)", (
        'old-1','old@example.com','bad-format','admin',None,'Old Admin',1,'2025-01-01'))
    connection.commit(); connection.close()
    import src.services.auth as auth
    monkeypatch.setattr(auth, 'DB', db)
    auth.init()
    connection = sqlite3.connect(db)
    columns = [x[1] for x in connection.execute('PRAGMA table_info(users)')]
    count = connection.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    backups = connection.execute("SELECT count(*) FROM sqlite_master WHERE name LIKE 'users_legacy_%'").fetchone()[0]
    assert columns == list(auth.USER_COLUMNS)
    assert count == 1
    assert backups == 1


def test_canonical_insert_uses_named_columns(tmp_path, monkeypatch):
    import src.services.auth as auth
    monkeypatch.setattr(auth, 'DB', tmp_path / 'new.db')
    monkeypatch.setenv('ADMIN_EMAIL','admin@example.com')
    monkeypatch.setenv('ADMIN_PASSWORD','ChangeMe123!')
    auth.init()
    user = auth.verify('admin@example.com','ChangeMe123!')
    assert user and user['role'] == 'admin' and user['active'] == 1
