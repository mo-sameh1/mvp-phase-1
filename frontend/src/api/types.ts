export type Layer = "motivation" | "strategy" | "business" | "application" | "technology";

export const LAYERS: Layer[] = [
  "motivation",
  "strategy",
  "business",
  "application",
  "technology",
];

export type IngestResponse = {
  job_id: string;
  system_id: string;
  phase: string;
  status: JobStatus;
  run_id: string;
};

export type JobStatus = "queued" | "running" | "succeeded" | "failed" | string;

export type JobResponse = {
  id: string;
  system_id: string;
  phase: string;
  status: JobStatus;
  run_id: string | null;
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
};

export type ModelElementIndex = {
  id: string;
  system_id: string;
  layer: Layer;
  archimate_type: string;
  name: string;
  git_path: string;
  current_commit: string;
  updated_at: string;
};

export type EvidenceCitation = {
  source_type: string;
  locator: string;
  excerpt: string;
};

export type RelationshipRef = {
  target_id: string;
  type: string;
  evidence: EvidenceCitation[];
};

export type ModelElement = {
  id: string;
  layer: Layer;
  archimate_type: string;
  name: string;
  documentation: string;
  confidence: "observed" | "inferred" | string;
  evidence: EvidenceCitation[];
  relationships: RelationshipRef[];
};

export type ModelElementDetail = {
  id: string;
  system_id: string;
  git_path: string;
  current_commit: string;
  model_json_url: string;
  element: ModelElement;
};

export type ArtifactVersion = {
  id: string;
  system_id: string;
  commit_sha: string;
  phase: string;
  tag: string | null;
  author_type: string;
  run_id: string | null;
  approval_status: string;
  approved_by: string | null;
  approved_at: string | null;
  pr_number: number | null;
  pr_url: string | null;
  created_at: string;
};
