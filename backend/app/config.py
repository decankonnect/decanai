from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    ai_api_key: str = ""
    ai_provider: str = "ollama"
    ai_base_url: str = "http://127.0.0.1:11434"
    ai_model: str = "llama3.2"
    ai_vision_model: str = "llama3.2-vision"
    ai_embedding_model: str = "nomic-embed-text"
    ai_embedding_dimensions: int = 768
    cors_origins: str = "http://localhost:3000"
    max_file_size_mb: int = 10
    max_message_length: int = 12000
    rate_limit_requests: int = 30
    rate_limit_window: int = 60

    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()
