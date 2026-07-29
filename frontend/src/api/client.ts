import { readAppConfig } from "../config/env";
import type {
  ArtifactVersion,
  IngestResponse,
  JobResponse,
  Layer,
  ModelElementDetail,
  ModelElementIndex,
} from "./types";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export type RequestOptions = {
  method?: "GET" | "POST";
  body?: unknown;
  signal?: AbortSignal;
};

export async function requestJson<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const config = readAppConfig();
  const response = await fetch(`${config.apiBasePath}${path}`, {
    method: options.method || "GET",
    signal: options.signal,
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": config.apiKey,
    },
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });

  if (!response.ok) {
    throw new ApiError(await readErrorMessage(response), response.status);
  }

  return (await response.json()) as T;
}

export function triggerIngestion(
  systemId: string,
  evidencePath?: string,
): Promise<IngestResponse> {
  return requestJson<IngestResponse>(`/systems/${encodeURIComponent(systemId)}/ingest`, {
    method: "POST",
    body: evidencePath ? { evidence_path: evidencePath } : {},
  });
}

export function getJob(jobId: string, signal?: AbortSignal): Promise<JobResponse> {
  return requestJson<JobResponse>(`/jobs/${encodeURIComponent(jobId)}`, { signal });
}

export function listElements(systemId: string, layer?: Layer): Promise<ModelElementIndex[]> {
  const query = layer ? `?layer=${encodeURIComponent(layer)}` : "";
  return requestJson<ModelElementIndex[]>(
    `/systems/${encodeURIComponent(systemId)}/elements${query}`,
  );
}

export function getElementDetail(
  elementId: string,
  signal?: AbortSignal,
): Promise<ModelElementDetail> {
  return requestJson<ModelElementDetail>(`/elements/${encodeURIComponent(elementId)}`, { signal });
}

export function listArtifactVersions(systemId: string): Promise<ArtifactVersion[]> {
  return requestJson<ArtifactVersion[]>(
    `/systems/${encodeURIComponent(systemId)}/artifact-versions`,
  );
}

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    if (typeof payload.detail === "string" && payload.detail.trim()) {
      return payload.detail;
    }
  } catch {
    // Fall back to status text when the backend returns a non-JSON error.
  }
  return response.statusText || `Request failed with status ${response.status}`;
}
