import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.workers.tasks import run_playlist_job
from app.db.session import SessionLocal
from app.db.repositories.job_repository import PlaylistJobRepository
from app.domain.enums import JobStatus

client = TestClient(app)


@pytest.mark.asyncio
async def test_full_end_to_end_pipeline():
    # 1. Preview Playlist
    preview_resp = client.post(
        "/api/v1/playlists/preview",
        json={"playlist_input": "https://www.youtube.com/playlist?list=PL_DISTRIBUTED_SYSTEMS_2026"}
    )
    assert preview_resp.status_code == 200
    preview = preview_resp.json()
    assert preview["total_videos"] == 4

    # 2. Submit Generation Job
    create_resp = client.post(
        "/api/v1/jobs",
        json={
            "playlist_input": "PL_DISTRIBUTED_SYSTEMS_2026",
            "options": {
                "detail_level": "standard",
                "enable_visuals": True
            }
        }
    )
    assert create_resp.status_code == 201
    job_id = create_resp.json()["id"]

    # 3. Execute job synchronously through task runner
    await run_playlist_job(job_id)

    # 4. Check Job Status in DB
    db = SessionLocal()
    try:
        repo = PlaylistJobRepository(db)
        job = repo.get_by_id(job_id)
        # Completed 3 of 4 (one was private) -> PARTIAL_SUCCESS or COMPLETED
        assert job.status in [JobStatus.COMPLETED.value, JobStatus.PARTIAL_SUCCESS.value]
        assert job.completed_videos >= 3
    finally:
        db.close()

    # 5. Fetch Notes Endpoint
    notes_resp = client.get(f"/api/v1/jobs/{job_id}/notes")
    assert notes_resp.status_code == 200
    notes = notes_resp.json()
    assert len(notes) == 3  # 3 successfully generated videos

    # Check original ordering of generated notes
    positions = [n["original_position"] for n in notes]
    assert positions == sorted(positions)

    # 6. Check Download Endpoint
    download_resp = client.get(f"/api/v1/jobs/{job_id}/download")
    assert download_resp.status_code == 200
    assert download_resp.headers["content-type"] == "application/pdf"
    assert len(download_resp.content) > 1000

