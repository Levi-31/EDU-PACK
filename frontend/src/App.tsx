import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Navbar } from './components/Navbar';
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
  const [currentTab, setCurrentTab] = useState<'create' | 'progress' | 'notes' | 'history'>('create');
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

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar
        currentTab={currentTab === 'progress' ? 'create' : currentTab}
        setCurrentTab={(tab) => {
          if (tab === 'create' && activeJobId && !previewData) {
            setCurrentTab('progress');
          } else {
            setCurrentTab(tab);
          }
        }}
        activeJobId={activeJobId}
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

        {currentTab === 'progress' && activeJob && (
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
        )}

        {currentTab === 'notes' && activeJobId && (
          <NotesViewer
            jobId={activeJobId}
            notes={activeNotes || []}
            onBackToDashboard={() => setCurrentTab('create')}
          />
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

      <footer className="border-t border-slate-900 bg-slate-950 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>Playlist Scholar &bull; Autonomous YouTube-to-Technical-Notes Platform</span>
          <span>Powered by LangGraph &bull; Playwright PDF &bull; OpenAI</span>
        </div>
      </footer>
    </div>
  );
}
export default App;

