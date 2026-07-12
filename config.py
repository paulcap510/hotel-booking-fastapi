# settings.py loads, validates, and organizes values from a .env file

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict( # SettingsConfigDict tells to load from env file
        env_file=".env",
        env_file_encoding="utf-8",
    )
    secret_key: SecretStr
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    database_url: str

settings = Settings() # Loaded from .env file