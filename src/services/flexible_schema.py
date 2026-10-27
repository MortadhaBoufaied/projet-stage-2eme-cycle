import pandas as pd
import numpy as np
import os
import json
import urllib.request
import hashlib
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Schema cache storage
SCHEMA_CACHE_DIR = Path.home() / '.finance_stage' / 'schema_cache'
SCHEMA_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Template storage
TEMPLATE_DIR = Path.home() / '.finance_stage' / 'templates'
TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)

# Schema versioning storage
SCHEMA_VERSIONS_DIR = Path.home() / '.finance_stage' / 'schema_versions'
SCHEMA_VERSIONS_DIR.mkdir(parents=True, exist_ok=True)

@dataclass
class SchemaVersion:
    version_id: str
    fingerprint: str
    columns: List[str]
    target: str
    features: List[str]
    task_type: str
    model_version: Optional[str] = None
    performance_metrics: Dict = None
    created_at: str = None
    created_by: str = "admin"

# Schema versioning storage
SCHEMA_VERSIONS_DIR = Path.home() / '.finance_stage' / 'schema_versions'
SCHEMA_VERSIONS_DIR.mkdir(parents=True, exist_ok=True)

def get_schema_fingerprint(df: pd.DataFrame) -> str:
    """Create a unique fingerprint based on column structure."""
    # Sort columns to ensure consistent fingerprint
    sorted_cols = sorted(df.columns.tolist())
    # Create fingerprint from column names and their data types
    col_signature = [(col, str(df[col].dtype)) for col in sorted_cols]
    signature_str = json.dumps({'schema_mapping_version': 2, 'columns': col_signature}, sort_keys=True)
    return hashlib.md5(signature_str.encode()).hexdigest()

def get_cached_schema(fingerprint: str) -> Optional[dict]:
    """Retrieve cached schema if available."""
    cache_file = SCHEMA_CACHE_DIR / f"{fingerprint}.json"
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception:
            return None
    return None

def cache_schema(fingerprint: str, schema_data: dict):
    """Cache schema for future use."""
    cache_file = SCHEMA_CACHE_DIR / f"{fingerprint}.json"
    try:
        with open(cache_file, 'w') as f:
            json.dump(schema_data, f, indent=2)
    except Exception as e:
        print(f"Failed to cache schema: {e}")

def clear_schema_cache():
    """Clear all cached schemas."""
    for cache_file in SCHEMA_CACHE_DIR.glob("*.json"):
        try:
            cache_file.unlink()
        except Exception:
            pass

@dataclass
class ColumnInfo:
    name: str
    dtype: str  # 'number', 'integer', 'string', 'date', 'boolean', 'categorical'
    nullable: bool
    unique_count: int
    missing_count: int
    sample_values: List[str]
    suggested_role: str = 'feature'  # 'feature', 'target', 'id', 'datetime', 'ignore'
    confidence: float = 0.5  # 0-1 confidence in the detection

@dataclass
class FlexibleSchema:
    columns: List[ColumnInfo]
    suggested_target: Optional[str]
    suggested_features: List[str]
    suggested_ids: List[str]
    task_type: str  # 'classification' or 'regression' or 'forecast'
    slm_suggestions: List[str] = None  # AI-provided suggestions
    slm_reasoning: Dict = None  # AI reasoning for decisions
    from_cache: bool = False  # Whether schema was loaded from cache

def generate_template_from_schema(schema: FlexibleSchema, task_name: str = "training_data") -> pd.DataFrame:
    """Generate an empty CSV template based on the detected schema."""
    # Create empty dataframe with the detected columns
    template_data = {}
    
    for col_info in schema.columns:
        # Set appropriate sample/empty values based on data type
        if col_info.dtype == 'number':
            template_data[col_info.name] = [0.0]  # Empty numeric
        elif col_info.dtype == 'integer':
            template_data[col_info.name] = [0]  # Empty integer
        elif col_info.dtype == 'date':
            template_data[col_info.name] = [pd.NaT]  # Empty date
        elif col_info.dtype == 'boolean':
            template_data[col_info.name] = [False]  # Empty boolean
        elif col_info.dtype == 'categorical':
            # Show sample categories if available
            if col_info.sample_values:
                template_data[col_info.name] = [col_info.sample_values[0]]
            else:
                template_data[col_info.name] = [""]  # Empty string
        else:
            template_data[col_info.name] = [""]  # Empty string for text
    
    template_df = pd.DataFrame(template_data)
    
    # Add metadata row at the top with column descriptions
    metadata_row = {}
    for col_info in schema.columns:
        role_emoji = {
            'target': '🎯',
            'feature': '📊', 
            'id': '🆔',
            'datetime': '📅',
            'ignore': '⏭️'
        }.get(col_info.suggested_role, '❓')
        
        # Add helpful description
        description = f"{role_emoji} {col_info.dtype.upper()} - {col_info.suggested_role.upper()}"
        if col_info.sample_values:
            description += f" (example: {col_info.sample_values[0]})"
        
        metadata_row[col_info.name] = description
    
    # Insert metadata row at the beginning
    template_df = pd.concat([pd.DataFrame([metadata_row]), template_df], ignore_index=True)
    
    return template_df

def save_template(schema: FlexibleSchema, fingerprint: str, task_name: str = "training_data"):
    """Save template to file and return the file path."""
    template_df = generate_template_from_schema(schema, task_name)
    
    # Create filename based on fingerprint and task
    template_filename = f"template_{fingerprint[:8]}_{task_name}.csv"
    template_path = TEMPLATE_DIR / template_filename
    
    try:
        template_df.to_csv(template_path, index=False)
        return template_path
    except Exception as e:
        print(f"Failed to save template: {e}")
        return None

def get_current_template(fingerprint: str) -> Optional[Path]:
    """Get the current template for this schema fingerprint."""
    template_files = list(TEMPLATE_DIR.glob(f"template_{fingerprint[:8]}_*.csv"))
    if template_files:
        return template_files[0]  # Return the most recent template
    return None

