
from app.integrations.pdf.renderer import fit_heading, shorten_title
from app.modules.research.models import Plan, Task
from app.modules.research.nodes.orchestrator import normalize_plan
from app.modules.research.nodes.reducer import place_visuals_in_sections
from app.modules.research.services.mermaid import clean_mermaid, flowchart_shape
from app.modules.research.text_cleanup import repair_control_chars, strip_reference_notes

DOC = """# Title

## Stage 1: Programming Fundamentals

Intro to programming.
Second line of the same paragraph.

### What to Learn

- Python

## Stage 5: RAG Techniques

### Core Concepts

Chunking and embeddings explained.

```bash
## not a heading
```

## Closing Notes

Bye.

[[IMAGE_1]]
"""


def _spec(**overrides):
    spec = {"placeholder": "[[IMAGE_1]]", "caption": "cap", "alt": "alt"}
    spec.update(overrides)
    return spec


def _section_of(md, marker="[[IMAGE_1]]"):
    before = md[: md.index(marker)]
    return [line for line in before.splitlines() if line.startswith("## ")][-1]


def test_visual_stranded_at_the_end_moves_to_the_named_section_after_its_first_paragraph():
    placed = place_visuals_in_sections(DOC, [_spec(section_heading="Stage 1: Programming Fundamentals")])

    assert placed.count("[[IMAGE_1]]") == 1
    assert _section_of(placed) == "## Stage 1: Programming Fundamentals"
    assert placed.index("Second line of the same paragraph.") < placed.index("[[IMAGE_1]]") < placed.index("### What to Learn")


def test_heading_match_ignores_markup_and_accepts_partial_text():
    placed = place_visuals_in_sections(DOC, [_spec(section_heading="**stage 5 rag techniques**")])
    assert _section_of(placed) == "## Stage 5: RAG Techniques"

    placed = place_visuals_in_sections(DOC, [_spec(section_heading="Programming Fundamentals")])
    assert _section_of(placed) == "## Stage 1: Programming Fundamentals"


def test_missing_heading_falls_back_to_caption_words():
    placed = place_visuals_in_sections(DOC, [_spec(section_heading="Nope", caption="Techniques used in RAG pipelines")])
    assert _section_of(placed) == "## Stage 5: RAG Techniques"


def test_placeholder_inserted_when_planner_dropped_it_and_kept_when_nothing_matches():
    no_placeholder = DOC.replace("[[IMAGE_1]]", "")
    placed = place_visuals_in_sections(no_placeholder, [_spec(section_heading="Closing Notes")])
    assert _section_of(placed) == "## Closing Notes"

    unmatched = place_visuals_in_sections(DOC, [_spec(section_heading=None, caption="zzzz", alt="qqqq")])
    assert unmatched == DOC


def test_hash_lines_inside_code_fences_are_not_sections():
    placed = place_visuals_in_sections(DOC, [_spec(section_heading="not a heading")])
    assert "## not a heading\n\n\n[[IMAGE_1]]" not in placed


def _task(task_id, title):
    return Task(id=task_id, title=title, goal="g", bullets=["a", "b", "c"], target_words=200)


def _plan(title, *task_titles):
    tasks = [_task(i, t) for i, t in enumerate(task_titles, start=1)]
    return Plan(blog_title=title, audience="a", tone="t", tasks=tasks)


def test_layout_chores_are_dropped_and_writer_instructions_removed_from_headings():
    plan = normalize_plan(
        _plan(
            "GenAI Developer Roadmap: A Clear Path to Becoming a Programmer",
            "Design the cover page",
            "Outline Stage 1: Programming Fundamentals",
            "Compose the closing notes page",
            "Design a RAG Pipeline",
            "Create Your First Agent",
        )
    )

    assert plan.blog_title == "GenAI Developer Roadmap"
    assert [t.title for t in plan.tasks] == [
        "Stage 1: Programming Fundamentals",
        "Closing notes",
        "Design a RAG Pipeline",
        "Create Your First Agent",
    ]


def test_plan_of_only_layout_tasks_is_left_usable():
    plan = normalize_plan(_plan("Guide To Things", "Design the cover page"))
    assert len(plan.tasks) == 1


