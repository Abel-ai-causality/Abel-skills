from fastapi.testclient import TestClient

from __PACKAGE_NAME__.app import app


CAP_HEADERS = __TEST_CAP_HEADERS__
GRAPH_CONTEXT = __TEST_GRAPH_CONTEXT__
EXPECT_OBSERVE_PREDICT = __TEST_EXPECT_OBSERVE_PREDICT__
EXPECT_INTERVENE_DO = __TEST_EXPECT_INTERVENE_DO__


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
    assert ("intervene.do" in body["supported_verbs"]["core"]) is EXPECT_INTERVENE_DO


def test_meta_methods_lists_level2_verbs() -> None:
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
    assert "graph.paths" in methods
    assert ("observe.predict" in methods) is EXPECT_OBSERVE_PREDICT
    assert ("intervene.do" in methods) is EXPECT_INTERVENE_DO


[[IF_INCLUDE_INTERVENTION]]
def test_intervene_do_returns_semantic_fields() -> None:
    response = client.post(
        "/cap",
        json=build_payload(
            {
                "cap_version": "0.2.2",
                "request_id": "req-intervene",
                "verb": "intervene.do",
                "params": {
                    "treatment_node": "marketing_spend",
                    "treatment_value": 2.0,
                    "outcome_node": "revenue",
                },
            }
        ),
        headers=CAP_HEADERS or None,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["result"]["effect"] == 2.4
    assert body["result"]["reasoning_mode"] == "scm_simulation"
    assert body["result"]["identification_status"] == "not_formally_identified"
[[END_IF_INCLUDE_INTERVENTION]]
