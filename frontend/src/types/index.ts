export type JobStatus =
  | 'QUEUED'
  | 'FETCHING_PLAYLIST'
  | 'PLANNING'
  | 'FETCHING_TRANSCRIPTS'
  | 'GENERATING_NOTES'
  | 'GENERATING_VISUALS'
  | 'REVIEWING_NOTES'
  | 'RENDERING_PDF'
  | 'COMPLETED'
  | 'PARTIAL_SUCCESS'
  | 'FAILED'
  | 'CANCELLED';

export type VideoProcessingStatus =
  | 'PENDING'
  | 'FETCHING_TRANSCRIPT'
  | 'TRANSCRIPT_FAILED'
  | 'GENERATING_NOTES'
  | 'GENERATING_VISUALS'
  | 'REVIEWING'
  | 'COMPLETED'
  | 'FAILED'
  | 'SKIPPED';

export type TranscriptStatus =
  | 'NOT_FETCHED'
  | 'AVAILABLE'
  | 'UNAVAILABLE'
  | 'DISABLED'
  | 'FAILED'
  | 'USER_PROVIDED';

export type NoteDetailLevel = 'concise' | 'standard' | 'comprehensive';
export type PDFTheme = 'editorial_navy' | 'technical_slate' | 'clean_minimal';

export interface GenerationOptions {
  detail_level: NoteDetailLevel;
  transcript_language: string;
  enable_visuals: boolean;
  pdf_theme: PDFTheme;
  max_revisions: number;
}

export interface PlaylistItemPreview {
  video_id: string;
  original_position: number;
  title: string;
  channel_title?: string;
  description?: string;
  thumbnail_url?: string;
  duration_seconds?: number;
  duration_formatted?: string;
  video_url: string;
  is_available: boolean;
  status_note?: string;
}

export interface PlaylistPreviewResponse {
  playlist_id: string;
  title: string;
  description?: string;
  channel_name?: string;
  thumbnail_url?: string;
  total_videos: number;
  available_videos_count: number;
  playlist_url: string;
  videos: PlaylistItemPreview[];
  is_mock: boolean;
}

export interface VideoStatusSchema {
  video_id: string;
  original_position: number;
  title: string;
  channel_title?: string;
  thumbnail_url?: string;
  duration_formatted?: string;
  status: VideoProcessingStatus;
  transcript_status: TranscriptStatus;
  error_message?: string;
  has_notes: boolean;
  has_visual: boolean;
}

export interface ArtifactSchema {
  id: string;
  job_id: string;
  artifact_type: string;
  file_name: string;
  file_path: string;
  mime_type: string;
  file_size_bytes: number;
  checksum_sha256: string;
  created_at: string;
  download_url: string;
  is_valid: boolean;
}

export interface JobDetailResponse {
  id: string;
  playlist_id: string;
  playlist_url: string;
  playlist_title: string;
  status: JobStatus;
  progress_percentage: number;
  current_stage: string;
  options: GenerationOptions;
  total_videos: number;
  completed_videos: number;
  failed_videos: number;
  skipped_videos: number;
  error_summary?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  artifact?: ArtifactSchema;
  videos: VideoStatusSchema[];
  is_mock: boolean;
}

export interface JobListResponse {
  jobs: JobDetailResponse[];
  total: number;
  page: number;
  page_size: number;
}

export interface JobEvent {
  job_id: string;
  video_id?: string;
  stage: string;
  message: string;
  progress: number;
  timestamp?: string;
  data?: Record<string, unknown>;
}

export interface CodeSnippet {
  language: string;
  code: string;
  caption?: string;
}

export interface CalloutBox {
  kind: 'note' | 'tip' | 'important' | 'warning' | 'caution';
  title: string;
  content: string;
}

export interface Flashcard {
  question: string;
  answer: string;
}

export interface GlossaryItem {
  term: string;
  definition: string;
}

export interface VisualAsset {
  video_id: string;
  section_index?: number;
  asset_type: string;
  title: string;
  description: string;
  mermaid_code?: string;
  image_url?: string;
  mime_type: string;
  is_generated: boolean;
  decision_reason?: string;
}

export interface NoteTopicSection {
  title: string;
  markdown_content: string;
  code_snippets: CodeSnippet[];
  callouts: CalloutBox[];
  visual?: VisualAsset;
  evidence_segment_ids: string[];
  timestamp_seconds?: number;
  timestamped_watch_url?: string;
}

export interface StructuredVideoNotes {
  schema_version: string;
  video_id: string;
  video_title: string;
  video_url: string;
  channel_name?: string;
  duration_seconds?: number;
  thumbnail_url?: string;
  original_position: number;
  executive_summary: string;
  key_takeaways: string[];
  learning_objectives: string[];
  prerequisites: string[];
  core_concepts: string[];
  sections: NoteTopicSection[];
  architecture_and_workflows?: string;
  trade_offs_and_decisions: string[];
  pitfalls_and_limitations: string[];
  glossary: GlossaryItem[];
  revision_sheet: string;
  flashcards: Flashcard[];
  is_mock: boolean;
}
