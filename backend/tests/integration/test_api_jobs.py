from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_preview_playlist_endpoint():
    response = client.post(
        "/api/v1/playlists/preview",
        json={"playlist_input": "PL_DISTRIBUTED_SYSTEMS_2026"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["playlist_id"] == "PL_DISTRIBUTED_SYSTEMS_2026"
    assert len(data["videos"]) == 4
    # Check ordering
    assert [v["original_position"] for v in data["videos"]] == [0, 1, 2, 3]


def test_create_and_get_job():
    # 1. Create job
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
    job = create_resp.json()
    job_id = job["id"]
    assert job["total_videos"] == 4

    # 2. Retrieve job by ID
    get_resp = client.get(f"/api/v1/jobs/{job_id}")
    assert get_resp.status_code == 200
    job_detail = get_resp.json()
    assert job_detail["id"] == job_id
    assert len(job_detail["videos"]) == 4

    # 3. List jobs
    list_resp = client.get("/api/v1/jobs")
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert list_data["total"] >= 1
