from __future__ import annotations
import re
from dataclasses import dataclass
import pandas as pd

@dataclass
class ContractIssue:
    level: str
    code: str
    column: str
    message: str
    count: int = 0

@dataclass
class ContractReport:
    valid: bool
    rows: int
    columns: int
    duplicates: int
    missing_cells: int
    issues: list

def _norm(value):
    return re.sub(r'[^a-z0-9]+','',str(value).strip().lower())

def model_features(model,metadata):
    features=list((metadata or {}).get('features') or [])
    if not features and hasattr(model,'feature_names_in_'):
        features=list(model.feature_names_in_)
    if not features and hasattr(model,'named_steps'):
        pre=model.named_steps.get('pre')
        if pre is not None and hasattr(pre,'feature_names_in_'):
            features=list(pre.feature_names_in_)
    return [str(x) for x in features]

def _encoded_parent(feature, columns):
    """Return (raw column, category) for a legacy get_dummies feature.

    Header spelling is normalized, so `document type_RV` can be rebuilt from
    `document_type`, `Document Type`, or a header with surrounding whitespace.
    """
    feature_text = str(feature).strip()
    matches = []
    for column in columns:
        column_key = column
        column_text = str(column).strip()
        # Try every split point because raw column names may themselves contain `_`.
        for split in range(1, len(feature_text)):
            if feature_text[split] != '_':
                continue
            parent, category = feature_text[:split], feature_text[split + 1:]
            if category and _norm(parent) == _norm(column_text):
                matches.append((column_key, category, len(_norm(parent))))
    if not matches:
        return None
    column, category, _ = max(matches, key=lambda item: item[2])
    return column, category

def raw_model_features(model,metadata,available_columns=None):
    encoded=model_features(model,metadata)
    available=[str(c) for c in (available_columns or [])]
    raw=[]
    for feature in encoded:
        encoded_parent=_encoded_parent(feature,available)
        name=encoded_parent[0] if encoded_parent else feature
        if name not in raw:raw.append(name)
    return raw

def align_to_model(frame,model,metadata):
    """Create the exact matrix expected by current and legacy saved models.

    New models consume raw columns through their saved preprocessing pipeline.
    Legacy models may store one-hot names. For those models, raw categorical columns
    are converted to the expected dummy columns; categories absent in a test file
    correctly become zero rather than being reported as missing.
    """
    expected=model_features(model,metadata)
    if not expected:
        raise ValueError('The active model has no saved feature contract. Retrain and activate the model once.')
    source_by_norm={_norm(c):c for c in frame.columns}
    aligned=pd.DataFrame(index=frame.index)
    missing=[]
    generated=[]
    for feature in expected:
        if feature in frame.columns:
            aligned[feature]=frame[feature]
            continue
        equivalent=source_by_norm.get(_norm(feature))
        if equivalent is not None:
            aligned[feature]=frame[equivalent]
            continue
        encoded_parent=_encoded_parent(feature,frame.columns)
        if encoded_parent is not None:
            parent, category = encoded_parent
            values=frame[parent].astype('string').str.strip().fillna('')
            aligned[feature]=(values==str(category)).astype('int8')
            generated.append(feature)
            continue
        missing.append(feature)
    return aligned,expected,missing,generated

def validate_for_model(frame,model,metadata):
    aligned,features,missing,generated=align_to_model(frame,model,metadata)
    issues=[]
    if len(frame)==0:issues.append(ContractIssue('error','empty','','The uploaded dataset is empty.'))
    if missing:
        issues.append(ContractIssue('error','missing_model_features','',
            'The file does not match the active model. Missing raw training feature(s): '+', '.join(missing),len(missing)))
    if generated:
        issues.append(ContractIssue('info','legacy_categories_encoded','',
            f'{len(generated)} legacy categorical indicator columns were reconstructed automatically.',len(generated)))
    duplicates=int(frame.duplicated().sum())
    if duplicates:issues.append(ContractIssue('warning','duplicates','',f'{duplicates} duplicate rows were detected.',duplicates))
    for feature in features:
        if feature in aligned:
            count=int(aligned[feature].isna().sum())
            if count:issues.append(ContractIssue('warning','missing_values',feature,
                f'{feature} contains {count} missing values. The saved pipeline will apply its imputation rule.',count))
    valid=not any(x.level=='error' for x in issues)
    return aligned,ContractReport(valid,len(frame),len(frame.columns),duplicates,int(frame.isna().sum().sum()),issues)

def prepare_model_input(frame,model,metadata):
    aligned,features,missing,_=align_to_model(frame,model,metadata)
    if missing:raise ValueError('Missing raw training feature(s): '+', '.join(missing))
    return aligned.loc[:,features].copy()

def template_for_model(model,metadata):
    """Generate a raw upload template, including inferred parents for legacy dummies."""
    expected=model_features(model,metadata)
    raw=list((metadata or {}).get('raw_features') or [])
    if not raw:
        # Known categorical parents can be recovered unambiguously from legacy names.
        known=('business_code','invoice_currency','document type','cust_payment_terms')
        for feature in expected:
            parent=next((p for p in known if feature.startswith(p+'_')),None)
            name=parent or feature
            if name not in raw:raw.append(name)
    return pd.DataFrame(columns=raw)

model_template=template_for_model
