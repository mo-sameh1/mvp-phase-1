import { ExternalLink, GitCommitHorizontal, GitPullRequest } from "lucide-react";
import { useEffect, useState } from "react";

import { listArtifactVersions } from "../../api/client";
import type { ArtifactVersion } from "../../api/types";
import { EmptyState, ErrorState, LoadingState } from "../../components/States";
import { StatusBadge } from "../../components/StatusBadge";

export function VersionsPage({ systemId }: { systemId: string }) {
  const [versions, setVersions] = useState<ArtifactVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    listArtifactVersions(systemId)
      .then(setVersions)
      .catch((exc) =>
        setError(exc instanceof Error ? exc.message : "Could not load artifact versions"),
      )
      .finally(() => setLoading(false));
  }, [systemId]);

  return (
    <main className="page">
      <section className="page-heading">
        <div>
          <p className="eyebrow">I4 Artifact Versions</p>
          <h2>PR and approval status</h2>
          <p>Review the git-backed artifact versions connected to Phase 1 model approvals.</p>
        </div>
      </section>

      {loading ? <LoadingState message="Loading artifact versions..." /> : null}
      {error ? <ErrorState title="Artifact versions unavailable" message={error} /> : null}
      {!loading && !error && versions.length === 0 ? (
        <EmptyState
          title="No artifact versions"
          message="Run ingestion, open the model PR, and merge it to populate version history."
        />
      ) : null}
      {!loading && !error && versions.length > 0 ? <VersionList versions={versions} /> : null}
    </main>
  );
}

function VersionList({ versions }: { versions: ArtifactVersion[] }) {
  return (
    <section className="version-list">
      {versions.map((version) => (
        <article className="panel version-item" key={version.id}>
          <div className="version-heading">
            <div>
              <h3>{version.phase}</h3>
              <p>{version.run_id || "No run id recorded"}</p>
            </div>
            <StatusBadge status={version.approval_status} />
          </div>

          <dl className="definition-grid">
            <div>
              <dt>Commit</dt>
              <dd>
                <GitCommitHorizontal size={15} aria-hidden="true" />
                {shortSha(version.commit_sha)}
              </dd>
            </div>
            <div>
              <dt>Author</dt>
              <dd>{version.author_type}</dd>
            </div>
            <div>
              <dt>Approved by</dt>
              <dd>{version.approved_by || "Pending review"}</dd>
            </div>
            <div>
              <dt>Approved at</dt>
              <dd>{formatDate(version.approved_at)}</dd>
            </div>
            <div>
              <dt>Created</dt>
              <dd>{formatDate(version.created_at)}</dd>
            </div>
            <div>
              <dt>Pull request</dt>
              <dd>
                {version.pr_url ? (
                  <a href={version.pr_url} target="_blank" rel="noreferrer" className="inline-link">
                    <GitPullRequest size={15} aria-hidden="true" />
                    PR {version.pr_number || ""}
                    <ExternalLink size={14} aria-hidden="true" />
                  </a>
                ) : (
                  "No PR URL"
                )}
              </dd>
            </div>
          </dl>
        </article>
      ))}
    </section>
  );
}

function shortSha(value: string) {
  return value.length > 10 ? value.slice(0, 10) : value;
}

function formatDate(value: string | null) {
  return value ? new Date(value).toLocaleString() : "Not recorded";
}
