import asyncio

from playwright.async_api import async_playwright

from app.integrations.pdf.figure_layout import CLOSE_FIGURE_GAPS_JS


def _para(tag, lines=6):
    return f"<p data-id='{tag}'>" + ("Words that fill a line of body text on the page. " * 6 * lines) + "</p>"


def _figure(tag, height=700):
    return f"<div class='diagram-box' data-id='{tag}' style='break-inside: avoid;'><svg style='height:{height}px;width:100%;display:block'></svg></div>"


def _image(tag, height=340):
    pixel = "data:image/gif;base64,R0lGODlhAQABAAAAACw="
    return f"<p data-id='{tag}' style='break-inside: avoid;'><img src='{pixel}' style='width:600px;height:{height}px;display:block'/></p>"


async def _layout(body):
    html = (
        "<html><body style='margin:0;font:16px/1.6 sans-serif'><div class='research-container'>"
        f"<div class='research-content'>{body}</div></div></body></html>"
    )
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page()
        await page.set_content(html)
        stats = await page.evaluate(CLOSE_FIGURE_GAPS_JS)
        order = await page.evaluate(
            "() => Array.from(document.querySelector('.research-content').children).map(e => e.dataset.id || e.tagName)"
        )
        leftover_style = await page.evaluate("() => document.querySelector('.research-container').style.cssText")
        heights = await page.evaluate(
            "() => Array.from(document.querySelectorAll('.diagram-box svg, p > img')).map(e => e.getBoundingClientRect().height)"
        )
        await browser.close()
    return stats, order, leftover_style, heights


def _run(body):
    return asyncio.run(_layout(body))


def test_text_after_a_jumping_figure_moves_up_and_stays_in_its_section():
    body = "<h2>One</h2>" + _para("a", 7) + _figure("fig") + _para("b") + _para("c") + "<h2>Two</h2>" + _para("d")
    stats, order, leftover_style, _ = _run(body)

    assert stats["moved"] >= 1
    assert order.index("a") < order.index("b") < order.index("fig")
    assert order.index("fig") < order.index("H2", 1)
    assert sorted(x for x in order if x != "H2") == ["a", "b", "c", "d", "fig"]
    assert order[-2:] == ["H2", "d"]
    assert "column" not in leftover_style


def test_figure_at_the_end_of_a_section_never_crosses_into_the_next_one():
    body = "<h2>One</h2>" + _para("a", 7) + _figure("fig", 880) + "<h2>Two</h2>" + _para("d")
    stats, order, _, _ = _run(body)

    assert stats["moved"] == 0
    assert stats["remaining"] == 1
    assert order == ["H2", "a", "fig", "H2", "d"]


def test_slightly_too_tall_figure_is_shrunk_in_place_rather_than_moved():
    body = "<p data-id='a' style='height:650px;margin:0'>text</p>" + _figure("fig", 340) + _para("b")
    stats, order, _, heights = _run(body)

    assert stats["shrunk"] == 1 and stats["moved"] == 0
    assert order.index("fig") < order.index("b")
    assert 340 * 0.8 <= heights[0] < 340


def test_image_figures_are_handled_and_small_gaps_left_alone():
    stats, order, _, _ = _run("<h2>One</h2>" + _para("a", 7) + _image("img") + _para("b"))
    assert stats["figures"] == 1
    assert stats["moved"] + stats["shrunk"] >= 1
    assert set(order) == {"H2", "a", "img", "b"}

    stats, order, _, _ = _run("<h2>One</h2>" + _para("a", 2) + _figure("fig", 300) + _para("b"))
    assert stats == {"figures": 1, "shrunk": 0, "moved": 0, "remaining": 0}
    assert order == ["H2", "a", "fig", "b"]


def test_pages_without_research_content_are_untouched():
    async def run():
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            page = await browser.new_page()
            await page.set_content("<div class='chapter-container'>notes</div>")
            result = await page.evaluate(CLOSE_FIGURE_GAPS_JS)
            await browser.close()
            return result

    assert asyncio.run(run()) == {"skipped": True}
