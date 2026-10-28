from typing import List, Optional
from app.domain.schemas.playlist import PlaylistItemPreview, PlaylistPreviewResponse
from app.integrations.youtube.client import YouTubeClientInterface, format_duration
from app.integrations.youtube.parser import extract_playlist_id, construct_playlist_url, construct_video_url


class MockYouTubeClient(YouTubeClientInterface):
    """
    High-fidelity mock YouTube client for demo mode and automated testing.
    Provides multi-video ordered playlists, duration metadata, and deliberate edge cases
    (e.g., unavailable/private video) to test resilience without API keys.
    """

    DEFAULT_PLAYLIST_ID = "PL_DISTRIBUTED_SYSTEMS_2026"

    SAMPLE_VIDEOS = [
        {
            "video_id": "vid_dist_001",
            "title": "1. Distributed Consensus: Paxos, Raft, and State Machine Replication",
            "channel_title": "MIT Distributed Systems Lab",
            "description": "Comprehensive technical lecture examining distributed consensus protocols, quorum slices, leader election, log replication, and split-brain recovery.",
            "thumbnail_url": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800&auto=format&fit=crop",
            "duration_seconds": 1245,  # 20:45
            "is_available": True,
            "status_note": None
        },
        {
            "video_id": "vid_dist_002",
            "title": "2. Event Sourcing and CQRS: High-Throughput System Design",
            "channel_title": "MIT Distributed Systems Lab",
            "description": "Deep-dive into event-driven persistence, append-only immutable event streams, projections, eventual consistency, and compensation workflows.",
            "thumbnail_url": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800&auto=format&fit=crop",
            "duration_seconds": 1560,  # 26:00
            "is_available": True,
            "status_note": None
        },
        {
            "video_id": "vid_dist_003",
            "title": "3. [Private Video - Restricted Lecture]",
            "channel_title": "MIT Distributed Systems Lab",
            "description": "This lecture video was set to private by the uploader.",
            "thumbnail_url": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&auto=format&fit=crop",
            "duration_seconds": 0,
            "is_available": False,
            "status_note": "Video is private or restricted by channel owner"
        },
        {
            "video_id": "vid_dist_004",
            "title": "4. Log-Structured Storage and Kafka Partitioning Architecture",
            "channel_title": "MIT Distributed Systems Lab",
            "description": "Internal mechanics of distributed commit logs, zero-copy socket transfers via sendfile, partition rebalancing, and exactly-once semantics.",
            "thumbnail_url": "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=800&auto=format&fit=crop",
            "duration_seconds": 1820,  # 30:20
            "is_available": True,
            "status_note": None
        }
    ]

    async def fetch_playlist(self, playlist_input: str) -> PlaylistPreviewResponse:
        playlist_id = extract_playlist_id(playlist_input)
        
        # Check if requesting pagination test playlist
        if "pagination" in playlist_id.lower() or "multipage" in playlist_id.lower():
            return self._build_paginated_playlist(playlist_id)

        videos: List[PlaylistItemPreview] = []
        available_count = 0
        for idx, item in enumerate(self.SAMPLE_VIDEOS):
            dur_sec = item["duration_seconds"]
            if item["is_available"]:
                available_count += 1
            videos.append(
                PlaylistItemPreview(
                    video_id=item["video_id"],
                    original_position=idx,
                    title=item["title"],
                    channel_title=item["channel_title"],
                    description=item["description"],
                    thumbnail_url=item["thumbnail_url"],
                    duration_seconds=dur_sec,
                    duration_formatted=format_duration(dur_sec),
                    video_url=construct_video_url(item["video_id"]),
                    is_available=item["is_available"],
                    status_note=item["status_note"]
                )
            )

        return PlaylistPreviewResponse(
            playlist_id=playlist_id,
            title="Distributed Systems & High-Throughput Architecture Masterclass",
            description="Production-grade technical curriculum on distributed consensus, event-driven architecture, and storage engine design.",
            channel_name="MIT Distributed Systems Lab",
            thumbnail_url="https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800&auto=format&fit=crop",
            total_videos=len(videos),
            available_videos_count=available_count,
            playlist_url=construct_playlist_url(playlist_id),
            videos=videos,
            is_mock=True
        )

    def _build_paginated_playlist(self, playlist_id: str) -> PlaylistPreviewResponse:
        """Generates 55 videos to test multi-page retrieval (simulating 50-item API page boundary)"""
        videos: List[PlaylistItemPreview] = []
        for i in range(55):
            vid = f"paged_vid_{i:03d}"
            dur = 600 + (i * 30)
            videos.append(
                PlaylistItemPreview(
                    video_id=vid,
                    original_position=i,
                    title=f"Advanced Microservices Module {i + 1:02d}: Topic {i + 1}",
                    channel_title="Cloud Native Engineering",
                    description=f"Curriculum module {i + 1} detailing container orchestration and service mesh patterns.",
                    thumbnail_url="https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800&auto=format&fit=crop",
                    duration_seconds=dur,
                    duration_formatted=format_duration(dur),
                    video_url=construct_video_url(vid),
                    is_available=True,
                    status_note=None
                )
            )
        return PlaylistPreviewResponse(
            playlist_id=playlist_id,
            title="Large Scale Cloud Architecture (55 Video Paginated Series)",
            description="Extensive 55-part engineering series spanning multiple API pages.",
            channel_name="Cloud Native Engineering",
            thumbnail_url="https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800&auto=format&fit=crop",
            total_videos=len(videos),
            available_videos_count=len(videos),
            playlist_url=construct_playlist_url(playlist_id),
            videos=videos,
            is_mock=True
        )

