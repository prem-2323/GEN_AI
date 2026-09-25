import { useState, useEffect, useRef, useCallback } from 'react';
import { jobApi, StartJobPayload } from '../api/jobApi';
import { JobRecord, JobStage } from '../types/job';

export function useJob(jobId?: string) {
  const [job, setJob] = useState<JobRecord | null>(null);
  const [loading, setLoading] = useState<boolean>(Boolean(jobId));
  const [error, setError] = useState<string | null>(null);
  const pollTimerRef = useRef<any>(null);

  const fetchJob = useCallback(async () => {
    if (!jobId) {
      setJob(null);
      setLoading(false);
      return;
    }
    try {
      const res = await jobApi.getJob(jobId);
      const j = res.job;
      setJob(j);
      if (j.status === 'completed' || j.status === 'failed') {
        if (pollTimerRef.current) {
          clearInterval(pollTimerRef.current);
          pollTimerRef.current = null;
        }
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to poll job status');
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  useEffect(() => {
    if (!jobId) return;
    fetchJob();
    pollTimerRef.current = setInterval(fetchJob, 1500);

    return () => {
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
        pollTimerRef.current = null;
      }
    };
  }, [jobId, fetchJob]);

  const startJob = async (projectId: string, payload: StartJobPayload): Promise<JobRecord> => {
    setLoading(true);
    setError(null);
    try {
      const res = await jobApi.startJob(projectId, payload);
      setJob(res.job);
      return res.job;
    } catch (err: any) {
      const msg = err?.message || 'Failed to start background job';
      setError(msg);
      throw new Error(msg);
    } finally {
      setLoading(false);
    }
  };

  return {
    job,
    loading,
    error,
    refresh: fetchJob,
    startJob,
  };
}
