from __future__ import annotations
import hmac
from datetime import datetime,timedelta,timezone
import streamlit as st
from src.config import ADMIN_PASSWORD,ADMIN_USERNAME,SESSION_MINUTES
A="finance_authenticated";U="finance_user";E="finance_session_expiry"
def credentials_configured():return bool(ADMIN_USERNAME and ADMIN_PASSWORD)
def sign_in(username,password):
 valid=credentials_configured() and hmac.compare_digest(username.strip(),ADMIN_USERNAME) and hmac.compare_digest(password,ADMIN_PASSWORD)
 if valid:st.session_state[A]=True;st.session_state[U]=ADMIN_USERNAME;st.session_state[E]=datetime.now(timezone.utc)+timedelta(minutes=SESSION_MINUTES)
 return valid
def is_authenticated():
 expiry=st.session_state.get(E)
 if not st.session_state.get(A) or not expiry or datetime.now(timezone.utc)>=expiry:sign_out();return False
 return True
def current_user():return str(st.session_state.get(U,""))
def sign_out():
 for key in (A,U,E):st.session_state.pop(key,None)
