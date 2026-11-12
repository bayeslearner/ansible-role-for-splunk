#!/usr/bin/env python3
"""ansible-role-for-splunk's Board seed: the shared kit in the spec-driven-dev skill, configured by
docs/board/board.json. The Board is the Claude Doc shape:
  python3 docs/board/seed.py doc --out .build/doc-board [--date YYYY-MM-DD]
Other arguments go to the kit's seed.py (the HTML page's store), e.g.
  python3 docs/board/seed.py --out .build/board
"""
import os
import sys
from pathlib import Path

board = Path(os.environ.get("BOARD_KIT", Path.home() / ".claude/skills/spec-driven-dev/board/seed.py")).parent
os.chdir(Path(__file__).resolve().parents[2])
args = sys.argv[1:]
# `doc` selects the doc-shape seed; everything after it is that script's own arguments
script, args = (board / "seed_doc.py", args[1:]) if args[:1] == ["doc"] else (board / "seed.py", args)
os.execv(sys.executable, [sys.executable, str(script), *args])