def test_shorten_title_keeps_titles_that_would_lose_their_meaning():
    assert shorten_title("RAG: A Practical Guide") == "RAG: A Practical Guide"
    assert shorten_title("Agents - The Why And How Of It") == "Agents - The Why And How Of It"
    assert shorten_title("Building Agents — A Field Guide") == "Building Agents"


def test_fit_heading_shrinks_font_then_cuts_words_but_never_mid_word():
    short = fit_heading("GenAI Roadmap", width_pt=493, max_pt=26)
    assert short == {"text": "GenAI Roadmap", "font_pt": 26}

    medium = fit_heading("A Considerably Longer Heading That Needs A Smaller Font", width_pt=493, max_pt=26)
    assert medium["font_pt"] < 26
    assert "Smaller Font" in medium["text"]

    very_long = " ".join(["word"] * 60)
    fitted = fit_heading(very_long, width_pt=493, max_pt=26)
    assert 14 <= fitted["font_pt"] < 15
    assert fitted["text"].split() == ["word"] * len(fitted["text"].split())
    assert len(fitted["text"].split()) < 60


def test_repair_control_chars_restores_punctuation_seen_in_real_output():
    assert repair_control_chars("Here\x1fs how, CampusX\x1fs channel, you\x1fll see") == "Here’s how, CampusX’s channel, you’ll see"
    assert repair_control_chars("output\x1flower values") == "output—lower values"
    assert repair_control_chars("Video 3** \x1f This one") == "Video 3** — This one"
    assert repair_control_chars("maintainable code\x00critical, versions\x01fundamentals") == "maintainable code—critical, versions—fundamentals"
    assert repair_control_chars("**Gemini** \x130 A model, graph\x131style") == "**Gemini** — A model, graph-style"
    assert repair_control_chars('- \x1b\x1b"Python Tutorial\x1b\x1b" covers') == '- "Python Tutorial" covers'
    assert repair_control_chars("keep\ttabs\nand newlines\r\n and café") == "keep\ttabs\nand newlines\r\n and café"


HUB = 'flowchart TD\n    H["Hub"] --> A["a"]\n    H --> B["b"]\n    H --> C["c"]\n    H --> D["d"]\n    H --> E["e"]\n    H --> F["f"]\n    A --> P["Project"]\n    F --> P\n'


def test_flowchart_shape_reads_layers_including_chains_and_labels():
    assert flowchart_shape(HUB) == (3, 6)
    assert flowchart_shape('flowchart TD\n    A["x --> y"] --> B["b"] --> C["c"]') == (3, 1)
    assert flowchart_shape('flowchart LR\n    A -->|"yes"| B\n    B -.-> C\n    C ==> D') == (4, 1)
    assert flowchart_shape("sequenceDiagram\n    A->>B: hi") == (0, 0)


def test_flowchart_shape_survives_cycles():
    ranks, widest = flowchart_shape('flowchart TD\n    A["a"] --> B["b"]\n    B --> A')
    assert ranks >= 1 and widest >= 1


def test_direction_follows_diagram_shape():
    assert clean_mermaid(HUB).startswith("flowchart LR")
    chain = 'flowchart LR\n    ' + " --> ".join(f'N{i}["n"]' for i in range(7))
    assert clean_mermaid(chain).startswith("flowchart TD")
    short = 'flowchart LR\n    A["a"] --> B["b"] --> C["c"]'
    assert clean_mermaid(short).startswith("flowchart LR")
    assert clean_mermaid("sequenceDiagram\n    A->>B: hi").startswith("sequenceDiagram")


def test_strip_reference_notes_removes_notes_and_sections_but_not_real_content():
    md = (
        "## Topic\n\nCross references are useful in code.\n\n"
        "*References for ML concepts are synthesized from notable resources.*\n\n"
        "References: Multiple collections.\n\n"
        "### Recommended Resources\n\n- A video\n\n"
        "## References\n\n1. Thing\n2. Other\n\n"
        "## Closing\n\nBye.\n\n"
        "```python\nreferences = 1\n# References\n```\n"
    )
    cleaned = strip_reference_notes(md)

    assert "synthesized" not in cleaned
    assert "Multiple collections" not in cleaned
    assert "## References" not in cleaned
    assert "1. Thing" not in cleaned
    assert "Cross references are useful in code." in cleaned
    assert "### Recommended Resources" in cleaned and "- A video" in cleaned
    assert "## Closing" in cleaned and "Bye." in cleaned
    assert "references = 1\n# References" in cleaned
