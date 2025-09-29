from unittest.mock import DEFAULT
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    APP_NAME: str
    APP_VERSION: str
    APP_ENV: str
    FILE_ALLOWED_EXTENSIONS: list
    FILE_MAX_SIZE_MB: int
    FILE_CHUNK_SIZE: int
    MONGODB_URL: str
    MONGODB_DATABASE: str

    GENERATION_BACKEND: str = None
    EMBEDDING_BACKEND: str = None

    OPENAI_API_KEY: str = None
    COHERE_API_KEY: str = None
    OPENAI_BASE_URL: str = None

    GENERATION_MODEL: str = None
    EMBEDDING_MODEL: str = None
    EMBEDDING_SIZE: int = None

    INPUT_DEFAULT_MAX_TOKENS: int = None
    GENERATION_DEFAULT_MAX_TOKENS: int = None
    GENERATION_DEFAULT_TEMPERATURE: float = None

    VECTOR_DB_BACKEND: str = None
    VECTOR_DB_PATH: str = None
    VECTOR_DB_DISTANCE_METHOD: str = None
    VECTOR_DB_TOP_K: int = None

    DESIRED_LANGUAGE: str = None
    DEFAULT_LANGUAGE: str = None

    class Config:

        env_file = "src/.env"
        validate_assignment = False


def get_settings():
    return Settings()