def update_template_on_schema_change(df: pd.DataFrame, schema: FlexibleSchema, fingerprint: str):
    """Update template when schema changes."""
    # Check if template exists for this fingerprint
    existing_template = get_current_template(fingerprint)
    
    if existing_template:
        # Backup old template
        backup_path = existing_template.with_suffix('.csv.backup')
        try:
            existing_template.rename(backup_path)
        except Exception:
            pass
    
    # Generate and save new template
    return save_template(schema, fingerprint)

def save_schema_version(schema: FlexibleSchema, fingerprint: str, task_type: str, model_version: str = None):
    """Save a new schema version for tracking."""
    version_id = f"schema_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{fingerprint[:8]}"
    
    schema_version = SchemaVersion(
        version_id=version_id,
        fingerprint=fingerprint,
        columns=[c.name for c in schema.columns],
        target=schema.suggested_target,
        features=schema.suggested_features,
        task_type=task_type,
        model_version=model_version,
        created_at=datetime.now(timezone.utc).isoformat()
    )
    
    version_file = SCHEMA_VERSIONS_DIR / f"{version_id}.json"
    try:
        with open(version_file, 'w') as f:
            json.dump(asdict(schema_version), f, indent=2)
        return version_id
    except Exception as e:
        print(f"Failed to save schema version: {e}")
        return None

def get_schema_versions(task_type: str = None) -> List[SchemaVersion]:
    """Get all schema versions, optionally filtered by task type."""
    versions = []
    for version_file in SCHEMA_VERSIONS_DIR.glob("schema_*.json"):
        try:
            with open(version_file, 'r') as f:
                version_data = json.load(f)
                if task_type is None or version_data.get('task_type') == task_type:
                    versions.append(SchemaVersion(**version_data))
        except Exception:
            pass
    
    # Sort by creation time (newest first)
    versions.sort(key=lambda x: x.created_at or '', reverse=True)
    return versions

def compare_schemas(old_fingerprint: str, new_fingerprint: str) -> Dict:
    """Compare two schema fingerprints and highlight differences."""
    old_versions = [v for v in get_schema_versions() if v.fingerprint == old_fingerprint]
    new_versions = [v for v in get_schema_versions() if v.fingerprint == new_fingerprint]
    
    if not old_versions or not new_versions:
        return {'can_compare': False, 'reason': 'One or both schemas not found in version history'}
    
    old_schema = old_versions[0]
    new_schema = new_versions[0]
    
    old_cols = set(old_schema.columns)
    new_cols = set(new_schema.columns)
    
    added_features = new_cols - old_cols
    removed_features = old_cols - new_cols
    common_features = old_cols & new_cols
    
    target_changed = old_schema.target != new_schema.target
    
    return {
        'can_compare': True,
        'old_version': old_schema.version_id,
        'new_version': new_schema.version_id,
        'old_created': old_schema.created_at,
        'new_created': new_schema.created_at,
        'added_features': list(added_features),
        'removed_features': list(removed_features),
        'common_features': list(common_features),
        'target_changed': target_changed,
        'old_target': old_schema.target,
        'new_target': new_schema.target,
        'feature_count_change': len(new_cols) - len(old_cols)
    }

def get_latest_schema_version(task_type: str) -> Optional[SchemaVersion]:
    """Get the most recent schema version for a task type."""
    versions = get_schema_versions(task_type)
    return versions[0] if versions else None

def check_schema_migration_required(fingerprint: str, task_type: str) -> dict:
    """Check if schema migration is required and provide migration info."""
    latest_schema = get_latest_schema_version(task_type)
    
    if not latest_schema:
        return {'migration_required': False, 'reason': 'No previous schema found'}
    
    if latest_schema.fingerprint == fingerprint:
        return {'migration_required': False, 'reason': 'Schema structure unchanged'}
    
    # Schema has changed - provide migration details
    comparison = compare_schemas(latest_schema.fingerprint, fingerprint)
    
    return {
        'migration_required': True,
        'old_schema': latest_schema,
        'comparison': comparison,
        'can_compare': comparison.get('can_compare', False),
        'message': f"New file structure detected ({len(comparison.get('added_features', []))} added, {len(comparison.get('removed_features', []))} removed features)"
    }

def suggest_schema_improvements(current_schema: FlexibleSchema, performance_metrics: Dict = None) -> List[str]:
    """Suggest potential schema improvements based on current schema and performance."""
    suggestions = []
    
    # Feature count analysis
    if len(current_schema.suggested_features) < 5:
        suggestions.append("Consider adding more features - current feature count may be limiting model performance")
    
    # Target variable analysis
    if current_schema.suggested_target:
        target_col = current_schema.suggested_target
        target_info = next((c for c in current_schema.columns if c.name == target_col), None)
        if target_info and target_info.unique_count < 2:
            suggestions.append("Target variable has very low cardinality - may need more diverse training data")
    
    # Missing value analysis
    high_missing_cols = [c.name for c in current_schema.columns if c.missing_count / len(current_schema.columns) > 0.5]
    if high_missing_cols:
        suggestions.append(f"Consider addressing high missing values in: {', '.join(high_missing_cols[:3])}")
    
    # Performance-based suggestions
    if performance_metrics:
        if performance_metrics.get('ROC-AUC', 0) < 0.7:
            suggestions.append("Current ROC-AUC suggests model may benefit from additional predictive features")
        if performance_metrics.get('WAPE', 1.0) > 0.3:
            suggestions.append("High WAPE indicates forecasting may need additional time-series features")
    
    # Domain-specific suggestions
    if current_schema.task_type == 'classification':
        if not any('ratio' in c.name.lower() or 'rate' in c.name.lower() for c in current_schema.columns):
            suggestions.append("Consider adding ratio/rate features (e.g., debt-to-income, payment-to-balance)")
    
    elif current_schema.task_type == 'regression':
        if not any('rolling' in c.name.lower() or 'moving' in c.name.lower() for c in current_schema.columns):
            suggestions.append("Consider adding rolling/moving average features for time-series patterns")
    
    return suggestions

