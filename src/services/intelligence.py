import os,json,urllib.request
import numpy as np
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


def _metric_value(metrics, key, default=0.0):
    try:
        value=float(metrics.get(key, default))
        return value if np.isfinite(value) else default
    except (TypeError, ValueError):
        return default

def _deterministic_model_ranking(task, runs):
    scored=[]
    for run in runs:
        m=run.get('validation',{})
        if task=='credit':
            score=(.18*_metric_value(m,'PR-AUC')+.14*_metric_value(m,'ROC-AUC')+
                   .14*_metric_value(m,'F1')+.14*_metric_value(m,'Recall')+
                   .10*_metric_value(m,'Precision')+.12*_metric_value(m,'Balanced Accuracy')+
                   .12*_metric_value(m,'MCC')+.06*_metric_value(m,'Accuracy'))
            floor=min(_metric_value(m,'Recall'),_metric_value(m,'Specificity'),_metric_value(m,'Precision'))
            score-=.12*max(0,.55-floor)
        else:
            wape=_metric_value(m,'WAPE',1e9);rmse=_metric_value(m,'RMSE',1e9);mae=_metric_value(m,'MAE',1e9);r2=_metric_value(m,'R2',-1)
            score=-(.55*wape+.20*(rmse/(abs(rmse)+1))+.15*(mae/(abs(mae)+1)))+.10*r2
        scored.append((score,run['algorithm']))
    return max(scored)[1],sorted(scored,reverse=True)

def recommend_model(task, runs, quality=None):
    """Recommend one trained model from all validation metrics; SLM is advisory only."""
    fallback, ranking=_deterministic_model_ranking(task,runs)
    evidence=[{'algorithm':r['algorithm'],'validation':r.get('validation',{}),
               'test':r.get('test',{}),'features':r.get('features',[]),
               'feature_count':len(r.get('features',[])),
               'column_meanings':r.get('column_meanings',{})} for r in runs]
    endpoint=os.getenv('SLM_ENDPOINT','');model=os.getenv('SLM_MODEL','qwen2.5:1.5b')
    base={'recommended_algorithm':fallback,'reasoning':'Composite validation ranking considered every available metric.','generator':'deterministic fallback','ranking':ranking,'evidence':evidence}
    if not endpoint:return base
    prompt={'task':task,'models':evidence,'quality':quality or {},'allowed_algorithms':[r['algorithm'] for r in runs],
            'rules':['Use validation metrics for selection; test metrics are context only and must not drive selection.',
                     'Consider every supplied metric and the complete feature contract.',
                     'For payment risk balance PR-AUC, ROC-AUC, F1, recall, precision, specificity, balanced accuracy, MCC and accuracy.',
                     'For forecasting prefer low WAPE, RMSE, MAE and strong R2.',
                     'Return one listed algorithm only. Admin retains final authority.']}
    try:
        req=urllib.request.Request(endpoint,data=json.dumps({'model':model,'stream':False,'prompt':'Return strict JSON with recommended_algorithm and reasoning only: '+json.dumps(prompt,default=str)}).encode(),headers={'Content-Type':'application/json'})
        raw=json.loads(urllib.request.urlopen(req,timeout=30).read());out=json.loads(raw['response'])
        if out.get('recommended_algorithm') not in prompt['allowed_algorithms']:return base
        return {**base,**out,'generator':'local SLM'}
    except Exception:return base
