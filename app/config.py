from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "DocMind"
    app_env: str = "development"
    secret_key: str

    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "db"
    postgres_port: int = 5432
    database_url: str

    redis_url: str
    celery_broker_url: str
    celery_result_backend: str

    openai_api_key: str = ""
    groq_api_key: str = ""
    llm_model: str = "llama-3.3-70b-versatile"
    llm_base_url: str = "https://api.groq.com/openai/v1"
    access_token_expire_minutes: int = 60
    jwt_algorithm: str = "HS256"
    max_file_size_mb: int = 50
    upload_dir: str = "/tmp/docmind_uploads"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
