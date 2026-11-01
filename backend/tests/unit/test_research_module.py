import pytest
from app.modules.research.models import (
    Task,
    Plan,
    RouterDecision,
    EvidenceItem,
    ImageSpec,
    GlobalImagePlan,
    State,
)
from app.modules.research.nodes.router import router_node, route_next
from app.modules.research.nodes.research import research_node
from app.modules.research.nodes.orchestrator import orchestrator_node, fanout
from app.modules.research.nodes.worker import worker_node
from app.modules.research.nodes.reducer import merge_content, decide_images
from app.modules.research.interfaces import SearchService, ImageGeneratorService
from app.modules.research.graph import app as research_graph


def test_research_models_validation():
    # Test RouterDecision
    rd = RouterDecision(
        needs_research=True,
        mode="hybrid",
        reason="Topic requires architectural background plus current evidence.",
        queries=["test query 1", "test query 2"]
    )
    assert rd.mode == "hybrid"
    assert len(rd.queries) == 2

    # Test Plan and Task
    t1 = Task(id=1, title="Introduction", goal="Overview of topic", bullets=["Concept A", "Concept B", "Concept C"], target_words=200)
    t2 = Task(id=2, title="Deep Dive", goal="Architecture details", bullets=["Engine 1", "Engine 2", "Engine 3"], target_words=350)
    plan = Plan(blog_title="Technical Guide", audience="Engineers", tone="Technical", blog_kind="explainer", tasks=[t1, t2])
    assert len(plan.tasks) == 2
    assert plan.tasks[0].title == "Introduction"

    # Test ImageSpec
    spec = ImageSpec(
        placeholder="[[IMAGE_1]]",
        filename="distributed_cache.png",
        alt="System architecture diagram",
        caption="Figure 1: Cache architecture",
        prompt="A system architecture diagram of distributed cache"
    )
    assert spec.placeholder == "[[IMAGE_1]]"
    assert spec.filename == "distributed_cache.png"


def test_router_three_modes():
    # 1. Closed book (evergreen CS theory)
    r_cb = RouterDecision(needs_research=False, mode="closed_book", reason="Evergreen theory", queries=[])
    assert r_cb.mode == "closed_book"
    assert len(r_cb.queries) == 0

    # 2. Hybrid (evergreen + current)
    r_hy = RouterDecision(needs_research=True, mode="hybrid", reason="Evergreen + 2026 updates", queries=["react 19 server actions"])
    assert r_hy.mode == "hybrid"
    assert len(r_hy.queries) == 1

    # 3. Open book (volatile news)
    r_ob = RouterDecision(needs_research=True, mode="open_book", reason="Volatile market data", queries=["latest nvidia ai chip pricing 2026"])
    assert r_ob.mode == "open_book"
    assert len(r_ob.queries) == 1


def test_route_next_logic():
    state_closed: State = {"needs_research": False}
    assert route_next(state_closed) == "orchestrator"

    state_open: State = {"needs_research": True}
    assert route_next(state_open) == "research"


def test_reducer_merge_content():
    t1 = Task(id=1, title="Architecture", goal="Explain architecture", bullets=["B1", "B2", "B3"], target_words=200)
    t2 = Task(id=2, title="Consensus", goal="Explain consensus", bullets=["C1", "C2", "C3"], target_words=200)
    plan = Plan(blog_title="Distributed Storage Architecture", audience="Engineers", tone="Technical", blog_kind="explainer", tasks=[t1, t2])

    state: State = {
        "topic": "Distributed Storage",
        "mode": "hybrid",
        "needs_research": False,
        "queries": [],
        "evidence": [],
        "plan": plan,
        "as_of": "2026-10-31",
        "recency_days": 7,
        "sections": [
            (1, "## Architecture\n\nStorage engines use LSM trees and B-trees."),
            (2, "## Consensus\n\nRaft guarantees linearizable replication.")
        ],
        "merged_md": "",
        "final": "",
        "image_specs": [],
        "md_with_placeholders": "",
        "output_dir": None,
    }

    merged = merge_content(state)
    assert "# Distributed Storage Architecture" in merged["merged_md"]
    assert "## Architecture" in merged["merged_md"]
    assert "## Consensus" in merged["merged_md"]


def test_orchestrator_fanout():
    t1 = Task(id=1, title="Task 1", goal="Goal 1", bullets=["A", "B", "C"], target_words=150)
    t2 = Task(id=2, title="Task 2", goal="Goal 2", bullets=["D", "E", "F"], target_words=150)
    plan = Plan(blog_title="Test Plan", audience="Engineers", tone="Technical", tasks=[t1, t2])

    state: State = {
        "topic": "Test",
        "mode": "closed_book",
        "as_of": "2026-10-31",
        "recency_days": 7,
        "plan": plan,
        "evidence": [],
    }

    sends = fanout(state)
    assert len(sends) == 2
    assert sends[0].node == "worker"
    assert sends[0].arg["task"]["id"] == 1
    assert sends[1].arg["task"]["id"] == 2


def test_compiled_graph_structure():
    assert research_graph is not None
    # Graph has nodes: router, research, orchestrator, worker, reducer
    node_names = set(research_graph.nodes.keys())
    assert "router" in node_names
    assert "research" in node_names
    assert "orchestrator" in node_names
    assert "worker" in node_names
    assert "reducer" in node_names
