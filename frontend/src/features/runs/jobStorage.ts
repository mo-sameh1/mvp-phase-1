const PREFIX = "mvp-phase1:last-job:";

export function readLastJobId(systemId: string): string | null {
  return window.localStorage.getItem(`${PREFIX}${systemId}`);
}

export function writeLastJobId(systemId: string, jobId: string): void {
  window.localStorage.setItem(`${PREFIX}${systemId}`, jobId);
}
