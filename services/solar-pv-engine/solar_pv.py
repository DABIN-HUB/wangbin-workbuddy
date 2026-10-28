"""Source checkout entrypoint; no installation or working-directory assumption."""
from pathlib import Path
import sys

if __name__ == "__main__":
    service = Path(__file__).resolve().parent
    for source in (service / "src", service.parent / "document-engine/src"):
        sys.path.insert(0, str(source))
    from wangbin_solar_pv.cli import main
    raise SystemExit(main())
