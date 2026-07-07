"""
main.py

Run modes:
  python main.py          -> Terminal UI (default)
  python main.py --gui    -> GUI [TO-DO]
"""

import sys
from pathlib import Path

from settings import load_settings


def main() -> None:
    folder   = Path(sys.argv[0]).resolve().parent
    settings = load_settings(folder)

    if "--gui" in sys.argv:
        from ui.gui import run_app
    else:
        from ui.terminal import run_app

    run_app(folder, settings)


if __name__ == "__main__":
    main()