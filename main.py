"""ServerDeck entry point."""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ui.main_window import MainWindow  # noqa: E402


def main() -> None:
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
