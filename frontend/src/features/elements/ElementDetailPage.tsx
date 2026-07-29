import { ArrowLeft, ExternalLink, GitBranch } from "lucide-react";
import { useEffect, useState } from "react";

import { getElementDetail } from "../../api/client";
import type { ModelElementDetail, RelationshipRef } from "../../api/types";
import { Link } from "../../app/router";
import { EmptyState, ErrorState, LoadingState } from "../../components/States";
import { StatusBadge } from "../../components/StatusBadge";
import { LAYER_LABELS } from "./layers";

export function ElementDetailPage({
  systemId,
  elementId,
}: {
  systemId: string;
  elementId: string;
}) {
  const [detail, setDetail] = useState<ModelElementDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    getElementDetail(elementId, controller.signal)
      .then(setDetail)
      .catch((exc) => {
        if (!controller.signal.aborted) {
          setError(exc instanceof Error ? exc.message : "Could not load element detail");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      });

    return () => controller.abort();
  }, [elementId]);

  return (
    <main className="page detail-page">
      <Link className="back-link" to={`/systems/${encodeURIComponent(systemId)}/elements`}>
        <ArrowLeft size={16} aria-hidden="true" />
        Back to model
      </Link>

      {loading ? <LoadingState message="Loading element detail..." /> : null}
      {error ? <ErrorState title="Element detail unavailable" message={error} /> : null}
      {!loading && !error && !detail ? (
        <EmptyState title="No element detail" message="The indexed element could not be found." />
      ) : null}
      {detail ? <ElementDetailContent systemId={systemId} detail={detail} /> : null}
    </main>
  );
}

function ElementDetailContent({
  systemId,
  detail,
}: {
  systemId: string;
  detail: ModelElementDetail;
}) {
  const element = detail.element;
  return (
    <>
      <section className="page-heading detail-heading">
        <div>
          <p className="eyebrow">{LAYER_LABELS[element.layer]}</p>
          <h2>{element.name}</h2>
          <p>{element.archimate_type}</p>
        </div>
        <StatusBadge status={element.confidence} />
      </section>

      <section className="panel detail-summary">
        <p>{element.documentation}</p>
        <dl className="definition-grid">
          <div>
            <dt>Element id</dt>
            <dd>{element.id}</dd>
          </div>
          <div>
            <dt>Git path</dt>
            <dd>{detail.git_path}</dd>
          </div>
          <div>
            <dt>Commit</dt>
            <dd>{shortSha(detail.current_commit)}</dd>
          </div>
          <div>
            <dt>Model JSON</dt>
            <dd>
              <a href={detail.model_json_url} target="_blank" rel="noreferrer" className="inline-link">
                Open file
                <ExternalLink size={14} aria-hidden="true" />
              </a>
            </dd>
          </div>
        </dl>
      </section>

      <section className="detail-grid">
        <article className="panel">
          <h3>Evidence citations</h3>
          <div className="citation-list">
            {element.evidence.map((citation, index) => (
              <div className="citation" key={`${citation.locator}-${index}`}>
                <strong>{citation.source_type}</strong>
                <code>{citation.locator}</code>
                <p>{citation.excerpt}</p>
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <h3>Relationships</h3>
          {element.relationships.length === 0 ? (
            <p className="muted">No relationships recorded for this element.</p>
          ) : (
            <div className="relationship-list">
              {element.relationships.map((relationship) => (
                <RelationshipLink
                  key={`${relationship.type}-${relationship.target_id}`}
                  systemId={systemId}
                  relationship={relationship}
                />
              ))}
            </div>
          )}
        </article>
      </section>
    </>
  );
}

function RelationshipLink({
  systemId,
  relationship,
}: {
  systemId: string;
  relationship: RelationshipRef;
}) {
  return (
    <Link
      className="relationship-link"
      ariaLabel={`${relationship.type} ${relationship.target_id}`}
      to={`/systems/${encodeURIComponent(systemId)}/elements/${encodeURIComponent(
        relationship.target_id,
      )}`}
    >
      <GitBranch size={16} aria-hidden="true" />
      <span>{relationship.type}</span>
      <strong>{relationship.target_id}</strong>
    </Link>
  );
}

function shortSha(value: string) {
  return value.length > 10 ? value.slice(0, 10) : value;
}
