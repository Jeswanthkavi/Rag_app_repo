import os
from typing import List
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Supabase Configuration
    supabase_url: str = Field(
        default="https://sbkxmevrereobziaubsl.supabase.co",
        validation_alias=AliasChoices("NEXT_PUBLIC_SUPABASE_URL", "SUPABASE_URL")
    )
    supabase_anon_key: str = Field(
        default="",
        validation_alias=AliasChoices("NEXT_PUBLIC_SUPABASE_ANON_KEY", "SUPABASE_ANON_KEY")
    )
    supabase_service_role_key: str = Field(
        default="",
        validation_alias=AliasChoices("SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_SERVICE_KEY")
    )
    supabase_jwt_secret: str = Field(
        default="",
        validation_alias=AliasChoices("SUPABASE_JWT_SECRET")
    )

    # Security & Abuse Guardrails
    max_upload_size_bytes: int = Field(
        default=20 * 1024 * 1024,  # 20 MB max file size
        validation_alias=AliasChoices("MAX_UPLOAD_SIZE_BYTES")
    )
    max_pdf_pages: int = Field(
        default=250,  # Prevent PDF decompression / page bombs
        validation_alias=AliasChoices("MAX_PDF_PAGES")
    )
    rate_limit_chat_per_minute: int = Field(
        default=30,  # Max LLM queries per minute per IP/tenant
        validation_alias=AliasChoices("RATE_LIMIT_CHAT_PER_MINUTE")
    )
    rate_limit_upload_per_minute: int = Field(
        default=10,  # Max uploads per minute per IP/tenant
        validation_alias=AliasChoices("RATE_LIMIT_UPLOAD_PER_MINUTE")
    )

    # OpenRouter LLM Configuration
    openrouter_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("OPENROUTER_API_KEY")
    )
    openrouter_model: str = Field(
        default="nvidia/nemotron-3-ultra-550b-a55b:free",
        validation_alias=AliasChoices("OPENROUTER_MODEL")
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        validation_alias=AliasChoices("OPENROUTER_BASE_URL")
    )

    # Embedding Configuration
    embedding_provider: str = Field(
        default="openrouter",
        validation_alias=AliasChoices("EMBEDDING_PROVIDER")
    )
    embedding_model: str = Field(
        default="text-embedding-3-large",
        validation_alias=AliasChoices("EMBEDDING_MODEL")
    )
    embedding_dimension: int = Field(
        default=768,
        validation_alias=AliasChoices("EMBEDDING_DIMENSION")
    )

    # Storage Configuration
    storage_bucket: str = Field(
        default="user-documents",
        validation_alias=AliasChoices("STORAGE_BUCKET")
    )

    # Server Configuration
    backend_host: str = Field(
        default="0.0.0.0",
        validation_alias=AliasChoices("BACKEND_HOST")
    )
    backend_port: int = Field(
        default=8000,
        validation_alias=AliasChoices("BACKEND_PORT")
    )
    cors_origins: List[str] = ["*"]


settings = Settings()

