"""
English text — English text
English textEnglish text http://127.0.0.1:8010 English text
English text sync_playwright English textEnglish text pytest-playwright fixture
"""
import json
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


def test_app_shell_two_pane_layout(page):
    """English text .app-shell English textEnglish text .ios-wrapper English text"""
    page.goto(BASE_URL)
    page.wait_for_selector(".app-shell", timeout=10000)
    assert page.locator(".app-shell").is_visible()
    # ios-wrapper English text
    ios = page.locator(".ios-wrapper")
    if ios.count() > 0:
        assert not ios.is_visible()


def test_sidebar_visible_with_nav(page):
    """English text 4 English text nav-itemEnglish text/English text/English text/English text"""
    page.goto(BASE_URL)
    page.wait_for_selector(".sidebar .nav-item", timeout=10000)
    navs = page.locator(".sidebar .nav-item")
    assert navs.count() == 4
    assert navs.nth(0).get_attribute("data-tab") == "chat"
    cls = navs.nth(0).get_attribute("class") or ""
    assert "active" in cls


def test_mode_grid_six_seals(page):
    """English textdata-mode English textEnglish text active"""
    page.goto(BASE_URL)
    page.wait_for_selector(".mode-grid .mode-card", timeout=10000)
    # English text init English textapplyPrefs English text setMode
    page.wait_for_timeout(1500)
    cards = page.locator(".mode-grid .mode-card")
    assert cards.count() == 6
    expected = ["auto", "rational", "random", "nature", "dialogue", "fengshui"]
    for i, m in enumerate(expected):
        assert cards.nth(i).get_attribute("data-mode") == m
    # English text mode-card English text activeEnglish text default_mode English text
    active_count = 0
    for i in range(6):
        cls = cards.nth(i).get_attribute("class") or ""
        if "active" in cls:
            active_count += 1
    assert active_count == 1


def test_click_archive_opens_drawer(page):
    """English text nav-item English text"""
    page.goto(BASE_URL)
    page.wait_for_selector(".nav-item[data-tab='archive']", timeout=10000)
    page.locator(".nav-item[data-tab='archive']").click()
    page.wait_for_timeout(300)
    cls = page.locator("#drawer").get_attribute("class") or ""
    assert "open" in cls
    cls2 = page.locator("#drawerOverlay").get_attribute("class") or ""
    assert "open" in cls2


def test_close_drawer_with_back_button(page):
    """English textEnglish text"""
    page.goto(BASE_URL)
    page.wait_for_selector(".nav-item[data-tab='archive']", timeout=10000)
    page.locator(".nav-item[data-tab='archive']").click()
    page.wait_for_timeout(300)
    page.locator("#drawerBack").click()
    page.wait_for_timeout(300)
    cls = page.locator("#drawer").get_attribute("class") or ""
    assert "open" not in cls


def test_esc_closes_drawer(page):
    """English text Esc English text"""
    page.goto(BASE_URL)
    page.wait_for_selector(".nav-item[data-tab='stats']", timeout=10000)
    page.locator(".nav-item[data-tab='stats']").click()
    page.wait_for_timeout(300)
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    cls = page.locator("#drawer").get_attribute("class") or ""
    assert "open" not in cls


def test_chat_main_area_visible(page):
    """English text"""
    page.goto(BASE_URL)
    page.wait_for_selector("#chatContainer", timeout=10000)
    assert page.locator("#chatContainer").is_visible()
    assert page.locator("#inputText").is_visible()
    assert page.locator("#sendBtn").is_visible()


def test_weather_settings_explain_mock_fallback(page):
    """English text API English textEnglish textEnglish text“English text”"""
    config = {
        "llm": {"model": "", "baseUrl": "", "hasKey": False},
        "weather": {"city": "", "baseUrl": "", "hasKey": False, "hasBaseUrl": False},
        "hasLlm": False,
        "hasWeather": False,
    }

    def handle_config(route):
        route.fulfill(status=200, content_type="application/json", body=json.dumps(config))

    page.route("**/api/config", handle_config)
    try:
        page.goto(BASE_URL)
        page.locator(".nav-item[data-tab='settings']").click()
        page.wait_for_function(
            "document.querySelector('#weatherConfigValue')?.textContent.includes('English text API')"
        )
        status = page.locator("#weatherConfigValue").inner_text()
        assert status == "English text APIEnglish text"
        assert status != "English text"

        page.locator("#setWeatherConfig").click()
        assert page.locator("#w_key").is_visible()
        assert page.locator("#w_base_url").is_visible()
        assert page.locator("#w_city").is_visible()
        assert "English text API English text" in page.locator(".weather-tip").inner_text()
    finally:
        page.unroute("**/api/config", handle_config)


