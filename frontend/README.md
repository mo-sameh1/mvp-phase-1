# Frontend

Epic I will build the React screens for the Phase 1 MVP. The current scaffold exists so the
frontend can run through Vite and call the FastAPI backend without browser CORS problems during
local development.

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

For the MVP, clickable external links should be limited to GitHub PR URLs and model JSON URLs
returned by the backend. Evidence locators should be displayed as traceability text unless a later
task adds a source-controlled evidence URL contract.
