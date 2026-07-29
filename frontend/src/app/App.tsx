import { Activity, Boxes, GitPullRequest, PlayCircle } from "lucide-react";
import { useEffect } from "react";

import { readAppConfig } from "../config/env";
import { EmptyState } from "../components/States";
import { ElementDetailPage } from "../features/elements/ElementDetailPage";
import { ElementsPage } from "../features/elements/ElementsPage";
import { RunPage } from "../features/runs/RunPage";
import { VersionsPage } from "../features/versions/VersionsPage";
import { Link, matchRoute, useRouter } from "./router";

export function App() {
  const route = matchRoute(useRouter().path);
  const config = readAppConfig();
  const systemId = "systemId" in route && route.systemId ? route.systemId : config.defaultSystemId;

  if (route.name === "home") {
    return <Redirect to={`/systems/${encodeURIComponent(config.defaultSystemId)}/run`} />;
  }

  return (
    <div className="app-shell">
      <header className="top-bar">
        <div>
          <p className="eyebrow">Phase 1 As-Is</p>
          <h1>7bots Model Viewer</h1>
        </div>
        <div className="system-pill">
          <Activity size={16} aria-hidden="true" />
          <span>{systemId}</span>
        </div>
      </header>

      <nav className="main-nav" aria-label="Primary navigation">
        <NavLink to={`/systems/${encodeURIComponent(systemId)}/run`} active={route.name === "run"}>
          <PlayCircle size={18} aria-hidden="true" />
          Run
        </NavLink>
        <NavLink
          to={`/systems/${encodeURIComponent(systemId)}/elements`}
          active={route.name === "elements" || route.name === "elementDetail"}
        >
          <Boxes size={18} aria-hidden="true" />
          Model
        </NavLink>
        <NavLink
          to={`/systems/${encodeURIComponent(systemId)}/versions`}
          active={route.name === "versions"}
        >
          <GitPullRequest size={18} aria-hidden="true" />
          Versions
        </NavLink>
      </nav>

      {route.name === "run" ? <RunPage systemId={route.systemId} /> : null}
      {route.name === "elements" ? <ElementsPage systemId={route.systemId} /> : null}
      {route.name === "elementDetail" ? (
        <ElementDetailPage systemId={route.systemId} elementId={route.elementId} />
      ) : null}
      {route.name === "versions" ? <VersionsPage systemId={route.systemId} /> : null}
      {route.name === "notFound" ? (
        <main className="page">
          <EmptyState
            title="Page not found"
            message="Use the navigation above to return to the Phase 1 viewer."
          />
        </main>
      ) : null}
    </div>
  );
}

function Redirect({ to }: { to: string }) {
  const { navigate } = useRouter();
  useEffect(() => navigate(to), [navigate, to]);
  return null;
}

function NavLink({
  to,
  active,
  children,
}: {
  to: string;
  active: boolean;
  children: React.ReactNode;
}) {
  return (
    <Link to={to} className={active ? "nav-link active" : "nav-link"}>
      {children}
    </Link>
  );
}
