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


def test_workspace_example_populates_composer(page):
    page.goto(BASE_URL + "/app")
    page.locator("[data-example]").first.click()
    assert len(page.locator("#input").input_value()) > 20
