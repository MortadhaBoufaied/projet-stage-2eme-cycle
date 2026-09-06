from __future__ import annotations
import json, os, threading
from pathlib import Path
from typing import Any
from src.config import PROJECT_ROOT

MODEL_DIR=PROJECT_ROOT/'models'/'slm'
MODEL_PATH=MODEL_DIR/'qwen2.5-1.5b-instruct-q4_k_m.gguf'
MAX_MODEL_BYTES=2_000_000_000
_lock=threading.Lock();_model=None

SYSTEM_PROMPTS={
'payment':'''You are the Payment Risk Decision Support Assistant. Convert verified model outputs into concise operational guidance. Never invent facts, modify probabilities, approve or reject credit, or make a legally consequential decision. Use only supplied aggregates. Return JSON only with keys headline, description, decision_status, priority_actions, evidence, limitations. decision_status must be STANDARD_PROCESS, REVIEW_RECOMMENDED, or MANUAL_REVIEW. Require a responsible employee to confirm every consequential action.''',
'forecast':'''You are the Cashflow and Revenue Decision Support Assistant. Explain forecast metrics, anomalies and stock exposure using only supplied facts. Do not invent future values or initiate purchases. Return JSON only with keys headline, description, decision_status, priority_actions, evidence, limitations. decision_status must be NORMAL_MONITORING, INVESTIGATE_VARIANCE, or OPERATIONAL_REVIEW. Human approval is mandatory for operational actions.'''
}
ALLOWED={
'payment':{'STANDARD_PROCESS','REVIEW_RECOMMENDED','MANUAL_REVIEW'},
'forecast':{'NORMAL_MONITORING','INVESTIGATE_VARIANCE','OPERATIONAL_REVIEW'}
}

def model_status():
 return {'installed':MODEL_PATH.exists(),'path':str(MODEL_PATH),'size_mb':round(MODEL_PATH.stat().st_size/1024/1024,1) if MODEL_PATH.exists() else 0,'model':'Qwen2.5-1.5B-Instruct Q4_K_M'}

def _load():
 global _model
 if _model is not None:return _model
 if not MODEL_PATH.exists():raise FileNotFoundError('Local SLM is not installed. Run install_slm.py or restart through the project launcher.')
 if MODEL_PATH.stat().st_size>MAX_MODEL_BYTES:raise RuntimeError('SLM exceeds the configured 2 GB limit.')
 with _lock:
  if _model is None:
   from llama_cpp import Llama
   _model=Llama(model_path=str(MODEL_PATH),n_ctx=4096,n_threads=max(1,(os.cpu_count() or 2)-1),n_gpu_layers=int(os.getenv('SLM_GPU_LAYERS','0')),verbose=False)
 return _model

def _fallback(service,data,reason='Local SLM unavailable'):
 if service=='forecast':
  anomalies=int(data.get('anomalies',0));stock=int(data.get('stockout_risks',0));status='OPERATIONAL_REVIEW' if stock else 'INVESTIGATE_VARIANCE' if anomalies else 'NORMAL_MONITORING';actions=['Review stock exposure and confirm replenishment constraints.'] if stock else ['Investigate the largest verified deviations.'] if anomalies else ['Continue routine monitoring.']
 else:
  high=int(data.get('high_risk',0));medium=int(data.get('medium_risk',0));status='MANUAL_REVIEW' if high else 'REVIEW_RECOMMENDED' if medium else 'STANDARD_PROCESS';actions=['Prioritize high-risk records for accountable human review.'] if high else ['Review medium-risk records and verify source data.'] if medium else ['Continue the standard process with routine monitoring.']
 return {'headline':'Analysis decision support','description':'Structured summary generated from verified model aggregates.','decision_status':status,'priority_actions':actions,'evidence':[f'{k}: {v}' for k,v in data.items() if isinstance(v,(int,float,str))][:8],'limitations':[reason,'This output is advisory and requires human review.'],'generated_by':'deterministic_fallback'}

def analyze(service:str,data:dict[str,Any]):
 if service not in SYSTEM_PROMPTS:raise ValueError('Unsupported SLM service.')
 safe={str(k):v for k,v in data.items() if isinstance(v,(str,int,float,bool)) or v is None}
 try:
  llm=_load();response=llm.create_chat_completion(messages=[{'role':'system','content':SYSTEM_PROMPTS[service]},{'role':'user','content':'Verified analysis aggregates:\n'+json.dumps(safe,ensure_ascii=False)+'\nReturn the required JSON object only.'}],temperature=0.1,top_p=0.8,max_tokens=500,response_format={'type':'json_object'})
  text=response['choices'][0]['message']['content'];report=json.loads(text)
  required={'headline','description','decision_status','priority_actions','evidence','limitations'}
  if not required.issubset(report) or report['decision_status'] not in ALLOWED[service]:raise ValueError('Invalid structured SLM response.')
  for key in ('priority_actions','evidence','limitations'):
   if not isinstance(report[key],list):raise ValueError('Invalid report list field.')
  report['generated_by']='local_slm';return report
 except Exception as exc:return _fallback(service,safe,str(exc))
