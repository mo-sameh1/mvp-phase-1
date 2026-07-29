import { ExternalLink, Filter, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { listElements } from "../../api/client";
import type { Layer, ModelElementIndex } from "../../api/types";
import { LAYERS } from "../../api/types";
import { EmptyState, ErrorState, LoadingState } from "../../components/States";
import { Link } from "../../app/router";
import { groupElementsByLayer, LAYER_LABELS } from "./layers";

type LayerFilter = "all" | Layer;

export function ElementsPage({ systemId }: { systemId: string }) {
  const [elements, setElements] = useState<ModelElementIndex[]>([]);
  const [layer, setLayer] = useState<LayerFilter>("all");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    listElements(systemId)
      .then(setElements)
      .catch((exc) => setError(exc instanceof Error ? exc.message : "Could not load elements"))
      .finally(() => setLoading(false));
  }, [systemId]);

  const filtered = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return elements.filter((element) => {
      const matchesLayer = layer === "all" || element.layer === layer;
      const matchesQuery =
        !normalizedQuery ||
        element.name.toLowerCase().includes(normalizedQuery) ||
        element.archimate_type.toLowerCase().includes(normalizedQuery) ||
        element.id.toLowerCase().includes(normalizedQuery);
      return matchesLayer && matchesQuery;
    });
  }, [elements, layer, query]);

  const grouped = groupElementsByLayer(filtered);

  return (
    <main className="page">
      <section className="page-heading">
        <div>
          <p className="eyebrow">I3 Model Browser</p>
          <h2>Architecture elements</h2>
          <p>Browse indexed model elements by ArchiMate layer and open git-backed details.</p>
        </div>
      </section>

      <section className="toolbar" aria-label="Model filters">
        <div className="search-box">
          <Search size={18} aria-hidden="true" />
          <input
            aria-label="Search model elements"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search by name, type, or id"
          />
        </div>
        <div className="layer-tabs" aria-label="Layer filter">
          <button className={layer === "all" ? "active" : ""} onClick={() => setLayer("all")}>
            <Filter size={16} aria-hidden="true" />
            All
          </button>
          {LAYERS.map((nextLayer) => (
            <button
              key={nextLayer}
              className={layer === nextLayer ? "active" : ""}
              onClick={() => setLayer(nextLayer)}
            >
              {LAYER_LABELS[nextLayer]}
            </button>
          ))}
        </div>
      </section>

      {loading ? <LoadingState message="Loading model elements..." /> : null}
      {error ? <ErrorState title="Model elements unavailable" message={error} /> : null}
      {!loading && !error && filtered.length === 0 ? (
        <EmptyState
          title="No elements found"
          message="Run ingestion and merge the model PR, or adjust the current filters."
        />
      ) : null}

      {!loading && !error && filtered.length > 0 ? (
        <section className="layer-groups">
          {LAYERS.map((nextLayer) =>
            grouped[nextLayer].length > 0 ? (
              <LayerGroup
                key={nextLayer}
                systemId={systemId}
                layer={nextLayer}
                elements={grouped[nextLayer]}
              />
            ) : null,
          )}
        </section>
      ) : null}
    </main>
  );
}

function LayerGroup({
  systemId,
  layer,
  elements,
}: {
  systemId: string;
  layer: Layer;
  elements: ModelElementIndex[];
}) {
  return (
    <section className="layer-group">
      <div className="layer-heading">
        <h3>{LAYER_LABELS[layer]}</h3>
        <span>{elements.length} elements</span>
      </div>
      <div className="element-table" role="table" aria-label={`${LAYER_LABELS[layer]} elements`}>
        <div className="table-row table-head" role="row">
          <span>Name</span>
          <span>Type</span>
          <span>Updated</span>
          <span>Open</span>
        </div>
        {elements.map((element) => (
          <div className="table-row" role="row" key={element.id}>
            <span>
              <strong>{element.name}</strong>
              <small>{element.id}</small>
            </span>
            <span>{element.archimate_type}</span>
            <span>{new Date(element.updated_at).toLocaleString()}</span>
            <span>
              <Link
                className="inline-link"
                to={`/systems/${encodeURIComponent(systemId)}/elements/${encodeURIComponent(
                  element.id,
                )}`}
              >
                Detail
                <ExternalLink size={14} aria-hidden="true" />
              </Link>
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
