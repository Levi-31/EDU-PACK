import os
import shutil
from pathlib import Path
from app.db.session import SessionLocal
from app.db.models import PlaylistJob, PlaylistVideo, VideoNotes, VisualAsset, Artifact, JobEvent, Transcript, ResearchJob


def clear_all_data():
    """Wipes all jobs, videos, notes, visual assets, research jobs, and artifacts for a fresh test run."""
    db = SessionLocal()
    try:
        db.query(JobEvent).delete()
        db.query(Artifact).delete()
        db.query(VisualAsset).delete()
        db.query(VideoNotes).delete()
        db.query(Transcript).delete()
        db.query(PlaylistVideo).delete()
        db.query(PlaylistJob).delete()
        db.query(ResearchJob).delete()
        db.commit()
        print("Database tables cleared successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error clearing database: {e}")
    finally:
        db.close()

    # Clear storage artifacts
    storage_dir = Path("/app/storage/artifacts" if os.path.exists("/app") else "storage/artifacts")
    if storage_dir.exists():
        for item in storage_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            else:
                item.unlink(missing_ok=True)
        print("Artifact storage cleared successfully.")


if __name__ == "__main__":
    clear_all_data()
