# Frontend

React/Vite/TypeScript frontend for the Phase 1 MVP reviewer loop.

Implemented screens:

- Run: trigger As-Is ingestion and poll job status.
- Model: browse indexed ArchiMate elements by layer and open git-backed element detail.
- Versions: inspect artifact versions, approval status, and GitHub PR links.

## Local Development

1. Start the backend from the repository root:

   ```bash
   uv run uvicorn backend.api.app:create_app --factory --reload
   ```

2. Copy the frontend environment example:

   ```bash
   cd frontend
   cp .env.example .env
   ```

3. Set `VITE_API_KEY` to the same value as backend `BACKEND_API_KEY`, then run:

   ```bash
   npm install
   npm run dev
   ```

The Vite dev server proxies browser calls from `/api/*` to the backend target configured by
`VITE_DEV_API_PROXY_TARGET`, defaulting to `http://127.0.0.1:8000`.

## Deployed Frontend

In local development, keep `VITE_API_BASE_PATH=/api` so Vite can proxy requests. In a deployed static
frontend, set `VITE_API_BASE_PATH` to the backend service URL, for example:

```bash
VITE_API_BASE_PATH=https://mvp-phase-1-production.up.railway.app
VITE_API_KEY=<same-value-as-backend-BACKEND_API_KEY>
```

The backend must allow the deployed frontend origin:

```bash
CORS_ALLOWED_ORIGINS=https://front-production-9849.up.railway.app
```

Redeploy the frontend after changing `VITE_*` values because Vite embeds them at build time.

For the MVP, clickable external links should be limited to GitHub PR URLs and model JSON URLs
returned by the backend. Evidence locators should be displayed as traceability text unless a later
task adds a source-controlled evidence URL contract.

## Checks

```bash
npm run build
npm run test:run
```
