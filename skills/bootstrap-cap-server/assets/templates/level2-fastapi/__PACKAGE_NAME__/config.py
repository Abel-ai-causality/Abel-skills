from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import __version__


APP_NAME = "__SERVER_TITLE__"
GRAPH_VERSION = "__GRAPH_VERSION__"
RUNTIME_SHAPE = "__RUNTIME_SHAPE__"
GRAPH_DATA_DIR = Path(__file__).resolve().parent / "data"
JSON_GRAPH_NODES_PATH = GRAPH_DATA_DIR / "nodes.json"
JSON_GRAPH_EDGES_PATH = GRAPH_DATA_DIR / "edges.json"
MAX_PATH_SEARCH_DEPTH = 4
MAX_PATH_SEARCH_EXPANSIONS = 500


@dataclass(frozen=True)
class ServiceSettings:
    app_name: str = APP_NAME
    app_version: str = __version__
