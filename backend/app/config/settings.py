from typing import Literal, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    APP_ENV: Literal["development", "staging", "production", "testing"] = "development"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # PostgreSQL Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "raguser"
    POSTGRES_PASSWORD: str = "ragpassword"
    POSTGRES_DB: str = "hr_rag_db"

    # LLM Settings (supports "gemini", "openai", "azure_openai", "anthropic", "local")
    LLM_PROVIDER: Literal["openai", "gemini", "azure_openai", "anthropic", "local"] = "gemini"
    LLM_MODEL: str = "gemini-2.5-flash"
    LLM_API_KEY: str = Field(default="", description="API key for LLM provider (OpenAI / Gemini / Anthropic)")
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API key")
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"

    # Embedding Settings
    EMBEDDING_PROVIDER: Literal["openai", "gemini", "huggingface", "azure_openai"] = "openai"
    EMBEDDING_MODEL: str = "gemini-embedding-002"
    EMBEDDING_DIMENSION: int = 1536

    # Reranker Settings
    RERANKER_PROVIDER: Literal["bge", "cohere", "none"] = "none"
    BGE_MODEL_NAME: str = "BAAI/bge-reranker-v2-m3"
    COHERE_API_KEY: str = Field(default="", description="Cohere API key for reranker")

    # Retrieval & Pipeline Settings
    VECTOR_STORE: str = "postgres"
    DENSE_TOP_K: int = 30
    SPARSE_TOP_K: int = 30
    FUSION_TOP_K: int = 50
    RERANK_TOP_K: int = 10
    FINAL_CONTEXT_CHUNKS: int = 5
    MAX_RETRIEVAL_RETRIES: int = 2
    MAX_HISTORY_MESSAGES: int = 20

    # Ingestion Settings
    MAX_FILE_SIZE_MB: int = 50
    UPLOAD_DIR: str = "./storage/uploads"
    TARGET_CHUNK_TOKENS: int = 512
    CHUNK_OVERLAP_TOKENS: int = 80

    # LangSmith Observability
    LANGSMITH_TRACING: bool = False
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_PROJECT: str = "hr-rag-chatbot"

    # MCP Server
    MCP_ENABLED: bool = False
    MCP_SERVER_HOST: str = "0.0.0.0"
    MCP_SERVER_PORT: int = 8001

    @property
    def effective_llm_key(self) -> str:
        if self.LLM_PROVIDER == "gemini":
            return self.GEMINI_API_KEY or self.LLM_API_KEY
        return self.LLM_API_KEY

    @property
    def async_database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def sync_database_url(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
