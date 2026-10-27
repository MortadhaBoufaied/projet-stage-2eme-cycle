from __future__ import annotations
import hashlib,hmac,json,secrets
from dataclasses import asdict,dataclass
from datetime import datetime,timezone
from pathlib import Path
from src.config import ARTIFACTS_DIR

@dataclass
class Account:
    user_id:str; email:str; display_name:str; role:str; tenant_id:str; active:bool=True; created_at:str=""
class AccountStore:
    def __init__(self,root:Path=ARTIFACTS_DIR):
        self.path=Path(root)/"platform_accounts.json";self.path.parent.mkdir(parents=True,exist_ok=True)
    def _load(self):
        if not self.path.exists():return {"users":{},"tenants":{}}
        try:return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:return {"users":{},"tenants":{}}
    def _save(self,data):
        tmp=self.path.with_suffix(".tmp");tmp.write_text(json.dumps(data,indent=2),encoding="utf-8");tmp.replace(self.path)
    @staticmethod
    def _hash(password,salt=None):
        salt=salt or secrets.token_hex(16);digest=hashlib.pbkdf2_hmac("sha256",password.encode(),bytes.fromhex(salt),210000);return salt,digest.hex()
    @staticmethod
    def _tenant(name):return "soc_"+hashlib.sha256((name+secrets.token_hex(8)).encode()).hexdigest()[:12]
    def signup(self,email,password,company_name,display_name):
        email=email.strip().lower();company_name=company_name.strip();display_name=display_name.strip()
        if "@" not in email or "." not in email.split("@")[-1]:raise ValueError("Enter a valid work email.")
        if len(password)<10 or not any(c.isdigit() for c in password) or not any(c.isalpha() for c in password):raise ValueError("Password needs at least 10 characters, including letters and a number.")
        if len(company_name)<2:raise ValueError("Enter the company name.")
        data=self._load()
        if email in data["users"]:raise ValueError("An account already exists for this email.")
        tenant=self._tenant(company_name);salt,digest=self._hash(password);uid="usr_"+secrets.token_hex(8);now=datetime.now(timezone.utc).isoformat()
        data["tenants"][tenant]={"tenant_id":tenant,"name":company_name,"status":"PENDING","created_at":now}
        data["users"][email]={"user_id":uid,"email":email,"display_name":display_name or email.split("@")[0],"role":"SOCIETY_OWNER","tenant_id":tenant,"active":True,"created_at":now,"salt":salt,"password_hash":digest}
        self._save(data);return tenant
    def authenticate(self,email,password):
        row=self._load()["users"].get(email.strip().lower())
        if not row or not row.get("active"):return None
        _,digest=self._hash(password,row["salt"])
        if not hmac.compare_digest(digest,row["password_hash"]):return None
        safe={k:v for k,v in row.items() if k not in {"salt","password_hash"}};return Account(**safe)
    def tenants(self):return list(self._load()["tenants"].values())
    def tenant(self,tenant_id):return self._load()["tenants"].get(tenant_id)
    def set_tenant_status(self,tenant_id,status):
        if status not in {"PENDING","ACTIVE","SUSPENDED"}:raise ValueError("Invalid tenant status")
        data=self._load();data["tenants"][tenant_id]["status"]=status;self._save(data)
    def users(self):
        return [{k:v for k,v in row.items() if k not in {"salt","password_hash"}} for row in self._load()["users"].values()]
