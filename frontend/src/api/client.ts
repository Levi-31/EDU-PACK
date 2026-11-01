import {
  PlaylistPreviewResponse,
  JobDetailResponse,
  JobListResponse,
  GenerationOptions,
  StructuredVideoNotes,
  CreateResearchJobRequest,
  ResearchJobDetailResponse,
  ResearchJobListResponse,
} from '../types';

const API_BASE = '/api/v1';

export async function previewPlaylist(playlistInput: string): Promise<PlaylistPreviewResponse> {
  const res = await fetch(`${API_BASE}/playlists/preview`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ playlist_input: playlistInput }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to preview playlist');
  }
  return res.json();
}

export async function createJob(
  playlistInput: string,
  options: GenerationOptions,
  titleOverride?: string,
  selectedVideoIds?: string[]
): Promise<JobDetailResponse> {
  const res = await fetch(`${API_BASE}/jobs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      playlist_input: playlistInput,
      options,
      title_override: titleOverride,
      selected_video_ids: selectedVideoIds,
    }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to start generation job');
  }
  return res.json();
}

export async function getJob(jobId: string): Promise<JobDetailResponse> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}`);
  if (!res.ok) {
    throw new Error('Failed to retrieve job details');
  }
  return res.json();
}

export async function listJobs(page = 1, pageSize = 20): Promise<JobListResponse> {
  const res = await fetch(`${API_BASE}/jobs?page=${page}&page_size=${pageSize}`);
  if (!res.ok) {
    throw new Error('Failed to fetch job history');
  }
  return res.json();
}

export async function retryJob(jobId: string): Promise<JobDetailResponse> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}/retry`, { method: 'POST' });
  if (!res.ok) {
    throw new Error('Failed to retry job');
  }
  return res.json();
}

export async function cancelJob(jobId: string): Promise<JobDetailResponse> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}/cancel`, { method: 'POST' });
  if (!res.ok) {
    throw new Error('Failed to cancel job');
  }
  return res.json();
}

export async function getJobNotes(jobId: string): Promise<StructuredVideoNotes[]> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}/notes`);
  if (!res.ok) {
    throw new Error('Failed to fetch generated notes');
  }
  return res.json();
}

export function getDownloadUrl(jobId: string): string {
  return `${API_BASE}/jobs/${jobId}/download`;
}

// ----------------------------------------------------
// Research Module Client (Levi-31/Research-Tool API)
// ----------------------------------------------------

export async function createResearchJob(
  request: CreateResearchJobRequest
): Promise<ResearchJobDetailResponse> {
  const res = await fetch(`${API_BASE}/research/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to start research job');
  }
  return res.json();
}

export async function getResearchJob(jobId: string): Promise<ResearchJobDetailResponse> {
  const res = await fetch(`${API_BASE}/research/${jobId}`);
  if (!res.ok) {
    throw new Error('Failed to retrieve research job details');
  }
  return res.json();
}

export async function listResearchJobs(
  page = 1,
  pageSize = 20
): Promise<ResearchJobListResponse> {
  const res = await fetch(`${API_BASE}/research?page=${page}&page_size=${pageSize}`);
  if (!res.ok) {
    throw new Error('Failed to fetch research history');
  }
  return res.json();
}

export function getResearchMarkdownUrl(jobId: string): string {
  return `${API_BASE}/research/${jobId}/download/markdown`;
}

export function getResearchBundleUrl(jobId: string): string {
  return `${API_BASE}/research/${jobId}/download/bundle`;
}

export function getResearchPdfUrl(jobId: string): string {
  return `${API_BASE}/research/${jobId}/download/pdf`;
}

export function getResearchImageUrl(jobId: string, filename: string): string {
  return `${API_BASE}/research/${jobId}/images/${filename}`;
}


