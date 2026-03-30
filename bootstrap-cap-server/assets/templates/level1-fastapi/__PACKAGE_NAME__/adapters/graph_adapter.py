from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Neighbor:
    node_id: str
    roles: list[str]


class GraphAdapter:
    def __init__(self) -> None:
[[IF_INCLUDE_PREDICTOR]]
        self._predictions = {
            "revenue": {"prediction": 125.4, "drivers": ["pipeline", "win_rate"]},
            "pipeline": {"prediction": 82.0, "drivers": ["marketing_spend"]},
        }
[[END_IF_INCLUDE_PREDICTOR]]
        self._neighbors = {
            ("revenue", "parents"): [
                Neighbor(node_id="pipeline", roles=["parent"]),
                Neighbor(node_id="win_rate", roles=["parent"]),
            ],
            ("revenue", "children"): [],
            ("pipeline", "parents"): [
                Neighbor(node_id="marketing_spend", roles=["parent"]),
            ],
            ("pipeline", "children"): [
                Neighbor(node_id="revenue", roles=["child"]),
            ],
        }
        self._blankets = {
            "revenue": [
                Neighbor(node_id="pipeline", roles=["parent"]),
                Neighbor(node_id="win_rate", roles=["parent"]),
                Neighbor(node_id="marketing_spend", roles=["spouse"]),
            ],
            "pipeline": [
                Neighbor(node_id="marketing_spend", roles=["parent"]),
                Neighbor(node_id="revenue", roles=["child"]),
                Neighbor(node_id="win_rate", roles=["spouse"]),
            ],
        }
[[IF_INCLUDE_PATHS]]
        self._paths = {
            ("marketing_spend", "revenue"): [
                {
                    "distance": 2,
                    "nodes": [
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
                            "node_id": "revenue",
                            "node_name": "Revenue",
                            "node_type": "outcome_metric",
                            "domain": "finance",
                        },
                    ],
                    "edges": [
                        {
                            "from_node_id": "marketing_spend",
                            "to_node_id": "pipeline",
                            "edge_type": "directed_causal_link",
                        },
                        {
                            "from_node_id": "pipeline",
                            "to_node_id": "revenue",
                            "edge_type": "directed_causal_link",
                        },
                    ],
                }
            ]
        }
[[END_IF_INCLUDE_PATHS]]

    def neighbors(self, node_id: str, scope: str, max_neighbors: int) -> tuple[list[Neighbor], int]:
        items = list(self._neighbors.get((node_id, scope), []))
        total = len(items)
        return items[:max_neighbors], total

    def markov_blanket(self, node_id: str, max_neighbors: int) -> tuple[list[Neighbor], int]:
        items = list(self._blankets.get(node_id, []))
        total = len(items)
        return items[:max_neighbors], total

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
        items = list(self._paths.get((source_node_id, target_node_id), []))
        total = len(items)
        return items[:max_paths], total
[[END_IF_INCLUDE_PATHS]]
