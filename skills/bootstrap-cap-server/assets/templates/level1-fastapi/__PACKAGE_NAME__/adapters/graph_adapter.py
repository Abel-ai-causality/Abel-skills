from __future__ import annotations

import json
from collections import defaultdict, deque
from dataclasses import dataclass

from ..config import (
    JSON_GRAPH_EDGES_PATH,
    JSON_GRAPH_NODES_PATH,
    MAX_PATH_SEARCH_DEPTH,
    MAX_PATH_SEARCH_EXPANSIONS,
    RUNTIME_SHAPE,
)


@dataclass(frozen=True)
class Neighbor:
    node_id: str
    roles: list[str]


class PathSearchLimitExceeded(RuntimeError):
    pass


class GraphAdapter:
    def __init__(self) -> None:
        self._node_details: dict[str, dict[str, object]] = {}
        self._parents: dict[str, list[str]] = defaultdict(list)
        self._children: dict[str, list[str]] = defaultdict(list)
        self._edge_details: dict[tuple[str, str], dict[str, object]] = {}
[[IF_INCLUDE_PREDICTOR]]
        self._predictions = {
            "revenue": {"prediction": 125.4, "drivers": ["pipeline", "win_rate"]},
            "pipeline": {"prediction": 82.0, "drivers": ["marketing_spend"]},
        }
[[END_IF_INCLUDE_PREDICTOR]]
        if RUNTIME_SHAPE == "json-graph":
            self._load_json_graph()
        else:
            self._load_demo_graph()

    def _load_demo_graph(self) -> None:
        nodes = [
            {
                "node_id": "marketing_spend",
                "node_name": "Marketing Spend",
                "node_type": "input_metric",
                "domain": "go_to_market",
            },
            {
                "node_id": "pipeline",
                "node_name": "Pipeline",
                "node_type": "intermediate_metric",
                "domain": "sales",
            },
            {
                "node_id": "win_rate",
                "node_name": "Win Rate",
                "node_type": "intermediate_metric",
                "domain": "sales",
            },
            {
                "node_id": "revenue",
                "node_name": "Revenue",
                "node_type": "outcome_metric",
                "domain": "finance",
            },
        ]
        edges = [
            {"source_node_id": "marketing_spend", "target_node_id": "pipeline"},
            {"source_node_id": "pipeline", "target_node_id": "revenue"},
            {"source_node_id": "win_rate", "target_node_id": "revenue"},
        ]
        self._load_graph_records(nodes, edges)

    def _load_json_graph(self) -> None:
        nodes = json.loads(JSON_GRAPH_NODES_PATH.read_text(encoding="utf-8"))
        edges = json.loads(JSON_GRAPH_EDGES_PATH.read_text(encoding="utf-8"))
        self._load_graph_records(nodes, edges)

    def _load_graph_records(self, nodes: list[dict], edges: list[dict]) -> None:
        for node in nodes:
            node_id = str(node["node_id"])
            self._node_details[node_id] = {
                "node_id": node_id,
                "node_name": str(node.get("node_name") or node_id),
                "node_type": str(node.get("node_type") or "generic_node"),
                "domain": node.get("domain"),
            }
        for edge in edges:
            source = str(edge["source_node_id"])
            target = str(edge["target_node_id"])
            if source not in self._node_details or target not in self._node_details:
                raise ValueError(f"Edge references unknown node: {source!r} -> {target!r}")
            self._children[source].append(target)
            self._parents[target].append(source)
            self._edge_details[(source, target)] = {
                "edge_type": "directed_causal_link",
                "weight": edge.get("weight"),
                "time_lag": edge.get("time_lag"),
            }

    def neighbors(self, node_id: str, scope: str, max_neighbors: int) -> tuple[list[Neighbor], int]:
        items: list[Neighbor] = []
        if scope in {"parents", "both"}:
            items.extend(Neighbor(node_id=parent, roles=["parent"]) for parent in self._parents.get(node_id, []))
        if scope in {"children", "both"}:
            items.extend(Neighbor(node_id=child, roles=["child"]) for child in self._children.get(node_id, []))
        total = len(items)
        return items[:max_neighbors], total

    def markov_blanket(self, node_id: str, max_neighbors: int) -> tuple[list[Neighbor], int]:
        blanket: list[Neighbor] = []
        seen: set[tuple[str, str]] = set()
        for parent in self._parents.get(node_id, []):
            key = (parent, "parent")
            if key not in seen:
                blanket.append(Neighbor(node_id=parent, roles=["parent"]))
                seen.add(key)
        children = self._children.get(node_id, [])
        for child in children:
            key = (child, "child")
            if key not in seen:
                blanket.append(Neighbor(node_id=child, roles=["child"]))
                seen.add(key)
            for spouse in self._parents.get(child, []):
                if spouse == node_id:
                    continue
                spouse_key = (spouse, "spouse")
                if spouse_key not in seen:
                    blanket.append(Neighbor(node_id=spouse, roles=["spouse"]))
                    seen.add(spouse_key)
        total = len(blanket)
        return blanket[:max_neighbors], total

