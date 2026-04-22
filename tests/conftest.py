from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
STRATEGY_DISCOVERY_SKILL_ROOT = REPO_ROOT / "skills" / "abel-strategy-discovery"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

if str(STRATEGY_DISCOVERY_SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(STRATEGY_DISCOVERY_SKILL_ROOT))