def test_stats_refreshes_each_time_drawer_opens(page):
    calls = {"count": 0}

    def handle_stats(route):
        calls["count"] += 1
        total = 2 if calls["count"] == 1 else 1
        route.fulfill(
            status=200,
            content_type="application/json",
            body=(
                '{"totalDecisions":%d,"modeDistribution":{},'
                '"avgConfidence":0,"executedRate":0,"regretRate":0,"weekTrend":[]}'
            ) % total,
        )

    page.route("**/api/stats", handle_stats)
    try:
        page.goto(BASE_URL)
        page.locator(".nav-item[data-tab='stats']").click()
        page.wait_for_function(
            "document.querySelector('#statsScroll .stat b')?.textContent.trim() === '2'"
        )

        page.locator(".nav-item[data-tab='archive']").click()
        page.locator(".nav-item[data-tab='stats']").click()
        page.wait_for_function(
            "document.querySelector('#statsScroll .stat b')?.textContent.trim() === '1'"
        )
        assert calls["count"] == 2
    finally:
        page.unroute("**/api/stats", handle_stats)


def test_zdog_dice_renders_requested_result(page):
    record = {
        "id": "dice-test-5",
        "question": "English text",
        "mode": "random",
        "result": {
            "type": "random",
            "options": ["English text", "English text", "English text", "English text", "English text", "English text"],
            "wheelResult": "English text",
        },
        "brief": {
            "summary": "English text",
            "confidence": 58,
            "perspectives": [],
            "risks": [],
            "nextSteps": [],
        },
        "createdAt": "2026-07-26T20:00:00",
        "executed": False,
        "regret": False,
    }

    def handle_archive(route):
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"ok": True, "list": [record], "total": 1, "page": 1, "pageSize": 20}),
        )

    def handle_detail(route):
        route.fulfill(status=200, content_type="application/json", body=json.dumps(record))

    page.route("**/api/archive*", handle_archive)
    page.route("**/api/decision/dice-test-5", handle_detail)
    try:
        page.goto(BASE_URL)
        assert page.evaluate("typeof Zdog") == "object"
        page.locator(".nav-item[data-tab='archive']").click()
        page.wait_for_selector(".archive-card[data-id='dice-test-5']")
        page.locator(".archive-card[data-id='dice-test-5']").click()
        page.wait_for_selector(".random-dice-canvas[data-ready='true']")
        page.wait_for_timeout(1600)

        stage = page.locator(".random-dice-canvas-stage")
        assert stage.get_attribute("data-result") == "4"
        painted_pixels = page.locator(".random-dice-canvas").evaluate(
            """canvas => {
                const pixels = canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height).data;
                let painted = 0;
                for (let i = 3; i < pixels.length; i += 4) {
                    if (pixels[i] > 0) painted++;
                }
                return painted;
            }"""
        )
        assert painted_pixels > 1000
    finally:
        page.unroute("**/api/archive*", handle_archive)
        page.unroute("**/api/decision/dice-test-5", handle_detail)


