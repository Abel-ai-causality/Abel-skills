from __future__ import annotations

from dataclasses import dataclass

from . import __version__


APP_NAME = "__SERVER_TITLE__"
GRAPH_ID = "__GRAPH_ID__"
GRAPH_VERSION = "__GRAPH_VERSION__"


@dataclass(frozen=True)
class ServiceSettings:
    app_name: str = APP_NAME
    app_version: str = __version__
