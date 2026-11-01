import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Navbar, AppModule, YouTubeNavTab, ResearchNavTab } from './components/Navbar';
import { PlaylistInput } from './components/PlaylistInput';
import { PlaylistPreview } from './components/PlaylistPreview';
import { JobProgress } from './components/JobProgress';
import { NotesViewer } from './components/NotesViewer';
import { JobHistory } from './components/JobHistory';
import { ResearchLanding } from './components/research/ResearchLanding';
import { ResearchProgress } from './components/research/ResearchProgress';
import { ResearchResults } from './components/research/ResearchResults';
import { ResearchHistory } from './components/research/ResearchHistory';
import {
  previewPlaylist,
  createJob,
  getJob,
  listJobs,
  retryJob,
  getJobNotes,
  createResearchJob,
  getResearchJob,
  listResearchJobs,
} from './api/client';
import {
  PlaylistPreviewResponse,
  GenerationOptions,
  JobDetailResponse,
  StructuredVideoNotes,
  CreateResearchJobRequest,
  ResearchJobDetailResponse,
} from './types';
import { useJobProgress } from './hooks/useJobProgress';

export function App() {
  const queryClient = useQueryClient();

  // 1. Dual-Module Route Synchronization
  const [currentModule, setCurrentModuleState] = useState<AppModule>(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const mod = params.get('module');
      if (mod === 'research' || mod === 'youtube') {
        return mod;
      }
      if (window.location.hash === '#research') return 'research';
    }
    return 'youtube';
  });

  const setCurrentModule = (mod: AppModule) => {
    setCurrentModuleState(mod);
    if (typeof window !== 'undefined') {
      const url = new URL(window.location.href);
      url.searchParams.set('module', mod);
      window.history.pushState({ module: mod }, '', url.toString());
    }
  };

  useEffect(() => {
    const handlePopState = () => {
      const params = new URLSearchParams(window.location.search);
      const mod = params.get('module');
      if (mod === 'research' || mod === 'youtube') {
        setCurrentModuleState(mod);
      } else if (window.location.hash === '#research') {
        setCurrentModuleState('research');
      } else {
        setCurrentModuleState('youtube');
      }
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  // ----------------------------------------------------
  // YouTube Module State
  // ----------------------------------------------------
  const [ytTab, setYtTab] = useState<YouTubeNavTab>('create');
  const [previewData, setPreviewData] = useState<PlaylistPreviewResponse | null>(null);
  const [activeYtJobId, setActiveYtJobId] = useState<string | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);

  const previewMutation = useMutation({
    mutationFn: previewPlaylist,
    onSuccess: (data) => {
      setPreviewData(data);
      setPreviewError(null);
    },
    onError: (err: Error) => {
      setPreviewError(err.message);
    },
  });

  const startYtJobMutation = useMutation({
    mutationFn: ({
      playlistInput,
      options,
      selectedVideoIds,
    }: {
      playlistInput: string;
      options: GenerationOptions;
      selectedVideoIds?: string[];
    }) => createJob(playlistInput, options, undefined, selectedVideoIds),
    onSuccess: (job: JobDetailResponse) => {
      setActiveYtJobId(job.id);
      setYtTab('progress');
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
    onError: (err: Error) => {
      alert(`Error starting generation: ${err.message}`);
    },
  });

  const { data: activeYtJob, refetch: refetchYtJob } = useQuery({
    queryKey: ['job', activeYtJobId],
    queryFn: () => getJob(activeYtJobId!),
    enabled: !!activeYtJobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status && ['COMPLETED', 'PARTIAL_SUCCESS', 'FAILED', 'CANCELLED'].includes(status)) {
        return false;
      }
      return 2000;
    },
  });

  const { data: ytJobsHistory, isLoading: isLoadingYtHistory, refetch: refetchYtHistory } = useQuery({
    queryKey: ['jobs'],
    queryFn: () => listJobs(1, 30),
  });

  const { data: activeNotes } = useQuery<StructuredVideoNotes[]>({
    queryKey: ['notes', activeYtJobId],
    queryFn: () => getJobNotes(activeYtJobId!),
    enabled: !!activeYtJobId && (activeYtJob?.status === 'COMPLETED' || activeYtJob?.status === 'PARTIAL_SUCCESS'),
  });

  const { events: ytEvents, latestProgress: ytLatestProgress, currentStage: ytCurrentStage, isFinished: isYtFinished } = useJobProgress(
    activeYtJobId,
    () => {
      setTimeout(() => {
        refetchYtJob();
        queryClient.invalidateQueries({ queryKey: ['notes', activeYtJobId] });
        queryClient.invalidateQueries({ queryKey: ['job', activeYtJobId] });
        queryClient.invalidateQueries({ queryKey: ['jobs'] });
      }, 300);
    }
  );

  const retryYtMutation = useMutation({
    mutationFn: (jobId: string) => retryJob(jobId),
    onSuccess: () => {
      refetchYtJob();
    },
  });

  const isYtRunning = activeYtJob ? ['QUEUED', 'PROCESSING'].includes(activeYtJob.status) : false;

  // ----------------------------------------------------
  // Research Module State (Levi-31/Research-Tool)
  // ----------------------------------------------------
  const [researchTab, setResearchTab] = useState<ResearchNavTab>('landing');
  const [activeResearchJobId, setActiveResearchJobId] = useState<string | null>(null);

  const startResearchMutation = useMutation({
    mutationFn: (req: CreateResearchJobRequest) => createResearchJob(req),
    onSuccess: (job: ResearchJobDetailResponse) => {
      setActiveResearchJobId(job.id);
      setResearchTab('progress');
      queryClient.invalidateQueries({ queryKey: ['research_jobs'] });
    },
    onError: (err: Error) => {
      alert(`Error starting research: ${err.message}`);
    },
  });

  const { data: activeResearchJob, refetch: refetchResearchJob } = useQuery({
    queryKey: ['research_job', activeResearchJobId],
    queryFn: () => getResearchJob(activeResearchJobId!),
    enabled: !!activeResearchJobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status && ['COMPLETED', 'FAILED'].includes(status)) {
        return false;
      }
      return 1500;
    },
  });

  const { data: researchJobsHistory, isLoading: isLoadingResearchHistory, refetch: refetchResearchHistory } = useQuery({
    queryKey: ['research_jobs'],
    queryFn: () => listResearchJobs(1, 30),
  });

  const isResearchRunning = activeResearchJob
    ? ['QUEUED', 'RUNNING'].includes(activeResearchJob.status)
    : false;

  return (
    <div className="min-h-screen bg-surface text-on-surface flex flex-col font-sans selection:bg-primary-container selection:text-on-primary-container">
      {/* Dual-Mode Navbar */}
      <Navbar
        currentModule={currentModule}
        setCurrentModule={setCurrentModule}
        ytTab={ytTab}
        setYtTab={setYtTab}
        activeYtJobId={activeYtJobId}
        hasActiveYtRunning={isYtRunning}
        researchTab={researchTab}
        setResearchTab={setResearchTab}
        activeResearchJobId={activeResearchJobId}
        hasActiveResearchRunning={isResearchRunning}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* ==================================================== */}
        {/* MODULE A: RESEARCH (Levi-31/Research-Tool Engine)   */}
        {/* ==================================================== */}
        {currentModule === 'research' && (
          <>
            {researchTab === 'landing' && (
              <ResearchLanding
                onStartResearch={(req) => startResearchMutation.mutate(req)}
                isLoading={startResearchMutation.isPending}
                recentJobs={researchJobsHistory?.jobs || []}
                onSelectJob={(id) => {
                  setActiveResearchJobId(id);
                  const selected = researchJobsHistory?.jobs.find((j) => j.id === id);
                  if (selected?.status === 'COMPLETED') {
                    setResearchTab('results');
                  } else {
                    setResearchTab('progress');
                  }
                }}
              />
            )}

            {researchTab === 'progress' && (
              activeResearchJob ? (
                <ResearchProgress
                  job={activeResearchJob}
                  onViewResults={() => setResearchTab('results')}
                  onBackToInput={() => setResearchTab('landing')}
                />
              ) : (
                <div className="max-w-md mx-auto py-16 text-center space-y-3 font-mono text-xs text-on-surface-variant">
                  <div>No active research job selected.</div>
                  <button
                    onClick={() => setResearchTab('landing')}
                    className="px-4 py-2 rounded-xl bg-primary-container text-on-primary-container font-sans text-xs font-semibold"
                  >
                    Initiate New Research
                  </button>
                </div>
              )
            )}

            {researchTab === 'results' && (
              activeResearchJob ? (
                <ResearchResults
                  job={activeResearchJob}
                  onBack={() => setResearchTab('landing')}
                />
              ) : (
                <div className="max-w-md mx-auto py-16 text-center space-y-3 font-mono text-xs text-on-surface-variant">
                  <div>No research article selected.</div>
                  <button
                    onClick={() => setResearchTab('landing')}
                    className="px-4 py-2 rounded-xl bg-primary-container text-on-primary-container font-sans text-xs font-semibold"
                  >
                    Return to Research Form
                  </button>
                </div>
              )
            )}

            {researchTab === 'history' && (
              <ResearchHistory
                jobs={researchJobsHistory?.jobs || []}
                isLoading={isLoadingResearchHistory}
                onSelectJob={(id) => {
                  setActiveResearchJobId(id);
                  const selected = researchJobsHistory?.jobs.find((j) => j.id === id);
                  if (selected?.status === 'COMPLETED') {
                    setResearchTab('results');
                  } else {
                    setResearchTab('progress');
                  }
                }}
                onRefresh={() => refetchResearchHistory()}
              />
            )}
          </>
        )}

        {/* ==================================================== */}
        {/* MODULE B: YOUTUBE NOTES (Single Video & Playlist)   */}
        {/* ==================================================== */}
        {currentModule === 'youtube' && (
          <>
            {ytTab === 'create' && (
              <>
                {previewData ? (
                  <PlaylistPreview
                    preview={previewData}
                    onBack={() => setPreviewData(null)}
                    onStartJob={(options, selectedVideoIds) => {
                      startYtJobMutation.mutate({
                        playlistInput: previewData.playlist_url,
                        options,
                        selectedVideoIds,
                      });
                    }}
                    isStarting={startYtJobMutation.isPending}
                  />
                ) : (
                  <PlaylistInput
                    onFetchPreview={(input) => previewMutation.mutate(input)}
                    isLoading={previewMutation.isPending}
                    errorMessage={previewError}
                  />
                )}
              </>
            )}

            {ytTab === 'progress' && (
              activeYtJob ? (
                <JobProgress
                  job={activeYtJob}
                  events={ytEvents}
                  latestProgress={ytLatestProgress}
                  currentStage={ytCurrentStage}
                  isFinished={isYtFinished}
                  onRetry={() => retryYtMutation.mutate(activeYtJob.id)}
                  onViewNotes={() => {
                    queryClient.invalidateQueries({ queryKey: ['notes', activeYtJob.id] });
                    queryClient.invalidateQueries({ queryKey: ['job', activeYtJob.id] });
                    refetchYtJob();
                    setYtTab('notes');
                  }}
                  isRetrying={retryYtMutation.isPending}
                />
              ) : (
                <div className="max-w-md mx-auto py-16 text-center space-y-3 font-mono text-xs text-on-surface-variant">
                  <div>No active generation pipeline selected.</div>
                  <button
                    onClick={() => setYtTab('create')}
                    className="px-4 py-2 rounded-xl bg-primary-container text-on-primary-container font-sans text-xs font-semibold"
                  >
                    Start New Pipeline
                  </button>
                </div>
              )
            )}

            {ytTab === 'notes' && (
              activeYtJobId ? (
                <NotesViewer
                  jobId={activeYtJobId}
                  notes={activeNotes || []}
                  onBackToDashboard={() => setYtTab('create')}
                />
              ) : (
                <div className="max-w-md mx-auto py-16 text-center space-y-3 font-mono text-xs text-on-surface-variant">
                  <div>No study notes selected.</div>
                  <button
                    onClick={() => setYtTab('create')}
                    className="px-4 py-2 rounded-xl bg-primary-container text-on-primary-container font-sans text-xs font-semibold"
                  >
                    Go to Generator
                  </button>
                </div>
              )
            )}

            {ytTab === 'history' && (
              <JobHistory
                jobs={ytJobsHistory?.jobs || []}
                isLoading={isLoadingYtHistory}
                onSelectJob={(id) => {
                  setActiveYtJobId(id);
                  const selected = ytJobsHistory?.jobs.find((j) => j.id === id);
                  if (selected?.status === 'COMPLETED' || selected?.status === 'PARTIAL_SUCCESS') {
                    queryClient.invalidateQueries({ queryKey: ['notes', id] });
                    setYtTab('notes');
                  } else {
                    setYtTab('progress');
                  }
                }}
                onRefresh={() => refetchYtHistory()}
              />
            )}
          </>
        )}
      </main>

      <footer className="border-t border-outline-variant/20 py-6 text-xs text-outline">
        <div className="max-w-6xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-on-surface">◇ Synthara</span>
            <span>&mdash;</span>
            <span>Research &amp; Learning Workspace</span>
          </div>
          <div className="text-on-surface-variant/70">
            Autonomous Research &bull; YouTube Study Notes
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