def test_random_effects_preview_renders_six_production_variants(page):
    page.goto(BASE_URL + "/random-effects-preview.html")
    page.wait_for_selector(".preview-effect")
    page.wait_for_selector(".random-dice-canvas[data-ready='true']")
    page.wait_for_timeout(1800)

    variants = page.locator(".preview-effect").evaluate_all(
        "nodes => nodes.map(node => node.dataset.variant)"
    )
    assert variants == ["pointer", "sticks", "dice", "cards", "tickets", "ink"]

    rendered = page.locator(".preview-effect .random-draw").evaluate_all(
        "nodes => nodes.map(node => node.className)"
    )
    assert rendered == [
        "random-draw random-draw--pointer",
        "random-draw random-draw--sticks",
        "random-draw random-draw--dice",
        "random-draw random-draw--cards",
        "random-draw random-draw--tickets",
        "random-draw random-draw--ink",
    ]

    results = page.locator(".preview-effect .random-draw-result").all_text_contents()
    assert results == [
        "English textEnglish text",
        "English textEnglish text",
        "English textEnglish text",
        "English textEnglish text",
        "English textEnglish text",
        "English textEnglish text",
    ]

    stage = page.locator(".random-dice-canvas-stage")
    assert stage.get_attribute("data-result") == "3"
    painted_pixels = page.locator(".random-dice-canvas").evaluate(
        """canvas => {
            const pixels = canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height).data;
            let painted = 0;
            for (let i = 3; i < pixels.length; i += 4) {
                if (pixels[i] > 0) painted++;
            }
            return painted;
        }"""
    )
    assert painted_pixels > 1000


def test_random_preview_cards_flip_one_front_and_sticks_use_palette(page):
    page.goto(BASE_URL + "/random-effects-preview.html")
    page.wait_for_selector("[data-preview-variant='cards'] .random-card-form")

    replay = page.get_by_role("button", name="English text", exact=True)
    replay.click()
    page.wait_for_timeout(620)
    picked = page.locator(
        "[data-preview-variant='cards'] .random-card-form.is-picked"
    )
    assert picked.locator(".random-card-back").evaluate(
        "node => getComputedStyle(node).opacity"
    ) == "1"
    assert picked.locator(".random-card-front").evaluate(
        "node => getComputedStyle(node).opacity"
    ) == "0"

    page.wait_for_timeout(1200)
    assert picked.locator(".random-card-back").evaluate(
        "node => getComputedStyle(node).opacity"
    ) == "0"
    assert picked.locator(".random-card-front").evaluate(
        "node => getComputedStyle(node).opacity"
    ) == "1"
    other_fronts = page.locator(
        "[data-preview-variant='cards'] .random-card-form:not(.is-picked) .random-card-front"
    ).evaluate_all("nodes => nodes.map(node => getComputedStyle(node).opacity)")
    assert other_fronts == ["0"] * 5

    stick_colors = page.locator(
        "[data-preview-variant='sticks'] .random-stick"
    ).evaluate_all("nodes => nodes.map(node => getComputedStyle(node).stroke)")
    assert len(set(stick_colors)) == 2
    assert "rgb(0, 0, 0)" not in stick_colors
    band_color = page.locator(
        "[data-preview-variant='sticks'] .random-stick-cup-band"
    ).evaluate("node => getComputedStyle(node).fill")
    assert band_color != "rgb(0, 0, 0)"

    stick_layers = page.locator(
        "[data-preview-variant='sticks'] .random-sticks-svg"
    ).evaluate(
        """svg => Array.from(svg.children).map(node => node.getAttribute('class') || '')"""
    )
    assert stick_layers.index("random-stick-rim-back") < next(
        i for i, cls in enumerate(stick_layers) if cls.startswith("random-stick ")
    )
    assert next(
        i for i, cls in enumerate(stick_layers) if cls.startswith("random-stick ")
    ) < stick_layers.index("random-stick-cup")
    assert stick_layers.index("random-stick-cup") < stick_layers.index("random-stick-rim-front")

    ticket_geometry = page.locator(
        "[data-preview-variant='tickets'] .random-tickets-svg"
    ).evaluate(
        """svg => {
            const windowRect = svg.querySelector('.random-ticket-window').getBoundingClientRect();
            return Array.from(svg.querySelectorAll('.random-ticket-row')).map(row => {
                const rect = row.getBoundingClientRect();
                const intersects = rect.bottom > windowRect.top && rect.top < windowRect.bottom;
                return {
                    intersects,
                    fullyVisible: rect.top >= windowRect.top - 1 && rect.bottom <= windowRect.bottom + 1,
                };
            });
        }"""
    )
    assert all(row["fullyVisible"] for row in ticket_geometry if row["intersects"])


