"""FounderOS route smoke tests for the graph-first product contract."""

from fastapi.testclient import TestClient

import main


def test_public_landing_route_serves_founderos_intro():
    with TestClient(main.app) as client:
        response = client.get("/")
    assert response.status_code == 200
    assert "FounderOS" in response.text
    assert 'id="seedForm"' in response.text
    assert 'href="/app"' in response.text


def test_workspace_route_serves_graph_first_app():
    with TestClient(main.app) as client:
        response = client.get("/app")
    assert response.status_code == 200
    assert 'class="app-shell founder-os"' in response.text
    assert 'id="fwSvg"' in response.text
    assert 'id="fwInput"' in response.text
    assert 'id="fwInsightsBtn"' in response.text


def test_workspace_trailing_slash_redirects_to_canonical_route():
    with TestClient(main.app, follow_redirects=False) as client:
        response = client.get("/app/")
    assert response.status_code == 308
    assert response.headers["location"] == "/app"


def test_graph_endpoint_returns_empty_or_persisted_graph():
    with TestClient(main.app) as client:
        response = client.get("/api/graph")
    assert response.status_code == 200
    body = response.json()
    assert set(body) >= {"root", "nodes", "edges"}
    assert isinstance(body["nodes"], list)
    assert isinstance(body["edges"], list)


def test_health_endpoint_is_available():
    with TestClient(main.app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
