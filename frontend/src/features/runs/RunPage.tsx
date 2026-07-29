import { AlertTriangle, CheckCircle2, Clock3, Loader2, PlayCircle } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { getJob, triggerIngestion } from "../../api/client";
import type { JobResponse } from "../../api/types";
import { Button } from "../../components/Button";
import { ErrorState } from "../../components/States";
import { StatusBadge } from "../../components/StatusBadge";
import { readAppConfig } from "../../config/env";
import { readLastJobId, writeLastJobId } from "./jobStorage";

const ACTIVE_STATUSES = new Set(["queued", "running"]);

export function RunPage({ systemId }: { systemId: string }) {
  const config = readAppConfig();
  const [evidencePath, setEvidencePath] = useState("");
  const [jobId, setJobId] = useState<string | null>(() => readLastJobId(systemId));
  const [job, setJob] = useState<JobResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isActive = useMemo(() => Boolean(job?.status && ACTIVE_STATUSES.has(job.status)), [job]);

  useEffect(() => {
    if (!jobId) {
      return;
    }

    const controller = new AbortController();
    let timeoutId: number | undefined;

    async function loadJob() {
      try {
        const nextJob = await getJob(jobId as string, controller.signal);
        setJob(nextJob);
        setError(null);
        if (ACTIVE_STATUSES.has(nextJob.status) && !controller.signal.aborted) {
          timeoutId = window.setTimeout(loadJob, config.jobPollingMs);
        }
      } catch (exc) {
        if (!controller.signal.aborted) {
          setError(exc instanceof Error ? exc.message : "Could not load job status");
        }
      }
    }

    void loadJob();

    return () => {
      controller.abort();
      if (timeoutId !== undefined) {
        window.clearTimeout(timeoutId);
      }
    };
  }, [config.jobPollingMs, jobId]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await triggerIngestion(systemId, evidencePath.trim() || undefined);
      writeLastJobId(systemId, response.job_id);
      setJobId(response.job_id);
      setJob({
        id: response.job_id,
        system_id: response.system_id,
        phase: response.phase,
        status: response.status,
        run_id: response.run_id,
        error_message: null,
        started_at: null,
        finished_at: null,
      });
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Could not trigger ingestion");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <section className="page-heading">
        <div>
          <p className="eyebrow">I2 Trigger Run</p>
          <h2>Run As-Is ingestion</h2>
          <p>
            Start the Phase 1 pipeline and monitor the backend job without refreshing the page.
          </p>
        </div>
        {job ? <StatusBadge status={job.status} /> : null}
      </section>

      <form className="panel run-form" onSubmit={onSubmit}>
        <label htmlFor="evidence-path">Evidence path</label>
        <div className="input-row">
          <input
            id="evidence-path"
            value={evidencePath}
            onChange={(event) => setEvidencePath(event.target.value)}
            placeholder="Leave empty to use EVIDENCE_ROOT"
          />
          <Button disabled={loading || isActive}>
            <PlayCircle size={18} aria-hidden="true" />
            {loading ? "Starting" : "Run"}
          </Button>
        </div>
      </form>

      {error ? <ErrorState title="Run status unavailable" message={error} /> : null}
      {job ? <JobCard job={job} /> : <NoJobState />}
    </main>
  );
}

function JobCard({ job }: { job: JobResponse }) {
  const icon = getStatusIcon(job.status);
  return (
    <section className="panel job-card" aria-live="polite">
      <div className="job-title">
        {icon}
        <div>
          <h3>Job {job.id}</h3>
          <p>{job.run_id || "Run id will appear once the backend starts processing."}</p>
        </div>
        <StatusBadge status={job.status} />
      </div>
      <dl className="definition-grid">
        <div>
          <dt>System</dt>
          <dd>{job.system_id}</dd>
        </div>
        <div>
          <dt>Phase</dt>
          <dd>{job.phase}</dd>
        </div>
        <div>
          <dt>Started</dt>
          <dd>{formatDate(job.started_at)}</dd>
        </div>
        <div>
          <dt>Finished</dt>
          <dd>{formatDate(job.finished_at)}</dd>
        </div>
      </dl>
      {job.error_message ? (
        <div className="error-message">
          <AlertTriangle size={18} aria-hidden="true" />
          <span>{job.error_message}</span>
        </div>
      ) : null}
    </section>
  );
}

function NoJobState() {
  return (
    <section className="state-block">
      <Clock3 size={28} aria-hidden="true" />
      <h2>No run selected</h2>
      <p>Trigger ingestion to create a job, or refresh after a saved job exists for this system.</p>
    </section>
  );
}

function getStatusIcon(status: string) {
  if (status === "succeeded") {
    return <CheckCircle2 className="status-icon success" size={28} aria-hidden="true" />;
  }
  if (status === "failed") {
    return <AlertTriangle className="status-icon danger" size={28} aria-hidden="true" />;
  }
  return <Loader2 className="status-icon spinning" size={28} aria-hidden="true" />;
}

function formatDate(value: string | null) {
  return value ? new Date(value).toLocaleString() : "Not recorded";
}