def test_random_preview_switches_all_four_skins(page):
    page.goto(BASE_URL + "/random-effects-preview.html")
    for label, skin in [
        ("English text", "heritage"),
        ("English text", "workbench"),
        ("English text", "journal"),
        ("English text", "console"),
    ]:
        page.get_by_role("button", name=label, exact=True).click()
        assert page.locator("html").get_attribute("data-skin") == skin
        assert page.locator(".preview-skin.is-active").get_attribute("data-skin") == skin


def test_nature_detail_shows_inputs_and_weights(page):
    record = {
        "id": "nature-reference-test",
        "question": "English text",
        "mode": "nature",
        "result": {
            "type": "nature",
            "signal": "English text",
            "poem": "English textEnglish text",
            "suggestion": "English textEnglish text",
            "source": "amap",
            "isReal": True,
            "city": "English text",
            "weather": "English text",
            "temperature": "29",
            "humidity": "78",
            "wind": "English text 3English text",
            "sun": "English text",
            "moonPhase": "English text",
            "updateTime": "2026-07-26 22:30:00",
            "alarms": [{"title": "English text"}],
            "weatherTrend": "English text · English text · 31℃",
            "forecast_24h": [{"time": "English text", "weather": "English text", "temperature": "31"}],
            "signals": {"weights": [
                {"name": "English text", "weight": 32, "value": "English text"},
                {"name": "English text", "weight": 28, "value": "English text"},
                {"name": "English text", "weight": 6, "value": "English text"},
            ]},
        },
        "brief": None,
        "createdAt": "2026-07-26T22:30:00",
        "executed": False,
        "regret": False,
    }

    def handle_archive(route):
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"ok": True, "list": [record], "total": 1, "page": 1, "pageSize": 20}),
        )

    def handle_detail(route):
        route.fulfill(status=200, content_type="application/json", body=json.dumps(record))

    page.route("**/api/archive*", handle_archive)
    page.route("**/api/decision/nature-reference-test", handle_detail)
    try:
        page.goto(BASE_URL)
        page.locator(".nav-item[data-tab='archive']").click()
        page.locator(".archive-card[data-id='nature-reference-test']").click()
        page.wait_for_selector(".nature-weights")
        assert "English text" in page.locator(".nature-considerations").inner_text()
        assert "English text" in page.locator(".nature-evidence").inner_text()
        assert page.locator(".nature-weight-row").count() == 3
        assert "English text · English text · 31" in page.locator(".nature-forecast").inner_text()
    finally:
        page.unroute("**/api/archive*", handle_archive)
        page.unroute("**/api/decision/nature-reference-test", handle_detail)


def test_dialogue_choice_is_saved_to_history(page):
    saved = {}
    response = {
        "brief": {
            "summary": "English text",
            "confidence": 58,
            "perspectives": [],
            "risks": [],
            "nextSteps": [],
        },
        "nature": None,
        "mode": "dialogue",
        "reply": "English text",
        "result": {
            "type": "dialogue",
            "question": "English textEnglish text",
            "options": ["English text", "English text", "English text"],
        },
        "autoRecognized": None,
        "decisionId": "dialogue-save-test",
    }

    def handle_chat(route):
        route.fulfill(status=200, content_type="application/json", body=json.dumps(response))

    def handle_patch(route):
        saved.update(route.request.post_data_json)
        body = {
            "id": "dialogue-save-test",
            "question": "English text",
            "mode": "dialogue",
            "result": response["result"],
            "dialogueHistory": saved.get("dialogueHistory", []),
            "executed": False,
            "regret": False,
        }
        route.fulfill(status=200, content_type="application/json", body=json.dumps(body))

    page.route("**/api/chat", handle_chat)
    page.route("**/api/decision/dialogue-save-test", handle_patch)
    try:
        page.goto(BASE_URL)
        page.locator(".mode-card[data-mode='dialogue']").click()
        page.locator("#inputText").fill("English text")
        page.locator("#sendBtn").click()
        page.get_by_role("button", name="English text", exact=True).click()
        page.wait_for_function("() => document.querySelector('.dialogue-record') !== null")
        page.wait_for_timeout(100)
        assert saved["dialogueHistory"] == [{
            "question": "English textEnglish text",
            "answer": "English text",
        }]
        assert "dialogueDone" not in saved
    finally:
        page.unroute("**/api/chat", handle_chat)
        page.unroute("**/api/decision/dialogue-save-test", handle_patch)
