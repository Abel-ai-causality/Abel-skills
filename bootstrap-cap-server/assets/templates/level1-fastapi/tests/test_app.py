from fastapi.testclient import TestClient

from __PACKAGE_NAME__.app import app


CAP_HEADERS = __TEST_CAP_HEADERS__
GRAPH_CONTEXT = __TEST_GRAPH_CONTEXT__
EXPECT_OBSERVE_PREDICT = __TEST_EXPECT_OBSERVE_PREDICT__


def build_payload(payload: dict) -> dict:
    body = dict(payload)
    if GRAPH_CONTEXT is not None:
        body["context"] = {"graph_ref": GRAPH_CONTEXT}
    return body


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_well_known_capability_card() -> None:
    response = client.get("/.well-known/cap.json")

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "__SERVER_TITLE__"
    assert body["conformance_level"] == __CONFORMANCE_LEVEL__
    assert ("observe.predict" in body["supported_verbs"]["core"]) is EXPECT_OBSERVE_PREDICT


def test_meta_methods_lists_core_verbs() -> None:
    response = client.post(
        "/cap",
        json=build_payload(
            {
                "cap_version": "0.2.2",
                "request_id": "req-methods",
                "verb": "meta.methods",
                "params": {"detail": "compact"},
            }
        ),
        headers=CAP_HEADERS or None,
    )

    assert response.status_code == 200
    methods = {item["verb"] for item in response.json()["result"]["methods"]}
    assert "meta.capabilities" in methods
    assert "graph.neighbors" in methods
    assert ("observe.predict" in methods) is EXPECT_OBSERVE_PREDICT
[[IF_INCLUDE_PATHS]]
    assert "graph.paths" in methods
[[END_IF_INCLUDE_PATHS]]


[[IF_INCLUDE_PREDICTOR]]
def test_observe_predict_returns_prediction() -> None:
    response = client.post(
        "/cap",
        json=build_payload(
            {
                "cap_version": "0.2.2",
                "request_id": "req-observe",
                "verb": "observe.predict",
                "params": {"target_node": "revenue"},
            }
        ),
        headers=CAP_HEADERS or None,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["result"]["target_node"] == "revenue"
    assert body["result"]["drivers"] == ["pipeline", "win_rate"]
[[END_IF_INCLUDE_PREDICTOR]]


[[IF_INCLUDE_PATHS]]
def test_graph_paths_returns_structural_path() -> None:
    response = client.post(
        "/cap",
        json=build_payload(
            {
                "cap_version": "0.2.2",
                "request_id": "req-paths",
                "verb": "graph.paths",
                "params": {
                    "source_node_id": "marketing_spend",
                    "target_node_id": "revenue",
                    "max_paths": 3,
                },
            }
        ),
        headers=CAP_HEADERS or None,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["result"]["connected"] is True
    assert body["result"]["path_count"] == 1
[[END_IF_INCLUDE_PATHS]]
