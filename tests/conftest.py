from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE_SRC = ROOT / "services" / "document-engine" / "src"
if str(ENGINE_SRC) not in sys.path:
    sys.path.insert(0, str(ENGINE_SRC))
if not (ROOT / "tests" / "fixtures" / "sample.pdf").exists():
    from generate_fixtures import make_fixtures
    make_fixtures()
