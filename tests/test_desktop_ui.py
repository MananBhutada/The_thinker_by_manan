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
    assert page.locator(".app-shell").is_visible()


def test_workspace_graph_first_shell(page):
    page.goto(BASE_URL + "/app")
    page.wait_for_selector(".fw-stage", timeout=10000)
    assert page.locator(".app-shell.founder-os").is_visible()
    assert page.locator("#fwSvg").is_visible()
    assert page.locator("#fwInput").is_visible()
    assert page.locator("#fwMapBtn").is_visible()
    assert page.locator("#fwSearch").is_visible()
    assert page.locator("#fwInsightsBtn").is_visible()


def test_workspace_has_expected_graph_lenses(page):
    page.goto(BASE_URL + "/app")
    page.wait_for_selector("#fwLenses", timeout=10000)
    lenses = page.locator("#fwLenses button")
    assert lenses.count() >= 6
    labels = [text.strip() for text in lenses.all_inner_texts()]
    for expected in ["Brain", "Money", "Product", "People", "Risk", "Evidence", "Sequence", "Future"]:
        assert expected in labels


def test_workspace_insights_drawer_opens_and_closes(page):
    page.goto(BASE_URL + "/app")
    page.wait_for_selector("#fwInsightsBtn", timeout=10000)
    assert page.locator("#fwInsights").get_attribute("aria-hidden") == "true"
    page.locator("#fwInsightsBtn").click(force=True)
    page.wait_for_timeout(200)
    assert page.locator("#fwInsights").get_attribute("aria-hidden") == "false"
    assert page.locator("#fwInsights").is_visible()
    page.locator("#fwInsClose").click(force=True)
    page.wait_for_timeout(200)
    assert page.locator("#fwInsights").get_attribute("aria-hidden") == "true"


def test_workspace_menu_exposes_archive_and_settings(page):
    page.goto(BASE_URL + "/app")
    page.wait_for_selector("#menuToggle", timeout=10000)
    page.locator("#menuToggle").click()
    page.wait_for_timeout(200)
    assert page.locator(".sidebar .nav-item[data-tab='archive']").count() == 1
    assert page.locator(".sidebar .nav-item[data-tab='settings']").count() == 1
