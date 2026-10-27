from __future__ import annotations
import numpy as np
import pandas as pd

HISTORY_FEATURES = [
    'customer_history_available','previous_invoice_count','previous_late_invoice_count',
    'previous_late_ratio','recent_5_late_ratio','previous_average_invoice_amount',
    'invoice_vs_customer_average','average_previous_delay_days','maximum_previous_delay_days',
    'days_since_previous_invoice','consecutive_previous_late_count'
]

def _norm(name): return str(name).strip().lower().replace(' ','_')
def _date(series):
    raw=series.astype('string').str.strip().str.replace(r'\.0$','',regex=True)
    compact=pd.to_datetime(raw.where(raw.str.fullmatch(r'\d{8}')),format='%Y%m%d',errors='coerce')
    return compact.fillna(pd.to_datetime(raw,errors='coerce'))
def find_column(df,*names):
    by={_norm(c):c for c in df.columns}
    return next((by[_norm(n)] for n in names if _norm(n) in by),None)

def prepare_reference(df):
    """Store auditable invoice history; outcome is usable only after clear_date."""
    cust=find_column(df,'cust_number','customer_id','client_id')
    posting=find_column(df,'posting_date','invoice_date','document_create_date')
    due=find_column(df,'due_in_date','due_date')
    clear=find_column(df,'clear_date','clearing_date','payment_date')
    amount=find_column(df,'total_open_amount','invoice_amount')
    target=find_column(df,'is_late','default_next_month')
    if not cust or not posting: return pd.DataFrame()
    r=pd.DataFrame({'cust_number':df[cust].astype('string').str.strip(),'posting_date':_date(df[posting])})
    r['due_date']=_date(df[due]) if due else pd.NaT
    r['clear_date']=_date(df[clear]) if clear else pd.NaT
    r['amount']=pd.to_numeric(df[amount],errors='coerce') if amount else np.nan
    if target: r['is_late']=pd.to_numeric(df[target],errors='coerce')
    else: r['is_late']=(r.clear_date>r.due_date).astype(float)
    r['delay_days']=(r.clear_date-r.due_date).dt.days.clip(lower=0)
    return r.dropna(subset=['cust_number','posting_date']).sort_values(['cust_number','posting_date']).reset_index(drop=True)

def _profile(prior,current_amount,current_date):
    if prior.empty:
        return [0,0,0,0.,0.,0.,1.,0.,0.,0.,0]
    observed=prior[prior.clear_date.notna() & (prior.clear_date<=current_date)].copy()
    amounts=prior.amount.dropna();avg=float(amounts.mean()) if len(amounts) else 0.
    late=observed.is_late.fillna(0).astype(int)
    delays=observed.delay_days.dropna()
    consecutive=0
    for value in reversed(late.tolist()):
        if value==1: consecutive+=1
        else: break
    ratio=float(late.mean()) if len(late) else 0.
    recent=float(late.tail(5).mean()) if len(late) else 0.
    last=prior.posting_date.max();days=max(0,(current_date-last).days) if pd.notna(last) else 0
    relative=float(current_amount/avg) if avg and pd.notna(current_amount) else 1.
    return [1,len(prior),int(late.sum()),ratio,recent,avg,relative,float(delays.mean()) if len(delays) else 0.,float(delays.max()) if len(delays) else 0.,days,consecutive]

def enrich_current(current,reference,assessment_date_column=None):
    """Add history known strictly before each current invoice assessment date."""
    d=current.copy();cust=find_column(d,'cust_number','customer_id','client_id')
    posting=find_column(d,assessment_date_column or 'posting_date','invoice_date','document_create_date')
    amount=find_column(d,'total_open_amount','invoice_amount')
    dates=_date(d[posting]) if posting else pd.Series(pd.Timestamp.now().normalize(),index=d.index)
    amounts=pd.to_numeric(d[amount],errors='coerce') if amount else pd.Series(np.nan,index=d.index)
    groups={k:g for k,g in reference.groupby('cust_number')} if reference is not None and not reference.empty else {}
    rows=[]
    for pos,idx in enumerate(d.index):
        customer=str(d.at[idx,cust]).strip() if cust else ''
        date=dates.loc[idx] if pd.notna(dates.loc[idx]) else pd.Timestamp.now().normalize()
        prior=groups.get(customer,pd.DataFrame(columns=reference.columns if reference is not None else []))
        prior=prior[prior.posting_date<date] if not prior.empty else prior
        rows.append(_profile(prior,amounts.loc[idx],date))
    hist=pd.DataFrame(rows,columns=HISTORY_FEATURES,index=d.index)
    return pd.concat([d,hist],axis=1)

def add_date_features(df):
    d=df.copy();date_cols=[]
    for c in list(d.columns):
        key=_norm(c)
        if 'date' in key or key in {'due_in_date','baseline_create_date','document_create_date','document_create_date.1','posting_date'}:
            parsed=_date(d[c])
            if parsed.notna().mean()>=.5:
                base=key.replace('.','_')
                d[f'{base}_year']=parsed.dt.year;d[f'{base}_month']=parsed.dt.month
                d[f'{base}_dayofweek']=parsed.dt.dayofweek;date_cols.append(c)
    posting=find_column(d,'posting_date');due=find_column(d,'due_in_date','due_date');created=find_column(d,'document_create_date')
    if posting and due:d['days_posting_to_due']=(_date(d[due])-_date(d[posting])).dt.days
    if created and posting:d['days_creation_to_posting']=(_date(d[posting])-_date(d[created])).dt.days
    return d.drop(columns=date_cols,errors='ignore')


