from pathlib import Path

def test_streamlit_upload_limit_is_500_mb():
    config=(Path(__file__).parents[1]/'.streamlit/config.toml').read_text(encoding='utf-8')
    assert 'maxUploadSize = 500' in config
    assert 'maxMessageSize = 500' in config

def test_every_active_uploader_uses_validated_wrapper():
    source=(Path(__file__).parents[1]/'src/ui/app.py').read_text(encoding='utf-8')
    assert 'MAX_UPLOAD_MB = 500' in source
    assert source.count('st.file_uploader(') == 1
    assert source.count('validated_upload(') >= 5
    assert 'stFileUploaderDropzoneInstructions' in source
