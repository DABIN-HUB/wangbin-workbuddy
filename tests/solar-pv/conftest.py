"""Local-only Phase 2 tests. All generated project/document data is SYNTHETIC."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
for source in (ROOT / "services/solar-pv-engine/src", ROOT / "services/document-engine/src"):
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))
