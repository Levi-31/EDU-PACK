import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Navbar, NavTabType } from './components/Navbar';
import { PlaylistInput } from './components/PlaylistInput';
import { PlaylistPreview } from './components/PlaylistPreview';
import { JobProgress } from './components/JobProgress';
import { NotesViewer } from './components/NotesViewer';
import { JobHistory } from './components/JobHistory';
import {
  previewPlaylist,
  createJob,
  getJob,
  listJobs,
  retryJob,
  getJobNotes
} from './api/client';
import {
  PlaylistPreviewResponse,
  GenerationOptions,
  JobDetailResponse,
  StructuredVideoNotes
} from './types';
import { useJobProgress } from './hooks/useJobProgress';

export function App() {
  const queryClient = useQueryClient();
  const [currentTab, setCurrentTab] = useState<NavTabType>('create');
  const [previewData, setPreviewData] = useState<PlaylistPreviewResponse | null>(null);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);

  // 1. Fetch Playlist Preview Mutation
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

  // 2. Start Job Mutation
  const startJobMutation = useMutation({
    mutationFn: ({ playlistInput, options }: { playlistInput: string; options: GenerationOptions }) =>
      createJob(playlistInput, options),
    onSuccess: (job: JobDetailResponse) => {
      setActiveJobId(job.id);
      setCurrentTab('progress');
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
    onError: (err: Error) => {
      alert(`Error starting generation: ${err.message}`);
    },
  });

  // 3. Active Job Query
  const { data: activeJob, refetch: refetchJob } = useQuery({
    queryKey: ['job', activeJobId],
    queryFn: () => getJob(activeJobId!),
    enabled: !!activeJobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status && ['COMPLETED', 'PARTIAL_SUCCESS', 'FAILED', 'CANCELLED'].includes(status)) {
        return false;
      }
      return 2000;
    },
  });

  // 4. Job History Query
  const { data: jobsHistory, isLoading: isLoadingHistory, refetch: refetchHistory } = useQuery({
    queryKey: ['jobs'],
    queryFn: () => listJobs(1, 30),
  });

  // 5. Notes Query
  const { data: activeNotes } = useQuery<StructuredVideoNotes[]>({
    queryKey: ['notes', activeJobId],
    queryFn: () => getJobNotes(activeJobId!),
    enabled: !!activeJobId && (activeJob?.status === 'COMPLETED' || activeJob?.status === 'PARTIAL_SUCCESS'),
  });

  // 6. SSE Progress Hook
  const { events, latestProgress, currentStage, isFinished } = useJobProgress(
    activeJobId,
    () => {
      refetchJob();
      queryClient.invalidateQueries({ queryKey: ['notes', activeJobId] });
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    }
  );

  // 7. Retry Mutation
  const retryMutation = useMutation({
    mutationFn: (jobId: string) => retryJob(jobId),
    onSuccess: () => {
      refetchJob();
    },
  });

  const isJobRunning = activeJob ? ['QUEUED', 'PROCESSING'].includes(activeJob.status) : false;

  return (
    <div className="min-h-screen bg-surface text-on-surface flex flex-col font-sans selection:bg-primary-container selection:text-on-primary-container">
      <Navbar
        currentTab={currentTab}
        setCurrentTab={(tab) => {
          if (tab === 'create' && activeJobId && !previewData && currentTab === 'create') {
            setCurrentTab('progress');
          } else {
            setCurrentTab(tab);
          }
        }}
        activeJobId={activeJobId}
        hasActiveJobRunning={isJobRunning}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {currentTab === 'create' && (
          <>
            {previewData ? (
              <PlaylistPreview
                preview={previewData}
                onBack={() => setPreviewData(null)}
                onStartJob={(options) => {
                  startJobMutation.mutate({
                    playlistInput: previewData.playlist_url,
                    options,
                  });
                }}
                isStarting={startJobMutation.isPending}
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

        {currentTab === 'progress' && (
          activeJob ? (
            <JobProgress
              job={activeJob}
              events={events}
              latestProgress={latestProgress}
              currentStage={currentStage}
              isFinished={isFinished}
              onRetry={() => retryMutation.mutate(activeJob.id)}
              onViewNotes={() => setCurrentTab('notes')}
              isRetrying={retryMutation.isPending}
            />
          ) : (
            <div className="max-w-md mx-auto py-16 text-center space-y-3 font-mono text-xs text-on-surface-variant">
              <div>No active generation pipeline selected.</div>
              <button
                onClick={() => setCurrentTab('create')}
                className="px-4 py-2 rounded-xl bg-primary-container text-on-primary-container font-sans text-xs font-semibold"
              >
                Start New Pipeline
              </button>
            </div>
          )
        )}

        {currentTab === 'notes' && (
          activeJobId ? (
            <NotesViewer
              jobId={activeJobId}
              notes={activeNotes || []}
              onBackToDashboard={() => setCurrentTab('create')}
            />
          ) : (
            <div className="max-w-md mx-auto py-16 text-center space-y-3 font-mono text-xs text-on-surface-variant">
              <div>No study notes selected.</div>
              <button
                onClick={() => setCurrentTab('create')}
                className="px-4 py-2 rounded-xl bg-primary-container text-on-primary-container font-sans text-xs font-semibold"
              >
                Go to Generator
              </button>
            </div>
          )
        )}

        {currentTab === 'history' && (
          <JobHistory
            jobs={jobsHistory?.jobs || []}
            isLoading={isLoadingHistory}
            onSelectJob={(id) => {
              setActiveJobId(id);
              setCurrentTab('progress');
            }}
            onRefresh={() => refetchHistory()}
          />
        )}
      </main>

      <footer className="border-t border-outline-variant/20 py-4 text-xs text-outline">
        <div className="max-w-6xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>Playlist Scholar</span>
          <span>Autonomous YouTube Study Guide Platform</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
