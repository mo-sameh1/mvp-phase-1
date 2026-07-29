export type AppConfig = {
  apiBasePath: string;
  apiKey: string;
  defaultSystemId: string;
  jobPollingMs: number;
};

const DEFAULT_API_BASE_PATH = "/api";
const DEFAULT_SYSTEM_ID = "demo-legacy-system";
const DEFAULT_JOB_POLLING_MS = 3000;

export function readAppConfig(): AppConfig {
  return {
    apiBasePath: normalizeBasePath(import.meta.env.VITE_API_BASE_PATH || DEFAULT_API_BASE_PATH),
    apiKey: import.meta.env.VITE_API_KEY || "",
    defaultSystemId: import.meta.env.VITE_DEFAULT_SYSTEM_ID || DEFAULT_SYSTEM_ID,
    jobPollingMs: parsePositiveInteger(
      import.meta.env.VITE_JOB_POLLING_MS,
      DEFAULT_JOB_POLLING_MS,
    ),
  };
}

function normalizeBasePath(value: string): string {
  const trimmed = value.trim();
  if (!trimmed || trimmed === "/") {
    return "";
  }
  return `/${trimmed.replace(/^\/+|\/+$/g, "")}`;
}

function parsePositiveInteger(value: string | undefined, fallback: number): number {
  if (!value) {
    return fallback;
  }
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}
