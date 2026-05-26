"""ServerDeck entry point."""

from __future__ import annotations

import os
import sys
import traceback

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def main() -> None:
    try:
        from core.data_store import DataStoreError
        from ui.main_window import MainWindow
    except ImportError as exc:
        _fatal(f"ServerDeck failed to load required modules.\n\n{exc}")
        return

    try:
        app = MainWindow()
    except DataStoreError as exc:
        _fatal(
            "ServerDeck could not initialize its local database.\n\n"
            f"{exc}\n\n"
            "The app will recreate serverdeck.db automatically when possible. "
            "If the problem persists, delete serverdeck.db and restart.",
            show_traceback=False,
        )
        return
    except Exception as exc:
        _fatal(f"ServerDeck encountered an unexpected startup error.\n\n{exc}")
        return

    app.mainloop()


def _fatal(message: str, *, show_traceback: bool = True) -> None:
    print(message, file=sys.stderr)
    if show_traceback:
        traceback.print_exc()
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("ServerDeck — Startup Error", message)
        root.destroy()
    except Exception:
        pass
    sys.exit(1)


if __name__ == "__main__":
    main()
