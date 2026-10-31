import asyncio
import os
import sys

sys.path.insert(0, "/app" if os.path.exists("/app") else "/Users/sarthakshukla/Desktop/NOTES PROJECT/backend")

from app.db.session import SessionLocal
from app.db.models.notes import VideoNotes
from app.db.models.job import PlaylistJob
from app.db.models.video import PlaylistVideo
from app.domain.schemas.notes import StructuredVideoNotes
from app.agents.notes_agent import TechnicalNotesAgent
from app.services.pdf_service import PDFService
from app.domain.schemas.playlist import GenerationOptions
from app.agents.state import VideoGraphItem
from app.domain.enums import VideoProcessingStatus


async def main():
    job_id = "9f1da9ff-acbf-4bd7-b8ac-b63b73b5a7e2"
    db = SessionLocal()
    job = db.query(PlaylistJob).filter_by(id=job_id).first()
    if not job:
        print("Job not found!")
        db.close()
        return

    notes_records = db.query(VideoNotes).filter_by(job_id=job_id).all()
    print(f"Found {len(notes_records)} notes records for job {job_id}")

    notes_agent = TechnicalNotesAgent(None)

    for nr in notes_records:
        if not nr.notes_json:
            continue
        try:
            notes = StructuredVideoNotes(**nr.notes_json)
        except Exception as e:
            print(f"Parsing error for {nr.video_id}: {e}")
            continue

        # 1. Clean salutations and placeholders across all fields
        notes_agent._clean_notes_placeholders(notes)

        # 2. Fix broken Mermaid diagram in KrXBcokM3Tc if present
        if nr.video_id == "KrXBcokM3Tc" or "Long Term Memory" in notes.video_title:
            valid_mermaid = """flowchart TD
    subgraph User_Interaction
        User["User Input"] --> Router["Agent / Graph Router"]
    end
    subgraph LangGraph_Runtime
        Router --> NodeA["Current Turn Execution"]
        NodeA --> MemRead["Memory Store Retrieval"]
        MemRead --> Context["Enriched LLM Context"]
        Context --> NodeB["Response Generation"]
        NodeB --> MemWrite["Memory Store Update"]
    end
    subgraph Persistence_Layer
        MemRead -.->|"Read Namespaced Memories"| LongTermStore[("Long-Term Store / PostgreSQL")]
        MemWrite -.->|"Persist New Facts / State"| LongTermStore
    end
    NodeB --> Output["Final Response to User"]"""

            if notes.visual:
                notes.visual.mermaid_code = valid_mermaid
                notes.visual.title = "Long-Term Memory in LangGraph Architecture"
                notes.visual.description = "Architectural interaction flow between conversational turns, namespaced long-term store, and LangGraph execution nodes."
                notes.visual.is_generated = True

            # Also check sections
            for s in notes.sections:
                if getattr(s, "visual", None) and s.visual:
                    s.visual.mermaid_code = valid_mermaid
                    s.visual.title = "Long-Term Memory in LangGraph Architecture"
                    s.visual.is_generated = True

        # Save back to database
        nr.notes_json = notes.model_dump()
        db.commit()
        print(f"Updated and saved clean notes for video: {nr.video_id} ({notes.video_title})")

    # Now recompile the PDF using the updated notes
    videos = (
        db.query(PlaylistVideo)
        .filter_by(job_id=job_id)
        .order_by(PlaylistVideo.original_position.asc())
        .all()
    )

    video_items = []
    for v in videos:
        note_rec = db.query(VideoNotes).filter_by(job_id=job_id, video_id=v.video_id).first()
        notes = None
        visual = None
        if note_rec and note_rec.notes_json:
            notes = StructuredVideoNotes(**note_rec.notes_json)
            visual = getattr(notes, "visual", None)

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

    job_title = job.playlist_title
    job_url = job.playlist_url
    job_channel = job.channel_name
    job_options = job.options
    db.close()

    options = GenerationOptions(**job_options) if job_options else GenerationOptions()
    pdf_service = PDFService()
    print("Recompiling PDF for job 9f1da9ff...")
    artifact = await pdf_service.compile_playlist_pdf(
        job_id=job_id,
        playlist_title=job_title,
        playlist_url=job_url,
        channel_name=job_channel,
        videos=video_items,
        options=options,
    )
    print("Compilation complete!")
    print(f"File Name: {artifact.file_name}")
    print(f"File Size: {artifact.file_size_bytes} bytes")
    print(f"Path: {artifact.file_path}")


if __name__ == "__main__":
    asyncio.run(main())