def detect_column_info(series: pd.Series, col_name: str) -> ColumnInfo:
    """Detect column type and characteristics from data."""
    series_clean = series.dropna()
    missing_count = series.isna().sum()
    unique_count = series_clean.nunique()
    sample_values = series_clean.head(5).astype(str).tolist()
    
    # Detect data type
    dtype = 'string'
    nullable = missing_count > 0
    
    # Initialize default role and confidence
    suggested_role = 'feature'
    confidence = 0.5
    
    # Try numeric
    numeric_series = pd.to_numeric(series_clean, errors='coerce')
    if numeric_series.notna().sum() / len(series_clean) > 0.8:  # 80% numeric
        if numeric_series.dropna().apply(lambda x: x == int(x)).all():
            dtype = 'integer'
        else:
            dtype = 'number'
    # Try date
    elif unique_count > 10 and unique_count < len(series_clean) * 0.9:
        date_series = pd.to_datetime(series_clean, errors='coerce')
        if date_series.notna().sum() / len(series_clean) > 0.8:
            dtype = 'date'
            # Check if this is an important date column
            col_lower = str(col_name).lower()
            important_date_patterns = {'due', 'invoice', 'posting', 'create', 'period', 'fiscal', 'year', 'quarter', 'month'}
            if any(pattern in col_lower for pattern in important_date_patterns):
                # Important dates should be features by default
                suggested_role = 'feature'
                confidence = 0.7
    # Try boolean
    elif unique_count <= 2 and series_clean.astype(str).str.lower().isin(['true', 'false', 'yes', 'no', '1', '0']).all():
        dtype = 'boolean'
    # Categorical if low cardinality
    elif unique_count <= 20 and dtype == 'string':
        dtype = 'categorical'
    
    # Set default values if not set above
    if suggested_role == 'feature' and confidence == 0.5:
        suggested_role = 'feature'
        confidence = 0.7
    
    col_lower = col_name.lower()
    
    # Target detection (highest priority)
    if any(target_word in col_lower for target_word in ['target', 'label', 'outcome', 'result', 'default', 'churn', 'fraud', 'risk', 'is_late', 'late', 'delinquent']):
        suggested_role = 'target'
        confidence = 0.8
    # Data leakage detection (highest priority after target)
    elif any(leakage_word in col_lower for leakage_word in ['clear', 'settle', 'settlement', 'paid_date', 'actual', 'realized', 'realised']):
        suggested_role = 'ignore'
        confidence = 0.95
    # ID detection
    elif any(id_word in col_lower for id_word in ['id', 'key', 'code', 'identifier', 'uuid']):
        suggested_role = 'id'
        confidence = 0.9
    # Financial feature detection (enhanced logic)
    elif any(fin_word in col_lower for fin_word in ['amount', 'balance', 'payment', 'invoice', 'price', 'sales', 'revenue', 'cost', 'profit', 'quantity', 'units', 'terms', 'credit', 'debit', 'rate', 'margin', 'ratio', 'score']):
        suggested_role = 'feature'
        confidence = 0.85
    # Important date detection (but not data leakage)
    elif dtype == 'date' and any(date_word in col_lower for date_word in ['due', 'invoice', 'posting', 'create', 'period', 'fiscal', 'year', 'quarter', 'month']):
        suggested_role = 'feature'
        confidence = 0.8
    # Regular date detection
    elif dtype == 'date' or any(date_word in col_lower for date_word in ['date', 'time', 'timestamp']):
        suggested_role = 'datetime'
        confidence = 0.85
    # Ignore detection
    elif any(ignore_word in col_lower for ignore_word in ['note', 'comment', 'description', 'text', 'name']):
        suggested_role = 'ignore'
        confidence = 0.6
    
    return ColumnInfo(
        name=col_name,
        dtype=dtype,
        nullable=nullable,
        unique_count=unique_count,
        missing_count=missing_count,
        sample_values=sample_values,
        suggested_role=suggested_role,
        confidence=confidence
    )

def govern_schema_roles(df: pd.DataFrame, schema: FlexibleSchema) -> FlexibleSchema:
    """Apply deterministic prediction-time guardrails after rule/SLM suggestions.

    The SLM may suggest semantic roles, but it cannot override measurable facts:
    target/outcome leakage, empty or constant columns, near-unique identifiers,
    or safe pre-outcome dates. Every non-target column finishes in exactly one
    group: feature (Included) or id/ignore (Excluded).
    """
    if df.empty:
        return schema
    target = schema.suggested_target
    by_name = {c.name: c for c in schema.columns}
    outcome_terms = ('clear_date', 'clearing_date', 'settlement_date', 'paid_date',
                     'payment_date', 'days_late', 'delay_days', 'final_status',
                     'actual_payment', 'realized', 'realised')
    pure_id_terms = ('doc_id', 'invoice_id', 'transaction_id', 'uuid', 'row_id')
    safe_date_terms = ('posting_date', 'document_create_date', 'baseline_create_date',
                       'due_in_date', 'due_date', 'invoice_date')
    included, excluded = [], []
    n = max(len(df), 1)
    for name in df.columns:
        if name == target:
            if name in by_name:
                by_name[name].suggested_role = 'target'
                by_name[name].confidence = 1.0
            continue
        info = by_name.get(name)
        key = str(name).strip().lower().replace(' ', '_')
        series = df[name]
        unique = int(series.nunique(dropna=True))
        missing_rate = float(series.isna().mean())
        unique_ratio = unique / n
        exclude = False
        confidence = .90
        if missing_rate >= .98 or unique <= 1:
            exclude, confidence = True, 1.0
        elif any(term in key for term in outcome_terms):
            exclude, confidence = True, 1.0
        elif any(term == key or key.endswith('_' + term) for term in pure_id_terms):
            exclude, confidence = True, .99
        elif unique_ratio >= .95:
            exclude, confidence = True, .98
        elif 'name' in key and unique_ratio > .02:
            exclude, confidence = True, .95
        elif any(term in key for term in safe_date_terms):
            exclude, confidence = False, .97
        elif key.endswith('_code') and unique <= min(100, max(10, int(n * .02))):
            exclude, confidence = False, .96
        if exclude:
            excluded.append(name)
            if info:
                info.suggested_role = 'ignore' if any(t in key for t in outcome_terms) or missing_rate >= .98 or unique <= 1 else 'id'
                info.confidence = confidence
        else:
            included.append(name)
            if info:
                info.suggested_role = 'feature'
                info.confidence = max(info.confidence, confidence)
    # Completeness and exclusivity are construction invariants.
    schema.suggested_features = included
    schema.suggested_ids = excluded
    return schema

