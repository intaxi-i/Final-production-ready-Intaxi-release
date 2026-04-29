from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'Intaxi Backend V2'
    app_env: str = Field(default='development', alias='APP_ENV')
    api_prefix: str = '/api/v2'

    database_url: str = Field(
        default='postgresql+asyncpg://intaxi:intaxi@localhost:5432/intaxi_v2',
        alias='DATABASE_URL',
    )
    session_secret: str = Field(default='change-me', alias='SESSION_SECRET')
    bot_token: str = Field(default='', alias='BOT_TOKEN')

    cors_origins: str = Field(
        default='http://localhost:3000,https://intaxi.best,https://www.intaxi.best,https://app.intaxi.best',
        alias='CORS_ORIGINS',
    )

    @property
    def is_production(self) -> bool:
        return self.app_env.strip().lower() in {'prod', 'production'}

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(',') if item.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
