"""FastAPI application for RAG demo."""

import asyncio
import logging
import os
import shutil
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import get_settings
from services.document_service import DocumentService
from services.chat_service import ChatService
from services.doc_generator import DocGeneratorService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

document_service = DocumentService()
chat_service = ChatService()
doc_generator = DocGeneratorService()


async def auto_generate_and_index_docs():
    """
    Automatically generate documentation from source code and index into RAG.
    Called on startup if AUTO_GENERATE_DOCS is enabled.
    """
    if not settings.auto_generate_docs:
        logger.info("Auto-generate docs is disabled. Skipping startup indexing.")
        return
    
    if not settings.target_app_source:
        logger.warning("AUTO_GENERATE_DOCS is enabled but TARGET_APP_SOURCE is not set. Skipping.")
        return
    
    source_path = Path(settings.target_app_source)
    if not source_path.exists():
        logger.warning(f"Target app source not found: {settings.target_app_source}. Skipping auto-generation.")
        return
    
    logger.info(f"Starting auto-generation of docs from: {settings.target_app_source}")
    
    try:
        # Output to project root's docs folder (go up from ui/src/app to project root)
        project_root = source_path.parent.parent.parent
        output_path = project_root / "docs" / "auto-generated"
        
        result = doc_generator.generate_docs(
            str(source_path),
            str(output_path),
            settings.target_app_name
        )
        
        logger.info(f"Generated {result['files_generated']} documentation files")
        logger.info(f"Stats: {result['stats']}")
        
        md_files = list(Path(result['output_path']).rglob("*.md"))
        total_chunks = 0
        indexed_count = 0
        
        for md_file in md_files:
            try:
                relative_name = f"auto-gen/{md_file.relative_to(output_path)}"
                doc_result = await document_service.process_document(str(md_file), relative_name)
                indexed_count += 1
                total_chunks += doc_result["chunks_created"]
                logger.info(f"Indexed {relative_name}: {doc_result['chunks_created']} chunks")
            except Exception as e:
                logger.warning(f"Failed to index {md_file}: {e}")
        
        logger.info(f"Startup indexing complete: {indexed_count} docs, {total_chunks} chunks")
        
    except Exception as e:
        logger.exception(f"Error during auto-generation: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown tasks."""
    await auto_generate_and_index_docs()
    yield


app = FastAPI(
    title="RAG Demo API",
    description="A minimal RAG demo with document upload and chat",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve widget static files from the widget/dist directory
widget_static_path = Path(__file__).parent.parent.parent / "widget" / "dist"
if widget_static_path.exists():
    app.mount("/static", StaticFiles(directory=str(widget_static_path)), name="static")
    logger.info(f"Serving widget from: {widget_static_path}")
else:
    logger.warning(f"Widget static files not found at: {widget_static_path}")


class IndexKnowledgeBaseResponse(BaseModel):
    """Response for knowledge base indexing."""
    indexed_files: int
    total_chunks: int
    files: List[str]


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    sources: List[str]


class DocumentInfo(BaseModel):
    filename: str
    uploaded_at: str


class UploadResponse(BaseModel):
    filename: str
    chunks_created: int
    text_length: int


class HealthResponse(BaseModel):
    status: str
    ollama_url: str
    llm_model: str
    embed_model: str


class ModelStatusResponse(BaseModel):
    llm_model: str
    embed_model: str
    llm_active: bool
    embed_active: bool


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API health and configuration."""
    return HealthResponse(
        status="ok",
        ollama_url=settings.ollama_base_url,
        llm_model=settings.ollama_llm_model,
        embed_model=settings.ollama_embed_model,
    )


@app.get("/model-status", response_model=ModelStatusResponse)
async def model_status():
    """Check if Ollama models are active and responding."""
    import httpx
    
    llm_active = False
    embed_active = False
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        # Check if Ollama is responding and models are available
        try:
            response = await client.get(f"{settings.ollama_base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = [m.get("name", "").split(":")[0] for m in data.get("models", [])]
                llm_model_base = settings.ollama_llm_model.split(":")[0]
                embed_model_base = settings.ollama_embed_model.split(":")[0]
                llm_active = llm_model_base in models
                embed_active = embed_model_base in models
        except Exception as e:
            logger.warning(f"Failed to check Ollama status: {e}")
    
    return ModelStatusResponse(
        llm_model=settings.ollama_llm_model,
        embed_model=settings.ollama_embed_model,
        llm_active=llm_active,
        embed_active=embed_active,
    )


class IndexKnowledgeBaseRequest(BaseModel):
    """Request for indexing knowledge base."""
    docs_path: str | None = None


@app.post("/index-knowledge-base", response_model=IndexKnowledgeBaseResponse)
async def index_knowledge_base(request: IndexKnowledgeBaseRequest | None = None):
    """
    Index all markdown files from a knowledge base directory.
    
    This scans the directory recursively for .md files and indexes them.
    Use this to index your app's documentation folder.
    
    Args:
        docs_path: Path to the docs folder. If not provided, uses KNOWLEDGE_BASE_DIR from config.
    """
    docs_path = request.docs_path if request else None
    target_path = docs_path or settings.knowledge_base_dir
    
    if not target_path:
        raise HTTPException(
            status_code=400,
            detail="No docs path provided. Either pass docs_path or set KNOWLEDGE_BASE_DIR in .env",
        )
    
    docs_dir = Path(target_path)
    if not docs_dir.exists():
        raise HTTPException(status_code=400, detail=f"Directory not found: {target_path}")
    
    md_files = list(docs_dir.rglob("*.md"))
    if not md_files:
        raise HTTPException(status_code=400, detail=f"No .md files found in {target_path}")
    
    indexed_files = []
    total_chunks = 0
    
    for md_file in md_files:
        try:
            relative_name = str(md_file.relative_to(docs_dir))
            result = await document_service.process_document(str(md_file), relative_name)
            indexed_files.append(relative_name)
            total_chunks += result["chunks_created"]
            logger.info(f"Indexed {relative_name}: {result['chunks_created']} chunks")
        except Exception as e:
            logger.warning(f"Failed to index {md_file}: {e}")
    
    return IndexKnowledgeBaseResponse(
        indexed_files=len(indexed_files),
        total_chunks=total_chunks,
        files=indexed_files,
    )


@app.delete("/clear-index")
async def clear_index():
    """Clear all documents from the vector store."""
    from rag.vector_store import VectorStore
    vector_store = VectorStore()
    vector_store.clear_all()
    return {"status": "cleared", "message": "All documents removed from index"}


class ScanAndIndexRequest(BaseModel):
    """Request for scanning and indexing an Angular app."""
    app_source_path: str
    app_name: str = "Application"
    auto_index: bool = True


class ScanAndIndexResponse(BaseModel):
    """Response for scan and index operation."""
    docs_generated: int
    docs_indexed: int
    total_chunks: int
    output_path: str
    stats: dict


@app.post("/scan-and-index", response_model=ScanAndIndexResponse)
async def scan_and_index(request: ScanAndIndexRequest):
    """
    Scan an Angular application and generate documentation, then index it.
    
    This endpoint:
    1. Scans the Angular source code for components, services, routes, modules
    2. Extracts JSDoc comments, method signatures, inputs/outputs, dependencies
    3. Generates comprehensive markdown documentation files
    4. Optionally indexes the generated docs into the RAG system
    
    Args:
        app_source_path: Path to the Angular app source (e.g., /path/to/app/ui/src/app)
        app_name: Name of the application (for doc titles)
        auto_index: Whether to automatically index the generated docs
    """
    source_path = Path(request.app_source_path)
    if not source_path.exists():
        raise HTTPException(status_code=400, detail=f"Source path not found: {request.app_source_path}")
    
    # Output to project root's docs folder (go up from ui/src/app to project root)
    # e.g., /project/ui/src/app -> /project/docs/auto-generated
    project_root = source_path.parent.parent.parent  # ui/src/app -> ui/src -> ui -> project
    output_path = project_root / "docs" / "auto-generated"
    
    try:
        result = doc_generator.generate_docs(
            str(source_path),
            str(output_path),
            request.app_name
        )
        
        docs_indexed = 0
        total_chunks = 0
        
        if request.auto_index:
            md_files = list(Path(result['output_path']).rglob("*.md"))
            for md_file in md_files:
                try:
                    relative_name = f"auto-gen/{md_file.relative_to(output_path)}"
                    doc_result = await document_service.process_document(str(md_file), relative_name)
                    docs_indexed += 1
                    total_chunks += doc_result["chunks_created"]
                    logger.info(f"Indexed {relative_name}: {doc_result['chunks_created']} chunks")
                except Exception as e:
                    logger.warning(f"Failed to index {md_file}: {e}")
        
        return ScanAndIndexResponse(
            docs_generated=result['files_generated'],
            docs_indexed=docs_indexed,
            total_chunks=total_chunks,
            output_path=result['output_path'],
            stats=result['stats']
        )
        
    except Exception as e:
        logger.exception("Error in scan-and-index")
        raise HTTPException(status_code=500, detail=f"Error: {e}")


SUPPORTED_EXTENSIONS = [".pdf", ".txt", ".md", ".markdown", ".docx", ".html", ".htm", ".csv"]


@app.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document for indexing.
    
    Supported formats: PDF, TXT, MD, DOCX, HTML, CSV.
    The document will be chunked, embedded, and stored in the vector database.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Supported: {', '.join(SUPPORTED_EXTENSIONS)}",
        )

    file_size = 0
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    max_size = settings.max_file_size_mb * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {settings.max_file_size_mb}MB",
        )

    os.makedirs(settings.upload_dir, exist_ok=True)
    file_path = os.path.join(settings.upload_dir, file.filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = await document_service.process_document(file_path, file.filename)

        return UploadResponse(**result)

    except ValueError as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        logger.exception("Error processing document")
        raise HTTPException(status_code=500, detail=f"Error processing document: {e}")


@app.get("/documents", response_model=List[DocumentInfo])
async def list_documents():
    """List all indexed documents."""
    docs = document_service.get_documents()
    return [DocumentInfo(**doc) for doc in docs]


@app.delete("/documents/{filename}")
async def delete_document(filename: str):
    """Delete a document from the index."""
    try:
        document_service.delete_document(filename)
        return {"status": "deleted", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the RAG system.
    
    Retrieves relevant context from uploaded documents and generates a response.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        result = await chat_service.chat(request.message)
        return ChatResponse(**result)
    except Exception as e:
        logger.exception("Error in chat")
        raise HTTPException(status_code=500, detail=f"Error generating response: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
