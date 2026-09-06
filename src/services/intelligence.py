import os,json,urllib.request
def deterministic(task,metrics,quality):
    strengths=[];weak=[];actions=[]
    if task=='credit':
        if (metrics.get('ROC-AUC') or 0)>=.8: strengths.append('Good class separation on holdout data.')
        if (metrics.get('Recall') or 0)<.65: weak.append('Recall is limited, so some risky records may be missed.');actions.append('Consider threshold tuning and more representative positive-class examples.')
        if (metrics.get('Precision') or 0)<.6: weak.append('Precision is limited, increasing manual-review load.');actions.append('Review false positives and improve discriminating features.')
    else:
        w=metrics.get('WAPE');
        if w is not None and w<=.2: strengths.append('Forecast error is relatively controlled on holdout data.')
        if w is None or w>.3: weak.append('Forecast error is material on holdout data.');actions.append('Review time coverage, product history, and additional demand drivers.')
    if quality.get('duplicates'): actions.append('Review duplicate training records.')
    score=2*len(strengths)-2*len(weak); health='Excellent' if score>=4 else 'Good' if score>=1 else 'Fair' if score>=-1 else 'Weak'
    return {'generator':'deterministic fallback','health':health,'executive_summary':f'{task.title()} model health is {health}.','strengths':strengths or ['The pipeline completed with a separated holdout evaluation.'],'weaknesses':weak or ['No critical weakness was triggered by configured rules.'],'recommendations':actions or ['Continue monitoring drift and holdout performance.'],'evidence_used':metrics,'limitations':['This interpretation uses only supplied metrics and data-quality facts.'],'human_review_notice':'Decision support only. A responsible employee should validate consequential actions.'}
def interpret(task,metrics,quality):
    fallback=deterministic(task,metrics,quality); endpoint=os.getenv('SLM_ENDPOINT',''); model=os.getenv('SLM_MODEL','qwen2.5:1.5b')
    if not endpoint:return fallback
    payload={'model':model,'stream':False,'prompt':'Return strict JSON. Interpret only this verified evidence; never alter numbers or invent facts: '+json.dumps({'task':task,'metrics':metrics,'quality':quality,'required':fallback})}
    try:
        req=urllib.request.Request(endpoint,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'}); raw=json.loads(urllib.request.urlopen(req,timeout=20).read()); out=json.loads(raw['response']); out['generator']='local SLM';out['evidence_used']=metrics;out['human_review_notice']=fallback['human_review_notice'];return out
    except Exception:return fallback
