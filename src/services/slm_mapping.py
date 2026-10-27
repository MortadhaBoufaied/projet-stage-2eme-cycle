from __future__ import annotations
import json
import pandas as pd
from src.services.schema import suggest_mapping
from src.services.slm_assistant import _load
MIN_CONFIDENCE=0.90

def map_columns(df:pd.DataFrame,required:list[str],service='forecast'):
    mapping=suggest_mapping(df.columns,required)
    unresolved=[f for f in required if not mapping.get(f)]
    report={'used':False,'installed':False,'accepted':[],'rejected':[],'unresolved':unresolved,'message':'Deterministic mapping resolved available columns.'}
    if not unresolved:return mapping,report
    unused=[str(c) for c in df.columns if c not in set(mapping.values())]
    try:
        llm=_load();report['installed']=True;report['used']=True
        profiles=[]
        for c in unused:
            series=df[c];profiles.append({'column':c,'dtype':str(series.dtype),'sample':[str(v)[:50] for v in series.dropna().head(3)]})
        prompt={'service':service,'required_fields':unresolved,'source_columns':unused,'profiles':profiles,
                'rule':'Return only semantically equivalent mappings. Never invent missing information. Minimum confidence is 0.90.'}
        response=llm.create_chat_completion(messages=[{'role':'system','content':'Return JSON only: {"compatible":true,"mappings":[{"field":"...","source":"...","confidence":0.0}]}.'},{'role':'user','content':json.dumps(prompt)}],temperature=0,max_tokens=500,response_format={'type':'json_object'})
        payload=json.loads(response['choices'][0]['message']['content']);used=set(mapping.values())
        for item in payload.get('mappings',[]):
            field=item.get('field');source=item.get('source');confidence=float(item.get('confidence',0))
            if field in unresolved and source in unused and source not in used and confidence>=MIN_CONFIDENCE and payload.get('compatible',True):
                mapping[field]=source;used.add(source);report['accepted'].append(item)
            else:report['rejected'].append(item)
        report['message']='SLM mapping completed. Suggestions below 90% were rejected.'
    except Exception as exc:report['message']=f'SLM was not used: {exc}'
    report['unresolved']=[f for f in required if not mapping.get(f)]
    return mapping,report
