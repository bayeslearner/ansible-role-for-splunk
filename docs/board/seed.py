#!/usr/bin/env python3
"""ansible-role-for-splunk's Board seed: the shared kit in the spec-driven-dev skill, configured by
docs/board/board.json. Same arguments as the kit's seed.py, e.g.
  python3 docs/board/seed.py --out .build/board [--versions versions.json] [--no-live]
  python3 docs/board/seed.py page --out board/board.html
"""
import os
import sys
from pathlib import Path

kit = Path(os.environ.get("BOARD_KIT", Path.home() / ".claude/skills/spec-driven-dev/board/seed.py"))
os.chdir(Path(__file__).resolve().parents[2])
os.execv(sys.executable, [sys.executable, str(kit), *sys.argv[1:]])
