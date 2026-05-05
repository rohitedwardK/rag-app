# Agents guide

This repository uses **`AGENTS.md`** only (common Cursor convention at the repo root). Do not add a duplicate `AGENT.md`; keep onboarding here.

Use this file as **first-pass context** when analyzing or changing this repository. For deeper diagrams and API tables, read [PROJECT_MAP.md](./PROJECT_MAP.md). For setup and commands, read [README.md](./README.md).

## What this project is

Local **RAG** demo: upload documents → chunk → embed with **Ollama** → store in **ChromaDB** (embedded) → chat via **FastAPI** backend and **Angular 18** SPA. No Docker in the default flow.

## Stack

| Layer | Technology |
|-------|------------|
| API | Python 3.11+, FastAPI (`backend/main.py`) |
| Config | `pydantic-settings`, `backend/.env` (copy from `backend/.env.example`) |
| Vector DB | Chroma persistent dir `backend/chroma_data/` (local files, not committed) |
| LLM / embeddings | Ollama HTTP API (default `http://localhost:11434`) |
| UI | Angular 18 standalone app (`frontend/`), dev server port **4200** |
| API port | **8010** by default (`API_PORT` in `.env`; avoids common **8000** conflicts) |
| Dev HTTP | Browser calls **`/api/*`**; **`frontend/proxy.conf.js`** forwards to the backend |

## Suggested read order for code analysis

1. `backend/main.py` — routes, models, startup (includes optional auto-doc indexing).
2. `backend/config.py` — all env-backed settings.
3. `backend/services/document_service.py` — upload → chunk → embed → Chroma.
4. `backend/services/chat_service.py` — retrieve → prompt → LLM response.
5. `backend/rag/` — `chunker.py`, `embeddings.py`, `vector_store.py`, `retriever.py`, `llm.py`, `prompts.py`.
6. `frontend/src/app/app.component.ts` — single-component UI (upload, doc list, chat).
7. `frontend/src/app/services/api.service.ts` — dev `baseUrl` is **`/api`** (proxy). For another backend port, set **`BACKEND_URL`** when running `npm start` or edit **`frontend/proxy.conf.js`**.

Optional / advanced:

- `backend/services/doc_generator.py` — Angular source → markdown (API + `scripts/generate-docs.py`).
- `scripts/generate-docs.py` — CLI companion to doc generation.

## Endpoints (backend)

The UI only calls: `/health`, `/model-status`, `/upload`, `/documents`, `/documents/{filename}`, `/chat`.

Additional admin-style routes live in `main.py`: `/index-knowledge-base`, `/scan-and-index`, `/clear-index`. Full list: [PROJECT_MAP.md](./PROJECT_MAP.md).

## Runtime data (usually absent from git)

Do not assume these exist in a fresh clone; they are gitignored or local-only:

- `frontend/node_modules/`, `frontend/.angular/`
- `backend/venv/`, `backend/chroma_data/`
- `backend/uploads/*` (except `.gitkeep`)

## Conventions worth preserving

- Backend settings: extend `Settings` in `config.py` and mirror variables in `.env.example`.
- CORS: `cors_origins` in settings — update if the frontend runs on a new origin/port.
- Angular: standalone component; HTTP calls centralized in `ApiService`.

## Documentation map

| File | Purpose |
|------|---------|
| [README.md](./README.md) | Install, run, troubleshoot |
| [PROJECT_MAP.md](./PROJECT_MAP.md) | Architecture, Mermaid diagram, directory tree, API table |

When answering questions about “how does X work?”, trace from `main.py` into the relevant `services/` or `rag/` module rather than inferring only from the frontend.
