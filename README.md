# RAG Demo

Minimal **Retrieval Augmented Generation** demo: upload documents, embed them into a local vector store, and chat with an LLM grounded on your files. **No Docker required.**

**Project layout and architecture:** see [PROJECT_MAP.md](./PROJECT_MAP.md).

**AI / agent onboarding:** see [AGENTS.md](./AGENTS.md) (standard repo-root file for assistants).

## What you need

| Requirement | Notes |
|-------------|--------|
| **Python 3.11+** | Backend |
| **Node.js 18+** | Angular frontend |
| **Ollama** | Local embeddings + LLM ([ollama.com](https://ollama.com)) |

## How to run (quick path)

Run these **three** pieces in order: Ollama → backend → frontend.

### 1. Ollama

```bash
ollama list
ollama pull nomic-embed-text
ollama pull llama3.2
```

Keep the Ollama app/daemon running (default API: `http://localhost:11434`).

### 2. Backend (FastAPI)

**Windows (PowerShell)**

```powershell
cd path\to\rag-demo\backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python main.py
```

**macOS / Linux**

```bash
cd path/to/rag-demo/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

- API (default port **8010** — avoids clashes with other tools that use **8000**): **http://localhost:8010**
- Swagger UI: **http://localhost:8010/docs**
- Override with **`API_PORT`** in `backend/.env`.

### 3. Frontend (Angular)

**Windows / macOS / Linux**

```bash
cd path/to/rag-demo/frontend
npm install
npm start
```

- App: **http://localhost:4200**
- In development, HTTP calls go to **`/api/...`** on the same origin and **`frontend/proxy.conf.js`** forwards them to the backend (default **`http://127.0.0.1:8010`**). No CORS setup needed for normal local use.
- If you change the backend port, start the dev server with the same target, for example:  
  `PowerShell:` `$env:BACKEND_URL='http://127.0.0.1:8088'; npm start`

Open the UI, confirm the status banner shows the backend and models, then upload a file and use the chat panel.

## Configuration

Copy `backend/.env.example` to `backend/.env` and edit as needed:

- **`OLLAMA_*`** — URL and model names (defaults match the pulls above).
- **`API_PORT`** — Backend listen port (default **8010**); keep it aligned with **`frontend/proxy.conf.js`** (or **`BACKEND_URL`** when running `npm start`).
- **`CHROMA_PERSIST_DIR`** — Where Chroma stores vectors (default `./chroma_data`).
- **`KNOWLEDGE_BASE_DIR`** — Optional folder of markdown docs to index via API (`POST /index-knowledge-base` / `POST /scan-and-index`). See `.env.example` for examples.
- **`TARGET_APP_SOURCE`**, **`AUTO_GENERATE_DOCS`** — Optional: generate markdown from an Angular `src/app` tree on startup and index it (advanced; see `.env.example`).
- **`CORS_ORIGINS`** — JSON list of allowed frontend origins if you change ports.

After changing `.env`, restart the backend.

## Optional: generate docs from Angular source (CLI)

From the repo root, with the backend venv activated and dependencies installed:

```bash
python scripts/generate-docs.py <path-to-angular-src-app> <output-markdown-dir>
```

Example:

```bash
python scripts/generate-docs.py C:/my-app/ui/src/app C:/my-app/docs/auto-generated
```

You can then point `KNOWLEDGE_BASE_DIR` at that output or index via the backend endpoints described in [PROJECT_MAP.md](./PROJECT_MAP.md).

## Using the app

1. Open **http://localhost:4200**
2. Upload **PDF, TXT, Markdown, DOCX, HTML, or CSV** (see UI hints)
3. Wait until indexing finishes
4. Ask questions in the chat; responses include **source** filenames when available

## Troubleshooting

| Issue | What to check |
|-------|----------------|
| UI says it cannot connect | Backend running? Default URL is **`http://127.0.0.1:8010`** (see `API_PORT`). Restart **`npm start`** after editing **`proxy.conf.js`** or **`BACKEND_URL`**. Another app on **8000** does not matter unless your proxy still points there. |
| Ollama / model errors | `ollama list`, models pulled, `OLLAMA_BASE_URL` in `.env` |
| CORS in browser console | Dev UI uses the **`/api` proxy** (same origin). If you bypass the proxy and call the API URL directly from the browser, add your origin to **`CORS_ORIGINS`** in `.env`. |
| Empty text from a PDF | Prefer text-based PDFs; scanned images need OCR elsewhere |
| Wrong API host from frontend | Dev: **`ApiService`** uses **`/api`** and **`proxy.conf.js`**. Production builds need a real API URL or your own proxy. |

## API summary

Full table: [PROJECT_MAP.md](./PROJECT_MAP.md). Common endpoints: `GET /health`, `POST /upload`, `GET /documents`, `DELETE /documents/{filename}`, `POST /chat`.

## Repository

Public mirror: [github.com/rohitedwardK/rag-app](https://github.com/rohitedwardK/rag-app).
