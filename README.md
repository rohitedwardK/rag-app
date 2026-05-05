# RAG Demo

A minimal RAG (Retrieval Augmented Generation) demo with document upload and chat. No Docker required.

## Features

- Upload PDF, TXT, or Markdown documents
- Automatic text extraction, chunking, and embedding
- Chat interface to ask questions about your documents
- Local vector storage (ChromaDB embedded mode)
- Uses Ollama for embeddings and LLM

## Prerequisites

- Python 3.11+
- Node.js 18+
- Ollama running locally

## Quick Start

### 1. Verify Ollama is Running

```bash
# Check Ollama is running
ollama list

# Pull required models (if not already)
ollama pull nomic-embed-text
ollama pull llama3.2
```

### 2. Start the Backend

```powershell
cd rag-demo/backend

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python main.py
```

The API will be available at `http://localhost:8000`.
API docs at `http://localhost:8000/docs`.

### 3. Start the Frontend

Open a new terminal:

```powershell
cd rag-demo/frontend

# Install dependencies
npm install

# Start development server
npm start
```

The UI will be available at `http://localhost:4200`.

## Usage

1. Open `http://localhost:4200` in your browser
2. Upload a document (PDF, TXT, or MD file)
3. Wait for indexing to complete
4. Ask questions about your document in the chat

## Project Structure

```
rag-demo/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Settings
│   ├── requirements.txt     # Python dependencies
│   ├── rag/                  # RAG components
│   │   ├── chunker.py       # Text splitting
│   │   ├── embeddings.py    # Ollama embeddings
│   │   ├── llm.py           # Ollama LLM
│   │   ├── prompts.py       # Prompt templates
│   │   ├── retriever.py     # Vector search
│   │   └── vector_store.py  # ChromaDB interface
│   └── services/
│       ├── chat_service.py      # Chat with RAG
│       └── document_service.py  # Document processing
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── app.component.ts    # Main UI component
│   │   │   └── services/
│   │   │       └── api.service.ts  # HTTP client
│   │   ├── main.ts
│   │   └── styles.scss
│   ├── package.json
│   └── angular.json
└── README.md
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Check API status |
| `/upload` | POST | Upload a document |
| `/documents` | GET | List all documents |
| `/documents/{filename}` | DELETE | Delete a document |
| `/chat` | POST | Send a message |

## Configuration

Create a `.env` file in `backend/` to customize settings:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBED_MODEL=nomic-embed-text
OLLAMA_LLM_MODEL=llama3.2
CHROMA_PERSIST_DIR=./chroma_data
```

## Troubleshooting

### "Cannot connect to backend"
- Ensure the Python server is running on port 8000
- Check for CORS errors in browser console

### "Ollama connection error"
- Verify Ollama is running: `ollama list`
- Check the Ollama URL in config

### "No text extracted from document"
- PDF must contain text (not just images)
- Try a different file format

## Next Steps

Once this works, you can expand to:
- URL crawling
- Multi-user/project support
- PostgreSQL for metadata
- Improved chunking strategies
