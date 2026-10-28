import { useEffect, useState, useRef } from 'react';
import { JobEvent, JobStatus } from '../types';

export function useJobProgress(jobId: string | null, onComplete?: () => void) {
  const [events, setEvents] = useState<JobEvent[]>([]);
  const [latestProgress, setLatestProgress] = useState<number>(0);
  const [currentStage, setCurrentStage] = useState<string>('Initializing');
  const [isFinished, setIsFinished] = useState<boolean>(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!jobId) {
      setEvents([]);
      setLatestProgress(0);
      setIsFinished(false);
      return;
    }

    const es = new EventSource(`/api/v1/jobs/${jobId}/events`);
    eventSourceRef.current = es;

    es.onmessage = (e) => {
      try {
        const data: JobEvent = JSON.parse(e.data);
        setEvents((prev) => [...prev, data]);
        if (typeof data.progress === 'number') {
          setLatestProgress(data.progress);
        }
        if (data.stage) {
          setCurrentStage(data.stage);
        }

        const terminalStages: JobStatus[] = ['COMPLETED', 'PARTIAL_SUCCESS', 'FAILED', 'CANCELLED'];
        if (terminalStages.includes(data.stage as JobStatus)) {
          setIsFinished(true);
          es.close();
          if (onComplete) {
            onComplete();
          }
        }
      } catch (err) {
        console.error('Error parsing SSE event', err);
      }
    };

    es.onerror = () => {
      // EventSource will automatically attempt to reconnect
    };

    return () => {
      es.close();
      eventSourceRef.current = null;
    };
  }, [jobId]);

  return { events, latestProgress, currentStage, isFinished };
}