def analyze_dataframe(df: pd.DataFrame) -> FlexibleSchema:
    """Analyze a dataframe and suggest schema."""
    columns = []
    for col in df.columns:
        col_info = detect_column_info(df[col], col)
        columns.append(col_info)
    
    # Determine task type and suggest columns
    targets = [c for c in columns if c.suggested_role == 'target']
    preferred_target_names = {'is_late', 'target', 'label', 'outcome', 'default', 'default_next_month', 'fraud', 'churn'}
    preferred_targets = [c for c in columns if c.name.strip().lower() in preferred_target_names]
    if preferred_targets:
        chosen = preferred_targets[0]
        for c in targets:
            if c is not chosen and c.suggested_role == 'target':
                c.suggested_role = 'feature'
        chosen.suggested_role = 'target'
        chosen.confidence = max(chosen.confidence, 0.98)
        targets = [chosen]
    features = [c for c in columns if c.suggested_role == 'feature']
    ids = [c for c in columns if c.suggested_role == 'id']
    
    # If no explicit target, suggest based on data characteristics
    if not targets:
        # Look for binary columns (good for classification)
        binary_cols = [c for c in columns if c.dtype in ['integer', 'boolean'] and c.unique_count == 2]
        if binary_cols:
            targets = [binary_cols[0]]
            targets[0].suggested_role = 'target'
            targets[0].confidence = 0.6
        # Or numeric columns (good for regression)
        elif len([c for c in columns if c.dtype in ['number', 'integer']]) > 1:
            numeric_cols = [c for c in columns if c.dtype in ['number', 'integer']]
            targets = [numeric_cols[-1]]  # Last numeric column often target
            targets[0].suggested_role = 'target'
            targets[0].confidence = 0.5
    
    # Determine task type
    task_type = 'classification'
    if targets:
        if targets[0].dtype in ['number']:
            task_type = 'regression'
        elif targets[0].unique_count > 10:
            task_type = 'regression'
    
    # Refine features (exclude IDs, targets, and ignored columns)
    features = [c for c in columns if c.suggested_role == 'feature' and c.name not in [t.name for t in targets]]
    
    # ENHANCED: Financial domain-aware feature assignment
    # Important financial features that should be included
    important_financial_patterns = {
        'amount', 'balance', 'payment', 'invoice', 'price', 'sales', 'revenue', 
        'cost', 'profit', 'income', 'expense', 'quantity', 'units', 'orders',
        'terms', 'credit', 'debit', 'rate', 'margin', 'ratio', 'score', 'risk'
    }
    
    # Important date patterns (but exclude data leakage dates)
    important_date_patterns = {
        'due', 'invoice', 'posting', 'create', 'period', 'fiscal', 'year', 'quarter', 'month'
    }
    
    # Data leakage patterns to exclude
    leakage_patterns = {
        'clear', 'settle', 'settlement', 'paid', 'payment_date', 'result', 'outcome', 
        'final', 'actual', 'realized', 'realised'
    }
    
    # Auto-assign important financial columns as features
    for col in columns:
        if col.suggested_role != 'target' and col.suggested_role != 'id':
            col_lower = col.name.lower()
            
            # Check if it's a data leakage column
            is_leakage = any(pattern in col_lower for pattern in leakage_patterns)
            
            # Check if it's an important financial feature
            is_financial = any(pattern in col_lower for pattern in important_financial_patterns)
            
            # Check if it's an important date (not leakage)
            is_important_date = (col.dtype in ['datetime64[ns]', 'object'] and 
                                any(pattern in col_lower for pattern in important_date_patterns) and
                                not is_leakage)
            
            # Assign as feature if it's important and not already assigned
            if is_financial and not is_leakage and col not in features:
                col.suggested_role = 'feature'
                col.confidence = max(col.confidence, 0.75)
                features.append(col)
            elif is_important_date and col not in features:
                col.suggested_role = 'feature'
                col.confidence = max(col.confidence, 0.7)
                features.append(col)
    
    # Auto-assign remaining columns as features if we have too few
    if len(features) < 2:
        potential_features = [c for c in columns if c.suggested_role not in ['id', 'ignore', 'target']]
        features = potential_features[:min(10, len(potential_features))]
        for f in features:
            f.suggested_role = 'feature'
    
    schema = FlexibleSchema(
        columns=columns,
        suggested_target=targets[0].name if targets else None,
        suggested_features=[f.name for f in features],
        suggested_ids=[i.name for i in ids],
        task_type=task_type
    )
    return govern_schema_roles(df, schema)

