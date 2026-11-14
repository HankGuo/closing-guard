import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))


def pytest_collection_modifyitems(config, items):
    if os.getenv("CG_E2E") == "1":
        return
    skip_e2e = pytest.mark.skip(reason="set CG_E2E=1 and start the local model servers to run real e2e tests")
    for item in items:
        if "e2e" in item.keywords:
            item.add_marker(skip_e2e)
