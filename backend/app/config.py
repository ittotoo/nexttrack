"""Configuration management using Pydantic settings."""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Spotify API Credentials (optional — system works without them)
    spotify_client_id: str = Field(default="", env="SPOTIFY_CLIENT_ID")
    spotify_client_secret: str = Field(default="", env="SPOTIFY_CLIENT_SECRET")

    # Database Configuration
    db_host: str = Field(default="localhost", env="DB_HOST")
    db_port: int = Field(default=5432, env="DB_PORT")
    db_name: str = Field(default="nexttrack", env="DB_NAME")
    db_user: str = Field(default="postgres", env="DB_USER")
    db_password: str = Field(default="postgres", env="DB_PASSWORD")

    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_reload: bool = Field(default=True, env="API_RELOAD")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
