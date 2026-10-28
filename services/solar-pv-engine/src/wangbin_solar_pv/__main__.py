"""python -m wangbin_solar_pv entry, guarded for Windows parser workers."""
from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
