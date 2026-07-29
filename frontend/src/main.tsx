import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "./styles.css";

function App() {
  return (
    <main className="app-shell">
      <section className="placeholder-panel">
        <p className="eyebrow">Epic I readiness</p>
        <h1>7bots MVP Phase 1 Frontend</h1>
        <p>
          Vite is configured with a local <code>/api</code> proxy to the FastAPI backend. The
          production Epic I screens will be planned and implemented next.
        </p>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root") as HTMLElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
