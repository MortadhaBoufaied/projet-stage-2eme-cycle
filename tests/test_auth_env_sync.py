import tempfile
from pathlib import Path
import src.services.auth as auth

def test_env_admin_is_inserted_and_then_updated():
 with tempfile.TemporaryDirectory() as td:
  auth.DB_PATH=Path(td)/'platform.db';auth.ADMIN_USERNAME='first@example.com';auth.ADMIN_PASSWORD='FirstPass123';auth.initialize()
  with auth._connect() as con:r=con.execute("SELECT * FROM users WHERE role='admin'").fetchall()
  assert len(r)==1 and r[0]['email']=='first@example.com' and auth._verify('FirstPass123',r[0]['password_hash'])
  auth.ADMIN_USERNAME='new@example.com';auth.ADMIN_PASSWORD='NewPass456';auth.initialize()
  with auth._connect() as con:r=con.execute("SELECT * FROM users WHERE role='admin'").fetchall()
  assert len(r)==1 and r[0]['email']=='new@example.com' and auth._verify('NewPass456',r[0]['password_hash'])
