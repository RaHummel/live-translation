import tomllib
from pathlib import Path


def _load_pyproject(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        with path.open('rb') as fh:
            return tomllib.load(fh)

    except Exception:
        return None


def get_app_version() -> str:
    """Read version from pyproject.toml [project].version.

    Returns 'unknown' if not found or on error.
    """
    try:
        # project root is two parents above src/utils
        project_root = Path(__file__).resolve().parents[2]
        pyproject = project_root / 'pyproject.toml'
        data = _load_pyproject(pyproject)
        if not data:
            return 'unknown'
        proj = data.get('project')
        if isinstance(proj, dict):
            v = proj.get('version')
            if v:
                return str(v)
        return 'unknown'
    except Exception:
        return 'unknown'
