import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("SICHE_DB_PATH", str(Path(tempfile.gettempdir()) / "siche-pytest.db"))

import pytest  # noqa: E402

from app.store import clear  # noqa: E402


@pytest.fixture(autouse=True)
def _clean_store():
    clear()
    yield
    clear()
