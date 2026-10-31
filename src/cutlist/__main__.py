"""Allow `python -m cutlist`."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
