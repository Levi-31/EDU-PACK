import asyncio
import io
from types import SimpleNamespace

import pytest
from PIL import Image, ImageDraw

from app.modules.research.nodes import reducer
from app.modules.research.services.mermaid import clean_mermaid, count_flowchart_nodes
from app.modules.research.services.image import (
    CLIP_RETRY_HINT,
    MAX_CLIP_ATTEMPTS,
    ClippedImageError,
    content_touches_edge,
    flatten_near_white,
    generate_unclipped,
)


def _diagram(box, background="white") -> bytes:
    img = Image.new("RGB", (1536, 1024), background)
    ImageDraw.Draw(img).rectangle(box, outline="black", width=4)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


CENTERED = _diagram((400, 300, 1100, 700))
CUT_ON_LEFT = _diagram((-50, 300, 500, 700))
CUT_ON_BOTTOM = _diagram((400, 500, 1100, 1100))


def test_detects_box_running_off_the_edge():
    assert content_touches_edge(CUT_ON_LEFT)
    assert content_touches_edge(CUT_ON_BOTTOM)


def test_centered_diagram_and_tinted_background_are_not_flagged():
    assert not content_touches_edge(CENTERED)
    assert not content_touches_edge(_diagram((400, 300, 1100, 700), background=(250, 248, 245)))


def test_flatten_near_white_removes_tint_but_keeps_content():
    img = Image.new("RGB", (2, 1), (250, 248, 245))
    img.putpixel((1, 0), (40, 40, 40))
    flattened = flatten_near_white(img)
    assert flattened.getpixel((0, 0)) == (255, 255, 255)
    assert flattened.getpixel((1, 0)) == (40, 40, 40)


def test_retries_with_stricter_prompt_until_diagram_fits():
    prompts = []
    responses = iter([CUT_ON_LEFT, CENTERED])

    async def generate_raw(prompt):
        prompts.append(prompt)
        return next(responses)

    result = asyncio.run(generate_unclipped(generate_raw, "draw"))

    assert prompts == ["draw", f"draw{CLIP_RETRY_HINT}"]
    assert Image.open(io.BytesIO(result)).size == (1600, 900)


def test_gives_up_instead_of_returning_a_cut_diagram():
    calls = []

    async def generate_raw(prompt):
        calls.append(prompt)
        return CUT_ON_LEFT

    with pytest.raises(ClippedImageError):
        asyncio.run(generate_unclipped(generate_raw, "draw"))
    assert len(calls) == MAX_CLIP_ATTEMPTS


def test_reducer_omits_image_that_stays_cut_off(tmp_path, monkeypatch):
    class AlwaysClipped:
        async def generate_image_bytes(self, prompt):
            raise ClippedImageError("cut off")

    monkeypatch.setattr(reducer.ServiceFactory, "get_image_generator", staticmethod(lambda: AlwaysClipped()))
    state = {
        "plan": SimpleNamespace(blog_title="Probe"),
        "md_with_placeholders": "Before\n\n[[IMAGE_1]]\n\nAfter\n",
        "image_specs": [
            {"placeholder": "[[IMAGE_1]]", "filename": "a.png", "prompt": "secret prompt", "alt": "alt", "caption": "cap"}
        ],
        "output_dir": str(tmp_path),
    }

    final = reducer.generate_and_place_images(state)["final"]

    assert "[[IMAGE_1]]" not in final
    assert "IMAGE GENERATION FAILED" not in final
    assert "secret prompt" not in final
    assert "Before" in final and "After" in final


def _spec(**overrides):
    spec = {"placeholder": "[[IMAGE_1]]", "filename": "a.png", "prompt": "draw it", "alt": "alt", "caption": "cap"}
    spec.update(overrides)
    return spec


def _run_reducer(tmp_path, monkeypatch, spec, mermaid_error):
    class FakeImages:
        calls = []

        async def generate_image_bytes(self, prompt):
            self.calls.append(prompt)
            return CENTERED

    async def fake_find_error(code):
        return mermaid_error

    monkeypatch.setattr(reducer.ServiceFactory, "get_image_generator", staticmethod(lambda: FakeImages()))
    monkeypatch.setattr(reducer, "find_mermaid_error", fake_find_error)
    state = {
        "plan": SimpleNamespace(blog_title="Probe"),
        "md_with_placeholders": "Before\n\n[[IMAGE_1]]\n\nAfter\n",
        "image_specs": [spec],
        "output_dir": str(tmp_path),
    }
    return reducer.generate_and_place_images(state)["final"], FakeImages.calls


