import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings
    """
    ENV: str = os.environ.get("ENV")
    API_V1_STR: str = os.environ.get("API_V1_STR")
    JWT_SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY")
    REDIS_URL: str = os.environ.get("REDIS_URL")
    
    class Config:
        case_sensitive = True
    
settings = Settings()