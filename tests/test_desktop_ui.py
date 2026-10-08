"""
FounderOS desktop/browser smoke tests.

These tests follow the current product split:
- / is the public FounderOS introduction/landing page.
- /app is the graph-first workspace.
"""

import os

import pytest
from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("DECISION_BRIEF_TEST_URL", "http://127.0.0.1:8010")


@pytest.fixture(scope="module")
def page():
    p = sync_playwright().start()
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1280, "height": 800})
    yield pg
    pg.close()
    b.close()
    p.stop()


def test_landing_page_is_founderos_intro(page):
    page.goto(BASE_URL)
    page.wait_for_selector(".hero", timeout=10000)
    assert page.locator(".hero").is_visible()
    assert page.locator(".brand").inner_text() == "FounderOS"
    assert "Your brain is not a" in page.locator("h1").inner_text()
    assert page.locator("#seedForm").is_visible()
    assert page.locator("#seedText").is_visible()
    assert page.locator("#seedGo").is_visible()


def test_landing_page_links_to_workspace(page):
    page.goto(BASE_URL)
    page.wait_for_selector("a[href='/app']", timeout=10000)
    links = page.locator("a[href='/app']")
    assert links.count() >= 1
    assert "Open workspace" in page.locator("a.nav-cta").inner_text()


def test_landing_example_populates_composer(page):
    page.goto(BASE_URL)
    page.locator("#seedExample").click()
    value = page.locator("#seedText").input_value()
    assert "PulseSense" in value
    assert len(value) > 20


def test_landing_composer_opens_workspace(page):
    page.goto(BASE_URL)
    page.locator("#seedText").fill("We are building a product and need to validate customers.")
    page.locator("#seedGo").click()
    page.wait_for_url("**/app", timeout=10000)
    assert page.url.rstrip("/").endswith("/app")
    assert page.locator(".shell").is_visible()


def test_workspace_graph_first_shell(page):
    page.goto(BASE_URL + "/app")
    page.wait_for_selector("#canvas", timeout=10000)
    assert page.locator(".shell").is_visible()
    assert page.locator(".graph canvas").is_visible()
    assert page.locator("#input").is_visible()
    assert page.locator("#map").is_visible()
    assert page.locator("#search").is_visible()


def test_workspace_is_clean_graph_first_ui(page):
    page.goto(BASE_URL + "/app")
    assert page.locator(".rail").is_visible()
    assert page.locator(".composer").is_visible()
    assert page.locator(".inspector").count() == 1
    assert page.locator(".fw-stage").count() == 0
    assert page.locator("#fwSvg").count() == 0


def test_workspace_graph_controls_work(page):
    page.goto(BASE_URL + "/app")
    page.wait_for_selector("#canvas", timeout=10000)
    page.locator("#fit").click()
    page.locator("#search").fill("runway")
    assert page.locator("#search").input_value() == "runway"


def test_workspace_graph_viewport_interactions(page):
    page.goto(BASE_URL + "/app")
    page.wait_for_selector("#canvas", timeout=10000)
    page.wait_for_function("document.querySelector('#canvas')?.dataset.scale")
    canvas = page.locator("#canvas")
    box = canvas.bounding_box()
    assert box
    cx, cy = box["width"] / 2, box["height"] / 2

    # Wheel zoom changes scale and keeps the cursor anchored.
    scale_before = float(canvas.get_attribute("data-scale"))
    page.mouse.move(box["x"] + 120, box["y"] + 120)
    page.mouse.wheel(0, -500)
    page.wait_for_function("(before) => Number(document.querySelector('#canvas').dataset.scale) > before", scale_before)

    # Empty-canvas drag pans the camera.
    pan_before = float(canvas.get_attribute("data-pan-x"))
    page.mouse.move(box["x"] + box["width"] * 0.75, box["y"] + box["height"] * 0.75)
    page.mouse.down()
    page.mouse.move(box["x"] + box["width"] * 0.75 + 80, box["y"] + box["height"] * 0.75 + 35)
    page.mouse.up()
    page.wait_for_function("(before) => Number(document.querySelector('#canvas').dataset.panX) != before", pan_before)

    # Fit and Focus are wired to the camera.
    page.locator("#fit").click()
    page.locator("#focusTool").click()

    # Seed a real node, drag it, and verify the saved position survives reload.
    graph = page.request.get(BASE_URL + "/api/graph").json()
    if not graph.get("nodes"):
        graph["nodes"] = [{
            "id": "ui-test-domain",
            "title": "UI Test Domain",
            "level": "domain",
            "type": "domain",
            "domain": "UI Test Domain",
            "x": 260,
            "y": 0,
            "thoughts": [],
            "summary": "UI test",
            "details": "UI test",
            "status": "active",
            "source": "founder",
        }]
        graph["edges"] = [{"source": "root", "target": "ui-test-domain", "kind": "structural", "relationship": "contains", "confidence": 100}]
        response = page.request.post(BASE_URL + "/api/graph/mutate", data={"graph": graph})
        assert response.ok
    page.reload()
    page.wait_for_selector("#canvas", timeout=10000)
    page.wait_for_function("document.querySelector('#canvas')?.dataset.scale")
    page.locator("#fit").click()
    page.wait_for_timeout(400)

    graph = page.request.get(BASE_URL + "/api/graph").json()
    node = next((n for n in graph.get("nodes", []) if n.get("id") == "ui-test-domain"), None)
    if node:
        canvas = page.locator("#canvas")
        box = canvas.bounding_box()
        assert box
        # Select the node by clicking near its fitted position.
        sx = box["x"] + box["width"] / 2 + float(node.get("x", 0)) * float(canvas.get_attribute("data-scale"))
        sy = box["y"] + box["height"] / 2 + float(node.get("y", 0)) * float(canvas.get_attribute("data-scale"))
        page.mouse.move(sx, sy)
        page.mouse.down()
        page.mouse.move(sx + 90, sy + 55)
        page.mouse.up()
        page.wait_for_timeout(500)
        saved = page.request.get(BASE_URL + "/api/graph").json()
        moved = next(n for n in saved.get("nodes", []) if n.get("id") == "ui-test-domain")
        assert abs(float(moved.get("x", 0)) - float(node.get("x", 0))) > 1
        assert abs(float(moved.get("y", 0)) - float(node.get("y", 0))) > 1


def test_workspace_composer_accepts_input(page):
    page.goto(BASE_URL + "/app")
    page.locator("#input").fill("We need to validate customers before building the next feature.")
    assert len(page.locator("#input").input_value()) > 20
