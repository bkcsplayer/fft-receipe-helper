"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """All configuration is injected via .env — never hardcode secrets."""

    # MiniMax API
    MINIMAX_API_KEY: str
    MINIMAX_MODEL: str = "MiniMax-M2.5"

    # Google OAuth User Credentials
    GOOGLE_OAUTH_TOKEN_JSON: str = "token.json"

    # Google Drive — root folder shared with the service account
    GOOGLE_DRIVE_ROOT_FOLDER_ID: str

    # Google Sheets — spreadsheet ID (from the Sheet URL)
    GOOGLE_SHEETS_SPREADSHEET_ID: str

    # Server
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