def validate_flexible(df: pd.DataFrame, schema: FlexibleSchema, training: bool = False) -> Tuple[pd.DataFrame, dict]:
    """Validate dataframe against flexible schema with quality checks."""
    issues = []
    
    # Check for empty dataset
    if len(df) == 0:
        issues.append({
            'level': 'error',
            'code': 'empty',
            'message': 'The dataset is empty.'
        })
        return df, {'valid': False, 'issues': issues}
    
    # Check for sufficient rows
    if training and len(df) < 100:
        issues.append({
            'level': 'warning',
            'code': 'insufficient_rows',
            'message': f'Training works best with at least 100 rows; received {len(df)}.'
        })
    
    # Check for duplicates
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        issues.append({
            'level': 'warning',
            'code': 'duplicates',
            'message': f'{dup_count} duplicate rows detected.'
        })
    
    # Check for high missing values
    for col in df.columns:
        missing_pct = (df[col].isna().sum() / len(df)) * 100
        if missing_pct > 50:
            issues.append({
                'level': 'warning',
                'code': 'high_missing',
                'column': col,
                'message': f'Column {col} has {missing_pct:.1f}% missing values.'
            })
    
    # Check for low variance features
    for col in schema.suggested_features:
        if col in df.columns:
            unique_ratio = df[col].nunique() / len(df)
            if unique_ratio < 0.01 and df[col].dtype in ['number', 'integer']:
                issues.append({
                    'level': 'warning',
                    'code': 'low_variance',
                    'column': col,
                    'message': f'Feature {col} has very low variance (may not be useful).'
                })
    
    valid = not any(issue['level'] == 'error' for issue in issues)
    
    return df, {
        'valid': valid,
        'rows': len(df),
        'columns': len(df.columns),
        'duplicates': int(dup_count),
        'missing_cells': int(df.isna().sum().sum()),
        'issues': issues,
        'schema': asdict(schema)
    }

def auto_clean_dataset(df: pd.DataFrame, schema: FlexibleSchema):
    """Automatically detect and fix common data quality issues.
    
    Returns:
        tuple: (cleaned_df, cleaning_report)
    """
    df_cleaned = df.copy()
    report = {
        'original_rows': len(df_cleaned),
        'duplicates_removed': 0,
        'missing_values_filled': 0,
        'outliers_handled': 0,
        'type_conversions': 0,
        'fixes_applied': []
    }
    
    # Preserve target column to avoid modifying it
    target_col = schema.suggested_target
    if target_col in df_cleaned.columns:
        target_values = df_cleaned[target_col].copy()
    
    # 1. Remove duplicate rows
    original_count = len(df_cleaned)
    df_cleaned = df_cleaned.drop_duplicates()
    duplicates_removed = original_count - len(df_cleaned)
    if duplicates_removed > 0:
        report['duplicates_removed'] = duplicates_removed
        report['fixes_applied'].append(f"Removed {duplicates_removed:,} duplicate rows")
    
    # 2. Handle missing values (skip target column)
    for col_info in schema.columns:
        if col_info.name in df_cleaned.columns and col_info.name != target_col:
            missing_count = df_cleaned[col_info.name].isna().sum()
            if missing_count > 0:
                if col_info.dtype in ['number', 'integer']:
                    # Fill numeric with median
                    try:
                        df_cleaned[col_info.name] = pd.to_numeric(df_cleaned[col_info.name], errors='coerce')
                        median_val = df_cleaned[col_info.name].median()
                        df_cleaned[col_info.name] = df_cleaned[col_info.name].fillna(median_val)
                    except:
                        pass
                elif col_info.dtype == 'date':
                    # Fill dates with forward fill then backward fill
                    df_cleaned[col_info.name] = df_cleaned[col_info.name].ffill().bfill()
                else:
                    # Fill categorical with mode
                    mode_val = df_cleaned[col_info.name].mode()[0] if not df_cleaned[col_info.name].mode().empty else 'unknown'
                    df_cleaned[col_info.name] = df_cleaned[col_info.name].fillna(mode_val)
                
                report['missing_values_filled'] += missing_count
                report['fixes_applied'].append(f"Filled {missing_count:,} missing values in '{col_info.name}'")
    
    # 3. Handle outliers in numeric columns (using IQR method) - skip target column
    for col_info in schema.columns:
        if col_info.dtype in ['number', 'integer'] and col_info.name in df_cleaned.columns and col_info.name in schema.suggested_features and col_info.name != target_col:
            # Ensure column is numeric before calculating quantiles
            try:
                df_cleaned[col_info.name] = pd.to_numeric(df_cleaned[col_info.name], errors='coerce')
                Q1 = df_cleaned[col_info.name].quantile(0.25)
                Q3 = df_cleaned[col_info.name].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outliers = ((df_cleaned[col_info.name] < lower_bound) | (df_cleaned[col_info.name] > upper_bound)).sum()
                if outliers > 0:
                    # Cap outliers at bounds instead of removing
                    df_cleaned[col_info.name] = df_cleaned[col_info.name].clip(lower_bound, upper_bound)
                    report['outliers_handled'] += outliers
                    report['fixes_applied'].append(f"Capped {outliers:,} outliers in '{col_info.name}'")
            except:
                # Skip outlier detection if column can't be converted to numeric
                pass
    
    # 4. Type conversions based on schema (skip target column)
    for col_info in schema.columns:
        if col_info.name in df_cleaned.columns and col_info.name != target_col:
            if col_info.dtype == 'integer':
                # Convert to integer if possible
                try:
                    df_cleaned[col_info.name] = pd.to_numeric(df_cleaned[col_info.name], errors='coerce').astype('Int64')
                    report['type_conversions'] += 1
                except:
                    pass
            elif col_info.dtype == 'number':
                # Ensure numeric
                try:
                    df_cleaned[col_info.name] = pd.to_numeric(df_cleaned[col_info.name], errors='coerce')
                    report['type_conversions'] += 1
                except:
                    pass
    
    report['final_rows'] = len(df_cleaned)
    return df_cleaned, report