def enrich_training_history(df):
    """Vectorized leakage-safe history features for training invoices.

    Invoice amount/count features use earlier posting dates. Payment outcome
    features use only outcomes whose clear date is on or before assessment.
    The original row order and index are preserved.
    """
    d = df.copy()
    if d.empty:
        for c in HISTORY_FEATURES:
            d[c] = 0.0
        return d

    customer = find_column(d, 'cust_number', 'customer_id', 'client_id')
    posting = find_column(d, 'posting_date', 'invoice_date', 'document_create_date')
    amount_col = find_column(d, 'total_open_amount', 'invoice_amount')
    if not customer or not posting:
        for c in HISTORY_FEATURES:
            d[c] = 0.0
        return d

    work = d.copy()
    work['_original_order'] = np.arange(len(work))
    work['_customer'] = work[customer].astype('string').fillna('__missing__')
    work['_assessment_date'] = _date(work[posting])
    work['_amount'] = pd.to_numeric(work[amount_col], errors='coerce') if amount_col else np.nan
    work = work.sort_values(['_customer', '_assessment_date', '_original_order'], kind='stable')
    g = work.groupby('_customer', sort=False, dropna=False)

    work['previous_invoice_count'] = g.cumcount().astype(float)
    amount_sum = g['_amount'].cumsum() - work['_amount'].fillna(0)
    amount_count = g['_amount'].cumcount()
    work['previous_average_invoice_amount'] = amount_sum.div(amount_count.replace(0, np.nan)).fillna(0.0)
    work['invoice_vs_customer_average'] = work['_amount'].div(work['previous_average_invoice_amount'].replace(0, np.nan)).fillna(0.0)
    previous_date = g['_assessment_date'].shift(1)
    work['days_since_previous_invoice'] = (work['_assessment_date'] - previous_date).dt.days.clip(lower=0).fillna(0.0)

    # Build outcome events at the date they became known, then as-of join them
    # to invoices. This prevents future clear/payment outcomes leaking backward.
    clear_col = find_column(work, 'clear_date', 'clearing_date', 'payment_date')
    due_col = find_column(work, 'due_in_date', 'due_date')
    late_col = find_column(work, 'is_late', 'default_next_month')
    events = work[['_customer', '_original_order']].copy()
    if clear_col:
        events['_known_date'] = _date(work[clear_col])
    else:
        events['_known_date'] = work['_assessment_date']
    if late_col:
        events['_late'] = pd.to_numeric(work[late_col], errors='coerce')
    elif clear_col and due_col:
        events['_late'] = (_date(work[clear_col]) > _date(work[due_col])).astype(float)
    else:
        events['_late'] = np.nan
    if clear_col and due_col:
        events['_delay'] = (_date(work[clear_col]) - _date(work[due_col])).dt.days.clip(lower=0)
    else:
        events['_delay'] = np.nan
    events = events.dropna(subset=['_known_date', '_late']).sort_values(['_customer', '_known_date', '_original_order'], kind='stable')

    if not events.empty:
        eg = events.groupby('_customer', sort=False, dropna=False)
        events['_late_count'] = eg['_late'].cumsum()
        events['_outcome_count'] = eg.cumcount() + 1
        events['_late_ratio'] = events['_late_count'] / events['_outcome_count']
        events['_delay_sum'] = eg['_delay'].cumsum()
        events['_delay_count'] = eg['_delay'].cumcount() + 1
        events['_avg_delay'] = events['_delay_sum'] / events['_delay_count']
        events['_max_delay'] = eg['_delay'].cummax()
        events['_recent5'] = eg['_late'].transform(lambda s: s.rolling(5, min_periods=1).mean())
        # Consecutive late count, vectorized by runs of non-late outcomes.
        reset = events['_late'].ne(1).groupby(events['_customer']).cumsum()
        events['_consecutive'] = events['_late'].eq(1).astype(int).groupby([events['_customer'], reset]).cumsum()
        left = work[['_customer', '_assessment_date', '_original_order']].sort_values(['_assessment_date', '_customer', '_original_order'], kind='stable')
        right = events.sort_values(['_known_date', '_customer', '_original_order'], kind='stable')
        merged = pd.merge_asof(left, right, left_on='_assessment_date', right_on='_known_date', by='_customer', direction='backward', allow_exact_matches=True)
        merged = merged.set_index('_original_order_x' if '_original_order_x' in merged else '_original_order')
        mapping = {
            'previous_late_invoice_count': '_late_count',
            'previous_late_ratio': '_late_ratio',
            'recent_5_late_ratio': '_recent5',
            'average_previous_delay_days': '_avg_delay',
            'maximum_previous_delay_days': '_max_delay',
            'consecutive_previous_late_count': '_consecutive',
        }
        for dst, src in mapping.items():
            work[dst] = work['_original_order'].map(merged[src]).fillna(0.0)
    else:
        for dst in ('previous_late_invoice_count','previous_late_ratio','recent_5_late_ratio','average_previous_delay_days','maximum_previous_delay_days','consecutive_previous_late_count'):
            work[dst] = 0.0

    work['customer_history_available'] = (work['previous_invoice_count'] > 0).astype(float)
    for c in HISTORY_FEATURES:
        if c not in work:
            work[c] = 0.0
        work[c] = pd.to_numeric(work[c], errors='coerce').fillna(0.0)
    work = work.sort_values('_original_order', kind='stable').drop(columns=[c for c in work.columns if c.startswith('_')], errors='ignore')
    work.index = d.index
    return work
