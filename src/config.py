from pathlib import Path
import os
ROOT=Path(__file__).resolve().parents[1]

def _load_env(env_path=None, override=False):
    """Load a .env file into os.environ.

    Parameters
    ----------
    env_path : Path | str | None
        Path to the .env file.  Defaults to ``ROOT / '.env'``.
    override : bool
        If *True*, overwrite existing environment variables.

    Returns
    -------
    dict
        Mapping of every key/value pair that was read from the file.
    """
    env_path = Path(env_path) if env_path is not None else ROOT / '.env'
    loaded = {}
    if not env_path.exists():
        return loaded
    raw = env_path.read_text(encoding='utf-8-sig')  # handles BOM
    for line in raw.splitlines():
        if line.strip() and not line.lstrip().startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            loaded[k] = v
            if override:
                os.environ[k] = v
            else:
                os.environ.setdefault(k, v)
    return loaded

_load_env()  # auto-load on import, same as before

ARTIFACTS=ROOT/'artifacts'; ARTIFACTS.mkdir(exist_ok=True)
ARTIFACTS_DIR=ARTIFACTS
PROJECT_ROOT=ROOT
DB=ROOT/'data'/'platform.db'
RANDOM_STATE=42
MAX_UPLOAD_MB=int(os.getenv('MAX_UPLOAD_MB','500'))