def test_valid_mermaid_becomes_fenced_block_without_image_call(tmp_path, monkeypatch):
    spec = _spec(kind="mermaid", mermaid_code='flowchart TD\n    A["One"] --> B["Two"]')

    final, image_calls = _run_reducer(tmp_path, monkeypatch, spec, mermaid_error=None)

    assert '```mermaid\nflowchart TD\n    A["One"] --> B["Two"]\n```\n*cap*' in final
    assert image_calls == []
    assert not (tmp_path / "images" / "a.png").exists()


def test_invalid_mermaid_falls_back_to_generated_image(tmp_path, monkeypatch):
    spec = _spec(kind="mermaid", mermaid_code="flowchart TD\n    A[[[")

    final, image_calls = _run_reducer(tmp_path, monkeypatch, spec, mermaid_error="Parse error")

    assert "```mermaid" not in final
    assert "![alt](images/a.png)" in final
    assert image_calls == ["draw it"]


def test_image_kind_and_older_specs_still_use_the_image_model(tmp_path, monkeypatch):
    final, image_calls = _run_reducer(tmp_path, monkeypatch, _spec(kind="image"), mermaid_error=None)
    assert "![alt](images/a.png)" in final
    assert image_calls == ["draw it"]

    (tmp_path / "images" / "a.png").unlink()
    image_calls.clear()
    final, image_calls = _run_reducer(tmp_path, monkeypatch, _spec(), mermaid_error=None)
    assert "![alt](images/a.png)" in final
    assert image_calls == ["draw it"]


def _chain(direction, count):
    return f"flowchart {direction}\n    " + " --> ".join(f'N{i}["Step {i} (a)"]' for i in range(count))


def test_counts_nodes_once_and_ignores_brackets_inside_labels():
    code = 'flowchart TD\n    A["one [x] y(z)"] --> B["two"]\n    A --> C{"three"}\n    B --> C'
    assert count_flowchart_nodes(code) == 3
    assert count_flowchart_nodes("sequenceDiagram\n    A->>B: hi(there)") == 0


def test_long_horizontal_flowcharts_become_vertical_but_short_ones_do_not():
    assert clean_mermaid(_chain("LR", 7)).startswith("flowchart TD")
    assert clean_mermaid(_chain("LR", 4)).startswith("flowchart LR")


def test_oversized_flowchart_is_condensed_once(tmp_path, monkeypatch):
    prompts = []

    class FakeLLM:
        async def ainvoke(self, messages):
            prompts.append(messages[1].content)
            return SimpleNamespace(content=_chain("TD", 5))

    monkeypatch.setattr(reducer, "llm", FakeLLM())
    spec = _spec(kind="mermaid", mermaid_code=_chain("TD", 20))

    final, image_calls = _run_reducer(tmp_path, monkeypatch, spec, mermaid_error=None)

    assert len(prompts) == 1
    assert "N4[" in final and "N5[" not in final
    assert image_calls == []


def test_oversized_flowchart_is_kept_if_condensing_fails(tmp_path, monkeypatch):
    class BrokenLLM:
        async def ainvoke(self, messages):
            raise RuntimeError("llm down")

    monkeypatch.setattr(reducer, "llm", BrokenLLM())
    spec = _spec(kind="mermaid", mermaid_code=_chain("TD", 20))

    final, image_calls = _run_reducer(tmp_path, monkeypatch, spec, mermaid_error=None)

    assert "N19[" in final
    assert image_calls == []


def test_saved_text_is_the_writers_copy_not_the_planners_retyped_one(tmp_path, monkeypatch):
    class NoImages:
        async def generate_image_bytes(self, prompt):
            raise AssertionError("no image expected")

    async def no_error(code):
        return None

    monkeypatch.setattr(reducer.ServiceFactory, "get_image_generator", staticmethod(lambda: NoImages()))
    monkeypatch.setattr(reducer, "find_mermaid_error", no_error)
    state = {
        "plan": SimpleNamespace(blog_title="Probe"),
        "merged_md": "# Probe\n\n## Caching\n\nClean code\u2014critical text.\n\nMore.\n",
        "md_with_placeholders": "# Probe\n\n## Caching\n\nClean code1 critical text.\n\n[[IMAGE_1]]\n",
        "image_specs": [
            _spec(kind="mermaid", section_heading="Caching", mermaid_code='flowchart TD\n    A["a"] --> B["b"]')
        ],
        "output_dir": str(tmp_path),
    }

    final = reducer.generate_and_place_images(state)["final"]

    assert "code\u2014critical" in final and "code1" not in final
    assert final.index("critical text.") < final.index("```mermaid") < final.index("More.")
