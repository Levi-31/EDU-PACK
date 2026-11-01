import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal, init_db
from app.modules.research.research_service import ResearchService

init_db()
client = TestClient(app)


def test_research_api_lifecycle():
    # 1. Create a Research Job via API
    create_resp = client.post(
        "/api/v1/research/generate",
        json={
            "topic": "PostgreSQL 17 Query Optimizer Improvements & B-Tree Deduplication",
            "as_of": "2026-10-31"
        }
    )
    assert create_resp.status_code == 201
    job = create_resp.json()
    job_id = job["id"]
    assert job["topic"] == "PostgreSQL 17 Query Optimizer Improvements & B-Tree Deduplication"
    assert job["as_of"] == "2026-10-31"
    assert job["status"] in ["QUEUED", "RUNNING", "COMPLETED"]

    # 2. Get Research Job Status
    get_resp = client.get(f"/api/v1/research/{job_id}")
    assert get_resp.status_code == 200
    detail = get_resp.json()
    assert detail["id"] == job_id

    # 3. List Research Jobs
    list_resp = client.get("/api/v1/research?page=1&page_size=10")
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert list_data["total"] >= 1
    assert any(j["id"] == job_id for j in list_data["jobs"])

    # 4. Synchronously execute job using ResearchService with mocked graph stream
    from unittest.mock import patch
    from app.modules.research.models import Plan, Task

    mock_plan = Plan(
        blog_title="PostgreSQL 17 Query Optimizer Deep Dive",
        audience="Engineers",
        tone="Technical",
        blog_kind="explainer",
        tasks=[
            Task(
                id=1,
                title="Introduction to Optimizer Changes",
                goal="Understand the main improvements",
                bullets=["Cost estimation models", "Query execution plans", "Hardware awareness"],
                target_words=200
            ),
            Task(
                id=2,
                title="B-Tree Deduplication Enhancements",
                goal="Learn how index tuples are deduplicated",
                bullets=["Deduplication mechanism", "Posting list structure", "Benchmark numbers"],
                target_words=300
            ),
        ]
    )

    sample_md = (
        "# PostgreSQL 17 Query Optimizer Deep Dive\n\n"
        "## Introduction to Optimizer Changes\n"
        "PostgreSQL 17 introduces significant enhancements to query planning and cost estimation.\n\n"
        "## B-Tree Deduplication Enhancements\n"
        "Index storage efficiency is improved by deduplicating index tuples seamlessly.\n"
    )

    mock_updates = [
        {"router": {"mode": "closed_book", "needs_research": False}},
        {"orchestrator": {"plan": mock_plan}},
        {"worker": {"sections": [(1, "## Introduction\nPostgres optimizer."), (2, "## Deduplication\nB-tree indexes.")]}},
        {"reducer": {
            "merged_md": sample_md,
            "final": sample_md,
            "plan": mock_plan,
            "sections": [(1, "## Introduction\nPostgres optimizer."), (2, "## Deduplication\nB-tree indexes.")],
            "image_specs": [],
            "evidence": []
        }}
    ]

    db = SessionLocal()
    try:
        service = ResearchService(db)
        with patch("app.modules.research.research_service.research_graph.stream", return_value=iter(mock_updates)):
            service.execute_job_sync(job_id)
    finally:
        db.close()

    # 5. Check Completed Status & Result
    res_resp = client.get(f"/api/v1/research/{job_id}/result")
    assert res_resp.status_code == 200
    res_data = res_resp.json()
    assert res_data["status"] == "COMPLETED"
    assert res_data["markdown_content"] is not None
    assert len(res_data["markdown_content"]) > 50

    # 6. Test Markdown Download
    md_resp = client.get(f"/api/v1/research/{job_id}/download/markdown")
    assert md_resp.status_code == 200
    assert md_resp.headers["content-type"].startswith("text/markdown")
    assert len(md_resp.content) > 50

    # 7. Test ZIP Bundle Download
    bundle_resp = client.get(f"/api/v1/research/{job_id}/download/bundle")
    assert bundle_resp.status_code == 200
    assert bundle_resp.headers["content-type"] == "application/zip"
    assert len(bundle_resp.content) > 50

    # 8. Test High-Res PDF Download
    pdf_resp = client.get(f"/api/v1/research/{job_id}/download/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert len(pdf_resp.content) > 500
    assert pdf_resp.content.startswith(b"%PDF")

    # 9. Test Image Asset Retrieval if image specs exist
    if res_data.get("images"):
        img_name = res_data["images"][0]
        img_resp = client.get(f"/api/v1/research/{job_id}/images/{img_name}")
        assert img_resp.status_code == 200
        assert img_resp.headers["content-type"].startswith("image/")
        assert len(img_resp.content) > 100


def test_youtube_and_research_isolation():
    # Verify that YouTube endpoints do not return research jobs
    yt_list_resp = client.get("/api/v1/jobs?page=1&page_size=50")
    assert yt_list_resp.status_code == 200
    yt_jobs = yt_list_resp.json()["jobs"]
    
    # Verify research endpoint returns research jobs
    res_list_resp = client.get("/api/v1/research?page=1&page_size=50")
    assert res_list_resp.status_code == 200
    res_jobs = res_list_resp.json()["jobs"]

    res_ids = {j["id"] for j in res_jobs}
    yt_ids = {j["id"] for j in yt_jobs}

    # The ID spaces and data models must be completely separate
    intersection = res_ids.intersection(yt_ids)
    assert len(intersection) == 0, f"Found overlapping IDs between modules: {intersection}"

