"""Configuration management for Memorizer."""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings."""

    # Application
    app_name: str = "Memorizer"
    app_version: str = "2.0.0"
    environment: str = "development"

    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    streamlit_port: int = 8501
    canonical_url: str = "http://localhost:8000"

    # Storage
    data_dir: Path = Path("./data")
    chroma_dir: Path = Path("./data/chroma")
    models_dir: Path = Path("./models")

    # Embeddings (Dual-embedding system for better accuracy)
    embedding_model_primary: str = "all-MiniLM-L6-v2"  # Fast, 384D
    embedding_model_secondary: str = "all-MiniLM-L12-v2"  # High-quality, 384D
    embedding_model: str = "all-MiniLM-L6-v2"  # Backward compatibility
    embedding_dimension: int = 384
    embedding_dimension_secondary: int = 384
    use_dual_embeddings: bool = True
    embedding_weight_primary: float = 0.4  # Weight for L6 embeddings
    embedding_weight_secondary: float = 0.6  # Weight for L12 embeddings

    # LLM
    llm_model_path: str = "./models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
    llm_context_size: int = 2048
    llm_max_tokens: int = 256
    llm_temperature: float = 0.7
    llm_timeout: int = 120

    # Search
    search_limit: int = 10
    search_max_limit: int = 100
    similarity_threshold: float = 0.7
    fallback_threshold: float = 0.6
    tag_boost: float = 0.05

    # Background Jobs
    enable_background_jobs: bool = True
    title_generation_batch_size: int = 10

    # CORS
    cors_origins: list[str] = ["*"]
    cors_methods: list[str] = ["*"]
    cors_headers: list[str] = ["*"]

    class Config:
        env_prefix = "MEMORIZER_"
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Ensure directories exist
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.chroma_dir.mkdir(parents=True, exist_ok=True)
settings.models_dir.mkdir(parents=True, exist_ok=True)
