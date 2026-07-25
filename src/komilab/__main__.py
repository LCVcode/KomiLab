from __future__ import annotations

import os


def main() -> None:
    os.environ.setdefault("GDK_BACKEND", "x11,wayland")
    from komilab.ui.launcher import run

    run()


if __name__ == "__main__":
    main()
