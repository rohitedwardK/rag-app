# RAG Demo

Minimal **Retrieval Augmented Generation** demo: upload documents, embed them into a local vector store, and chat with an LLM grounded on your files. **No Docker required.**

**Project layout and architecture:** see [PROJECT_MAP.md](./PROJECT_MAP.md).

**AI / agent onboarding:** see [AGENTS.md](./AGENTS.md) (shortcut: [AGENT.md](./AGENT.md)).

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

- API: **http://localhost:8000**
- Swagger UI: **http://localhost:8000/docs**

### 3. Frontend (Angular)

**Windows / macOS / Linux**

```bash
cd path/to/rag-demo/frontend
npm install
npm start
```

- App: **http://localhost:4200**

Open the UI, confirm the status banner shows the backend and models, then upload a file and use the chat panel.

## Configuration

Copy `backend/.env.example` to `backend/.env` and edit as needed:

- **`OLLAMA_*`** — URL and model names (defaults match the pulls above).
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
| UI says it cannot connect | Backend running on port **8000**? Firewall? |
| Ollama / model errors | `ollama list`, models pulled, `OLLAMA_BASE_URL` in `.env` |
| CORS in browser console | Add your frontend URL to `CORS_ORIGINS` in `.env` |
| Empty text from a PDF | Prefer text-based PDFs; scanned images need OCR elsewhere |
| Wrong API host from frontend | `baseUrl` in `frontend/src/app/services/api.service.ts` is **http://localhost:8000** |

## API summary

Full table: [PROJECT_MAP.md](./PROJECT_MAP.md). Common endpoints: `GET /health`, `POST /upload`, `GET /documents`, `DELETE /documents/{filename}`, `POST /chat`.

## Repository

Public mirror: [github.com/rohitedwardK/rag-app](https://github.com/rohitedwardK/rag-app).
