"""Configuration settings for the RAG demo."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Ollama configuration
    ollama_base_url: str = "http://localhost:11434"
    ollama_embed_model: str = "nomic-embed-text"
    ollama_llm_model: str = "llama3.2"

    # ChromaDB - uses persistent local storage
    chroma_persist_dir: str = "./chroma_data"

    # HTTP server (uvicorn); 8010 avoids clashing with other local apps on 8000
    api_port: int = 8010

    # File upload
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 10

    # Knowledge base folder (for auto-indexing app documentation)
    # Set this to point to your app's docs folder
    knowledge_base_dir: str = ""

    # Target Angular app source path (for auto-generating docs)
    # Example: C:/path/to/app/ui/src/app
    target_app_source: str = ""
    target_app_name: str = "Application"

    # Auto-generate and index docs on startup
    auto_generate_docs: bool = False

    # CORS
    cors_origins: list[str] = [
        "http://localhost:4200",
        "http://localhost:4201",
        "http://localhost:3000",
    ]

    class Config:
        env_file = ".env"
        extra = "ignore"


_settings: Settings | None = None


def get_settings() -> Settings:
    """Get cached settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
