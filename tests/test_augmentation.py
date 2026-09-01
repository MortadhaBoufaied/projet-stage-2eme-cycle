from src.smoke_check import credit_data
from src.services.augmentation import augment_credit_training_data
from src.services.training import compare_credit_augmentation

def test_augmentation_does_not_change_original_or_target_contract():
    data=credit_data(240);aug,meta=augment_credit_training_data(data,.75,.02)
    assert len(aug)>=len(data) and meta['synthetic_rows']>=0
    assert set(aug.columns)==set(data.columns)

def test_same_holdout_comparison_runs():
    result=compare_credit_augmentation(credit_data(240),model_type='xgboost',target_ratio=.7,jitter=.02)
    assert result['recommended'] in {'baseline','augmented'}
    assert result['baseline_metrics']['n_test']==result['augmented_metrics']['n_test']