def apply_flexible_preprocessing(df: pd.DataFrame, schema: FlexibleSchema) -> pd.DataFrame:
    """Apply preprocessing based on detected schema."""
    df_processed = df.copy()
    
    # Preserve target column before any transformations
    target_col = schema.suggested_target
    if target_col in df_processed.columns:
        target_values = df_processed[target_col].copy()
    
    # Handle dates
    for col_info in schema.columns:
        if col_info.dtype == 'date' and col_info.name in df_processed.columns and col_info.name != target_col:
            df_processed[col_info.name] = pd.to_datetime(df_processed[col_info.name], errors='coerce')
    
    # Handle categorical encoding (one-hot for low cardinality) - skip target
    for col_info in schema.columns:
        if col_info.dtype == 'categorical' and col_info.name in df_processed.columns and col_info.name in schema.suggested_features and col_info.name != target_col:
            if col_info.unique_count <= 10:
                dummies = pd.get_dummies(df_processed[col_info.name], prefix=col_info.name)
                df_processed = pd.concat([df_processed.drop(col_info.name, axis=1), dummies], axis=1)
    
    # Handle missing values - skip target column
    for col_info in schema.columns:
        if col_info.name in df_processed.columns and col_info.nullable and col_info.name != target_col:
            if col_info.dtype in ['number', 'integer']:
                df_processed[col_info.name] = df_processed[col_info.name].fillna(df_processed[col_info.name].median())
            else:
                mode_val = df_processed[col_info.name].mode()[0] if not df_processed[col_info.name].mode().empty else 'unknown'
                df_processed[col_info.name] = df_processed[col_info.name].fillna(mode_val)
    
    # Restore target column if it was lost during preprocessing
    if target_col in df.columns and target_col not in df_processed.columns:
        df_processed[target_col] = target_values
    
    return df_processed

def slm_schema_suggestion(df: pd.DataFrame, sample_size: int = 5, column_meanings: dict | None = None) -> dict:
    column_meanings = {str(k): str(v).strip() for k, v in (column_meanings or {}).items() if str(v).strip()}
    """Use AI to provide intelligent schema suggestions."""
    endpoint = os.getenv('AI_ENDPOINT', '')
    model = os.getenv('AI_MODEL', 'qwen2.5:1.5b')
    
    if not endpoint:
        return None
    
    # Prepare data for AI
    columns_info = []
    for col in df.columns:
        sample_values = df[col].head(sample_size).dropna().astype(str).tolist()
        dtype = str(df[col].dtype)
        unique_count = df[col].nunique()
        missing_count = df[col].isna().sum()
        
        columns_info.append({
            'name': col,
            'dtype': dtype,
            'unique_count': int(unique_count),
            'unique_ratio': round(float(unique_count / max(len(df), 1)), 6),
            'missing_count': int(missing_count),
            'missing_ratio': round(float(missing_count / max(len(df), 1)), 6),
            'is_constant': bool(unique_count <= 1),
            'is_near_unique': bool(unique_count / max(len(df), 1) >= 0.95),
            'sample_values': sample_values[:3]
        })
    
    meanings_context = json.dumps(column_meanings, ensure_ascii=False, indent=2) if column_meanings else "No administrator descriptions were supplied."
    prompt = f"""You are an expert data scientist specializing in financial ML, payment risk analysis, and demand forecasting. Analyze this dataset schema and provide intelligent suggestions.

Administrator column meanings (optional semantic context; do not treat as observed values):
{meanings_context}

Dataset Info:
- Total rows: {len(df)}
- Total columns: {len(df.columns)}

Column Details:
{json.dumps(columns_info, indent=2)}

Your task:
1. Identify the TARGET variable (what we want to predict)
2. Identify FEATURES (input variables for prediction) - BE INCLUSIVE for predictive features
3. Identify ID columns (unique identifiers to exclude from training)
4. Identify DATETIME columns (time-based data) - INCLUDE dates that are useful for prediction
5. Suggest task type: "classification" or "regression"
6. Assign EVERY non-target column to exactly one of feature_columns or excluded_columns
7. Never leave a column unassigned and never put a column in both lists
8. Base exclusions on prediction-time availability and measured statistics, not name matching alone
9. Empty, constant, near-unique identifiers, and outcome/post-event columns must be excluded
10. Pre-outcome dates such as posting, creation, baseline, invoice, and due dates are features unless measured evidence proves leakage

Return strict JSON in this exact format:
{{
    "target_column": "column_name or null",
    "target_reasoning": "why this is the target",
    "feature_columns": ["col1", "col2"],
    "id_columns": ["col1"],
    "excluded_columns": ["col1"],
    "datetime_columns": ["col1"],
    "task_type": "classification or regression",
    "task_reasoning": "why this task type",
    "confidence": 0.85,
    "suggestions": [
        "suggestion 1",
        "suggestion 2"
    ]
}}

CRITICAL DOMAIN KNOWLEDGE FOR FINANCIAL ML:

**PAYMENT/CREDIT RISK TARGETS (look for these):**
- is_late, is_default, is_risk, payment_status, risk_score, churn_flag
- Binary indicators (0/1) for payment outcomes
- Risk classifications (low/medium/high)

**DEMAND FORECAST TARGETS (look for these):**
- units_sold, sales_amount, demand, revenue, forecast
- Numeric continuous values for quantity prediction

**IMPORTANT FEATURES (INCLUDE these - BE INCLUSIVE):**
- Financial amounts: total_open_amount, invoice_amount, payment_amount, balance, units_sold, price
- Dates that matter: due_in_date, posting_date, invoice_date, document_create_date, date, period
- Terms: cust_payment_terms, payment_terms, credit_terms
- Status flags only when they vary and are available at scoring time; constant status fields must be excluded
- Currency: invoice_currency, payment_currency
- Categories: area_business, customer_segment, product_category, store_id, region
- Time-based features: business_year, fiscal_year, quarter, month, week
- Descriptive text: name_customer, product_name (can be useful if not too high cardinality)

**EXCLUDE THESE (DATA LEAKAGE - CRITICAL):**
- clear_date, settlement_date, payment_date (when payment actually occurred)
- Any column that reveals the outcome you're trying to predict
- Columns with names like "result", "outcome", "final_status", "actual" vs "predicted"

**ID COLUMNS (exclude from training):**
- Exclude only true row/invoice identifiers. A low-cardinality business_code is a categorical feature, not an ID
- Exception: If they have predictive patterns (like area_business_code), keep as features

**BE INCLUSIVE WITH FEATURES:**
- Include most columns as features unless they're clearly IDs or data leakage
- Numeric columns are generally useful features
- Date columns (except leakage dates) can be engineered into useful features
- Categorical columns with reasonable cardinality are valuable features
- When in doubt, INCLUDE as feature rather than exclude

**PRIORITY:**
1. Financial and behavioral features over simple identifiers
2. Dates that inform prediction (due dates) over dates that reveal outcomes (settlement dates)
3. Include columns that would be available at prediction time in production
4. Inclusive approach: prefer false positives (include non-useful features) over false negatives (exclude useful features)"""

    payload = {
        'model': model,
        'stream': False,
        'prompt': prompt
    }
    
    try:
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode(),
            headers={'Content-Type': 'application/json'}
        )
        raw = json.loads(urllib.request.urlopen(req, timeout=30).read())
        response = json.loads(raw['response'])
        response['generator'] = 'local AI'
        return response
    except Exception as e:
        print(f"AI schema suggestion failed: {e}")
        return None

