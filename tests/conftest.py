"""pytest English text fixtures

- English text backend/ English text sys.pathEnglish text main.py English text
- English text DB_PATH English text CONFIG_FILE_PATHEnglish text choice.db English text ~/.choice/config.json
"""

import sys
from pathlib import Path

# English text backend/ English text sys.pathEnglish text backend/main.py English text 22 English text
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest  # noqa: E402

import config as config_mod  # noqa: E402
import db  # noqa: E402


@pytest.fixture(autouse=True)
def isolate_paths(tmp_path, monkeypatch):
    """Give every test an isolated PostgreSQL workspace and config file."""
    monkeypatch.setattr(config_mod, "CONFIG_FILE_PATH", tmp_path / "config.json")
    db.init_db()
    workspace_id = "test_" + tmp_path.name
    token = db.set_workspace_id(workspace_id)
    try:
        yield
    finally:
        db.reset_workspace_id(token)
