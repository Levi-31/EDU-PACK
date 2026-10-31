import asyncio
import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, "/app" if os.path.exists("/app") else "/Users/sarthakshukla/Desktop/NOTES PROJECT/backend")

from app.db.session import SessionLocal
from app.db.models.job import PlaylistJob
from app.db.models.video import PlaylistVideo
from app.db.models.notes import VideoNotes
from app.domain.schemas.notes import StructuredVideoNotes
from app.domain.schemas.playlist import GenerationOptions
from app.agents.state import VideoGraphItem
from app.domain.enums import VideoProcessingStatus
from app.services.pdf_service import PDFService


async def recompile(job_id: str):
    db = SessionLocal()
    job = db.query(PlaylistJob).filter_by(id=job_id).first()
    if not job:
        print(f"Job {job_id} not found in database.")
        db.close()
        return

    videos = (
        db.query(PlaylistVideo)
        .filter_by(job_id=job_id)
        .order_by(PlaylistVideo.original_position.asc())
        .all()
    )
    print(f"Found {len(videos)} videos for job: '{job.playlist_title}' ({job_id})")

    video_items = []
    for v in videos:
        note_rec = (
            db.query(VideoNotes)
            .filter_by(job_id=job_id, video_id=v.video_id)
            .first()
        )
        notes = None
        visual = None
        if note_rec and note_rec.notes_json:
            try:
                notes = StructuredVideoNotes(**note_rec.notes_json)
                visual = notes.diagram
            except Exception as e:
                print(f"Warning: could not parse notes for video {v.video_id}: {e}")

        # Map processing status safely
        try:
            status = VideoProcessingStatus(v.processing_status) if v.processing_status else VideoProcessingStatus.COMPLETED
        except ValueError:
            status = VideoProcessingStatus.COMPLETED

        item = VideoGraphItem(
            video_id=v.video_id,
            original_position=v.original_position,
            title=v.title,
            channel_title=v.channel_title or job.channel_name,
            description=v.description,
            duration_seconds=v.duration_seconds,
            thumbnail_url=v.thumbnail_url,
            video_url=v.video_url,
            status=status,
            notes=notes,
            visual=visual,
        )
        video_items.append(item)
    db.close()

    options = GenerationOptions(**job.options) if job.options else GenerationOptions()
    pdf_service = PDFService()
    print("Compiling PDF with Playwright 2-pass pagination...")
    artifact = await pdf_service.compile_playlist_pdf(
        job_id=job.id,
        playlist_title=job.playlist_title,
        playlist_url=job.playlist_url,
        channel_name=job.channel_name,
        videos=video_items,
        options=options,
    )
    print(f"\nPDF Generation Successful!")
    print(f"File Name: {artifact.file_name}")
    print(f"Size: {artifact.file_size_bytes} bytes")
    print(f"Absolute Path: {artifact.file_path}")


if __name__ == "__main__":
    target_job = sys.argv[1] if len(sys.argv) > 1 else "6daf16c8-3144-469a-9ca1-c2df6bf9924c"
    asyncio.run(recompile(target_job))