def enhance_schema_with_slm(df: pd.DataFrame, rule_based_schema: FlexibleSchema, force_slm: bool = False, column_meanings: dict | None = None) -> FlexibleSchema:
    column_meanings = {str(k): str(v).strip() for k, v in (column_meanings or {}).items() if str(v).strip()}
    """Enhance rule-based schema with AI suggestions, using caching for efficiency."""
    # Create fingerprint of the dataframe structure
    fingerprint = get_schema_fingerprint(df)
    
    # Check if we have a cached schema for this structure
    if not force_slm:
        cached_schema = get_cached_schema(fingerprint)
        if cached_schema:
            # Reconstruct schema from cache
            enhanced_columns = []
            for col_data in cached_schema['columns']:
                col_info = ColumnInfo(**col_data)
                enhanced_columns.append(col_info)
            
            enhanced_schema = FlexibleSchema(
                columns=enhanced_columns,
                suggested_target=cached_schema['suggested_target'],
                suggested_features=cached_schema['suggested_features'],
                suggested_ids=cached_schema['suggested_ids'],
                task_type=cached_schema['task_type'],
                slm_suggestions=cached_schema.get('slm_suggestions'),
                slm_reasoning=cached_schema.get('slm_reasoning')
            )
            enhanced_schema.from_cache = True
            return govern_schema_roles(df, enhanced_schema)
    
    # No cache available or forced refresh - use AI
    slm_result = slm_schema_suggestion(df, column_meanings=column_meanings)
    
    if not slm_result:
        return govern_schema_roles(df, rule_based_schema)  # Governed deterministic fallback
    
    # Create enhanced schema combining both approaches
    enhanced_columns = []
    
    # Create a map of AI suggestions
    slm_target = slm_result.get('target_column')
    slm_targets = {slm_target} if slm_target else set()
    slm_features = set(slm_result.get('feature_columns', []))
    slm_ids = set(slm_result.get('id_columns', []))
    slm_datetimes = set(slm_result.get('datetime_columns', []))
    
    for col_info in rule_based_schema.columns:
        enhanced_col = col_info
        
        # Apply AI suggestions with higher confidence
        if col_info.name in slm_targets:
            enhanced_col.suggested_role = 'target'
            enhanced_col.confidence = max(enhanced_col.confidence, 0.9)
        elif col_info.name in slm_ids:
            enhanced_col.suggested_role = 'id'
            enhanced_col.confidence = max(enhanced_col.confidence, 0.9)
        elif col_info.name in slm_datetimes:
            enhanced_col.suggested_role = 'datetime'
            enhanced_col.confidence = max(enhanced_col.confidence, 0.85)
        elif col_info.name in slm_features:
            enhanced_col.suggested_role = 'feature'
            enhanced_col.confidence = max(enhanced_col.confidence, 0.8)
        
        enhanced_columns.append(enhanced_col)
    
    # Update task type based on AI suggestion
    enhanced_task_type = slm_result.get('task_type', rule_based_schema.task_type)
    
    # Update suggested target
    enhanced_target = slm_result.get('target_column') if slm_result.get('target_column') else rule_based_schema.suggested_target
    
    # Update features based on AI
    enhanced_features = [c.name for c in enhanced_columns if c.suggested_role == 'feature']
    if not enhanced_features:
        enhanced_features = slm_result.get('feature_columns', rule_based_schema.suggested_features)
    
    # Update IDs
    enhanced_ids = [c.name for c in enhanced_columns if c.suggested_role == 'id']
    if not enhanced_ids:
        enhanced_ids = slm_result.get('id_columns', rule_based_schema.suggested_ids)
    
    enhanced_schema = FlexibleSchema(
        columns=enhanced_columns,
        suggested_target=enhanced_target,
        suggested_features=enhanced_features,
        suggested_ids=enhanced_ids,
        task_type=enhanced_task_type,
        slm_suggestions=slm_result.get('suggestions', []),
        slm_reasoning={
            'target': slm_result.get('target_reasoning'),
            'task': slm_result.get('task_reasoning'),
            'confidence': slm_result.get('confidence', 0)
        }
    )
    enhanced_schema.from_cache = False
    
    # Cache the enhanced schema for future use
    cache_data = {
        'columns': [asdict(col) for col in enhanced_columns],
        'suggested_target': enhanced_schema.suggested_target,
        'suggested_features': enhanced_schema.suggested_features,
        'suggested_ids': enhanced_schema.suggested_ids,
        'task_type': enhanced_schema.task_type,
        'slm_suggestions': enhanced_schema.slm_suggestions,
        'slm_reasoning': enhanced_schema.slm_reasoning,
        'fingerprint': fingerprint,
        'timestamp': pd.Timestamp.now().isoformat()
    }
    cache_schema(fingerprint, cache_data)
    
    # Update template when schema changes (if not from cache)
    if not enhanced_schema.from_cache:
        update_template_on_schema_change(df, enhanced_schema, fingerprint)
        
        # Save schema version for evolution tracking
        save_schema_version(enhanced_schema, fingerprint, 'credit')
    
    return enhanced_schema

