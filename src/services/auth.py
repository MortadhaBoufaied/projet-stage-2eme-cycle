import sqlite3,hashlib,hmac,secrets,os,re
from datetime import datetime,timezone,timedelta
from src.config import DB

SESSION_HOURS=24

def con(): c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;return c
def h(p,s=None): s=s or secrets.token_hex(16);return s+':'+hashlib.pbkdf2_hmac('sha256',p.encode(),bytes.fromhex(s),250000).hex()

def _columns(cursor,table):
    return [row[1] for row in cursor.execute(f"PRAGMA table_info({table})").fetchall()]

def init():
    DB.parent.mkdir(exist_ok=True)
    with con() as c:
        c.executescript(
            "CREATE TABLE IF NOT EXISTS companies(id TEXT PRIMARY KEY,name TEXT,status TEXT,created_at TEXT);"
            "CREATE TABLE IF NOT EXISTS users(email TEXT PRIMARY KEY,password_hash TEXT,role TEXT,company_id TEXT,display_name TEXT,status TEXT DEFAULT 'active',created_at TEXT,last_login_at TEXT);"
            "CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,email TEXT NOT NULL,expires_at TEXT NOT NULL);"
        )
        ae=os.getenv('ADMIN_EMAIL');ap=os.getenv('ADMIN_PASSWORD')
        if ae and ap:
            now=datetime.now(timezone.utc).isoformat()
            cols=_columns(c,'users')
            pwd_col='password_hash' if 'password_hash' in cols else 'password'
            name_col='display_name' if 'display_name' in cols else 'name'
            if 'status' in cols and 'created_at' in cols:
                c.execute(f"INSERT OR IGNORE INTO users(email,{pwd_col},role,company_id,{name_col},status,created_at) VALUES(?,?,?,?,?,'active',?)",(ae.lower(),h(ap),'admin','','Platform administrator',now))
            else:
                c.execute(f"INSERT OR IGNORE INTO users(email,{pwd_col},role,company_id,{name_col}) VALUES(?,?,?,?,?)",(ae.lower(),h(ap),'admin','','Platform administrator'))

def _get_user(email):
    """Look up a user by email and return a dict, or None."""
    r=con().execute('SELECT * FROM users WHERE email=?',(email.lower(),)).fetchone()
    if not r: return None
    cols=r.keys()
    name_col='display_name' if 'display_name' in cols else 'name'
    return {'email':r['email'],'role':r['role'],'company_id':r['company_id'],'name':r[name_col]}

def verify(email,password):
    init()
    r=con().execute('SELECT * FROM users WHERE email=?',(email.lower(),)).fetchone()
    if not r:return None
    cols=r.keys()
    pwd_col='password_hash' if 'password_hash' in cols else 'password'
    name_col='display_name' if 'display_name' in cols else 'name'
    s,x=r[pwd_col].split(':');y=h(password,s).split(':')[1]
    if hmac.compare_digest(x,y):
        return {'email':r['email'],'role':r['role'],'company_id':r['company_id'],'name':r[name_col]}
    return None

def create_session(email):
    """Create a session token for the given email, return the token string."""
    token=secrets.token_urlsafe(48)
    expires=(datetime.now(timezone.utc)+timedelta(hours=SESSION_HOURS)).isoformat()
    with con() as c:
        c.execute("INSERT INTO sessions(token,email,expires_at) VALUES(?,?,?)",(token,email.lower(),expires))
    return token

def validate_session(token):
    """Validate a session token. Returns the user dict or None."""
    if not token: return None
    with con() as c:
        r=c.execute("SELECT * FROM sessions WHERE token=?",(token,)).fetchone()
        if not r: return None
        if datetime.fromisoformat(r['expires_at'])<datetime.now(timezone.utc):
            c.execute("DELETE FROM sessions WHERE token=?",(token,))
            return None
    return _get_user(r['email'])

def destroy_session(token):
    """Delete a session token."""
    if not token: return
    with con() as c:
        c.execute("DELETE FROM sessions WHERE token=?",(token,))

def signup(company,name,email,password):
    if not re.fullmatch(r'[^@ ]+@[^@ ]+\.[^@ ]+',email):return False,'Enter a valid email.'
    if len(password)<10:return False,'Password must contain at least 10 characters.'
    cid='co_'+secrets.token_hex(6);now=datetime.now(timezone.utc).isoformat()
    try:
        with con() as c:
            cols=_columns(c,'users')
            pwd_col='password_hash' if 'password_hash' in cols else 'password'
            name_col='display_name' if 'display_name' in cols else 'name'
            comp_cols=_columns(c,'companies')
            if 'created_at' in comp_cols:
                c.execute("INSERT INTO companies(id,name,status,created_at) VALUES(?,?,?,?)",(cid,company,'active',now))
            else:
                c.execute("INSERT INTO companies(id,name,status) VALUES(?,?,?)",(cid,company,'active'))
            if 'status' in cols and 'created_at' in cols:
                c.execute(f"INSERT INTO users(email,{pwd_col},role,company_id,{name_col},status,created_at) VALUES(?,?,?,?,?,'active',?)",(email.lower(),h(password),'company',cid,name,now))
            else:
                c.execute(f"INSERT INTO users(email,{pwd_col},role,company_id,{name_col}) VALUES(?,?,?,?,?)",(email.lower(),h(password),'company',cid,name))
        return True,'Workspace created.'
    except sqlite3.IntegrityError:return False,'An account already exists.'
init()