[[IF_INCLUDE_PREDICTOR]]
    def predict(self, target_node: str) -> dict[str, object]:
        return dict(self._predictions.get(target_node, {"prediction": 0.0, "drivers": []}))
[[END_IF_INCLUDE_PREDICTOR]]
[[IF_INCLUDE_PREDICTOR_STUB]]
    def predict(self, target_node: str) -> dict[str, object]:
        raise NotImplementedError(
            f"TODO: wire an observational predictor for target_node={target_node!r} before mounting observe.predict."
        )
[[END_IF_INCLUDE_PREDICTOR_STUB]]
[[IF_INCLUDE_PATHS]]

    def paths(self, source_node_id: str, target_node_id: str, max_paths: int) -> tuple[list[dict], int]:
        if source_node_id not in self._node_details or target_node_id not in self._node_details:
            return [], 0

        queue: deque[list[str]] = deque([[source_node_id]])
        shortest_distance: int | None = None
        found_paths: list[list[str]] = []
        expansions = 0

        while queue:
            path = queue.popleft()
            current = path[-1]
            distance = len(path) - 1
            if shortest_distance is not None and distance > shortest_distance:
                continue
            if distance >= MAX_PATH_SEARCH_DEPTH:
                continue

            for child in self._children.get(current, []):
                if child in path:
                    continue
                next_path = path + [child]
                next_distance = len(next_path) - 1
                if shortest_distance is not None and next_distance > shortest_distance:
                    continue
                if next_distance > MAX_PATH_SEARCH_DEPTH:
                    continue
                expansions += 1
                if expansions > MAX_PATH_SEARCH_EXPANSIONS:
                    raise PathSearchLimitExceeded(
                        "graph.paths exceeded the configured expansion limit for this scaffold."
                    )
                if child == target_node_id:
                    shortest_distance = next_distance
                    found_paths.append(next_path)
                else:
                    queue.append(next_path)

        payloads = [self._build_path_payload(path) for path in found_paths[:max_paths]]
        return payloads, len(found_paths)

    def _build_path_payload(self, path: list[str]) -> dict[str, object]:
        nodes = [self._node_payload(node_id) for node_id in path]
        edges = [
            {
                "from_node_id": source,
                "to_node_id": target,
                "edge_type": self._edge_details[(source, target)]["edge_type"],
            }
            for source, target in zip(path, path[1:])
        ]
        return {
            "distance": len(path) - 1,
            "nodes": nodes,
            "edges": edges,
        }

    def _node_payload(self, node_id: str) -> dict[str, object]:
        details = self._node_details[node_id]
        return {
            "node_id": details["node_id"],
            "node_name": details["node_name"],
            "node_type": details["node_type"],
            "domain": details["domain"],
        }
[[END_IF_INCLUDE_PATHS]]
