#!/usr/bin/env python3
from __future__ import annotations

import sys
import os
from pathlib import Path


def main() -> None:
    skill_dir = Path(__file__).resolve().parent
    os.environ.setdefault("GRAPHWIKI_SKILL_DIR", str(skill_dir))
    bundled_tool = skill_dir / "tool"
    sys.path.insert(0, str(bundled_tool))

    from graphwiki.cli import main as cli_main

    cli_main()


if __name__ == "__main__":
    main()