def enhance_schema_with_slm_forecast(df: pd.DataFrame, rule_based_schema: FlexibleSchema, force_slm: bool = False, column_meanings: dict | None = None) -> FlexibleSchema:
    column_meanings = {str(k): str(v).strip() for k, v in (column_meanings or {}).items() if str(v).strip()}
    """Enhance rule-based schema with AI suggestions for forecast (separate function to avoid conflicts)."""
    # Create fingerprint of the dataframe structure
    fingerprint = get_schema_fingerprint(df)
    
    # Check if we have a cached schema for this structure
    if not force_slm:
        cached_schema = get_cached_schema(fingerprint)
        if cached_schema:
            # Reconstruct schema from cache
            enhanced_columns = []
            for col_data in cached_schema['columns']:
                col_info = ColumnInfo(**col_data)
                enhanced_columns.append(col_info)
            
            enhanced_schema = FlexibleSchema(
                columns=enhanced_columns,
                suggested_target=cached_schema['suggested_target'],
                suggested_features=cached_schema['suggested_features'],
                suggested_ids=cached_schema['suggested_ids'],
                task_type=cached_schema['task_type'],
                slm_suggestions=cached_schema.get('slm_suggestions'),
                slm_reasoning=cached_schema.get('slm_reasoning')
            )
            enhanced_schema.from_cache = True
            return govern_schema_roles(df, enhanced_schema)
    
    # No cache available or forced refresh - use AI
    slm_result = slm_schema_suggestion(df, column_meanings=column_meanings)
    
    if not slm_result:
        return govern_schema_roles(df, rule_based_schema)  # Governed deterministic fallback
    
    # Create enhanced schema combining both approaches
    enhanced_columns = []
    
    # Create a map of AI suggestions
    slm_target = slm_result.get('target_column')
    slm_targets = {slm_target} if slm_target else set()
    slm_features = set(slm_result.get('feature_columns', []))
    slm_ids = set(slm_result.get('id_columns', []))
    slm_datetimes = set(slm_result.get('datetime_columns', []))
    
    for col_info in rule_based_schema.columns:
        enhanced_col = col_info
        
        # Apply AI suggestions with higher confidence
        if col_info.name in slm_targets:
            enhanced_col.suggested_role = 'target'
            enhanced_col.confidence = max(enhanced_col.confidence, 0.9)
        elif col_info.name in slm_ids:
            enhanced_col.suggested_role = 'id'
            enhanced_col.confidence = max(enhanced_col.confidence, 0.9)
        elif col_info.name in slm_datetimes:
            enhanced_col.suggested_role = 'datetime'
            enhanced_col.confidence = max(enhanced_col.confidence, 0.85)
        elif col_info.name in slm_features:
            enhanced_col.suggested_role = 'feature'
            enhanced_col.confidence = max(enhanced_col.confidence, 0.8)
        
        enhanced_columns.append(enhanced_col)
    
    # Update task type based on AI suggestion
    enhanced_task_type = slm_result.get('task_type', rule_based_schema.task_type)
    
    # Update suggested target
    enhanced_target = slm_result.get('target_column') if slm_result.get('target_column') else rule_based_schema.suggested_target
    
    # Update features based on AI
    enhanced_features = [c.name for c in enhanced_columns if c.suggested_role == 'feature']
    if not enhanced_features:
        enhanced_features = slm_result.get('feature_columns', rule_based_schema.suggested_features)
    
    # Update IDs
    enhanced_ids = [c.name for c in enhanced_columns if c.suggested_role == 'id']
    if not enhanced_ids:
        enhanced_ids = slm_result.get('id_columns', rule_based_schema.suggested_ids)
    
    enhanced_schema = FlexibleSchema(
        columns=enhanced_columns,
        suggested_target=enhanced_target,
        suggested_features=enhanced_features,
        suggested_ids=enhanced_ids,
        task_type=enhanced_task_type,
        slm_suggestions=slm_result.get('suggestions', []),
        slm_reasoning={
            'target': slm_result.get('target_reasoning'),
            'task': slm_result.get('task_reasoning'),
            'confidence': slm_result.get('confidence', 0)
        }
    )
    enhanced_schema.from_cache = False
    
    # Cache the enhanced schema for future use
    cache_data = {
        'columns': [asdict(col) for col in enhanced_columns],
        'suggested_target': enhanced_schema.suggested_target,
        'suggested_features': enhanced_schema.suggested_features,
        'suggested_ids': enhanced_schema.suggested_ids,
        'task_type': enhanced_schema.task_type,
        'slm_suggestions': enhanced_schema.slm_suggestions,
        'slm_reasoning': enhanced_schema.slm_reasoning,
        'fingerprint': fingerprint,
        'timestamp': pd.Timestamp.now().isoformat()
    }
    cache_schema(fingerprint, cache_data)
    
    # Update template when schema changes (if not from cache)
    if not enhanced_schema.from_cache:
        update_template_on_schema_change(df, enhanced_schema, fingerprint)
        
        # Save schema version for evolution tracking
        save_schema_version(enhanced_schema, fingerprint, 'forecast')
    
    return enhanced_schema
