from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    APP_NAME: str
    APP_VERSION: str
    APP_ENV: str
    FILE_ALLOWED_EXTENSIONS: list
    FILE_MAX_SIZE_MB: int
    FILE_CHUNK_SIZE: int

    class Config:
        
        env_file = "src/.env"
        validate_assignment = False
        
def get_settings():
    return Settings()