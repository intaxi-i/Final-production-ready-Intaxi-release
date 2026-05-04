from __future__ import annotations

import os
from functools import lru_cache

from intaxi_bot.app.runtime_hotfixes import apply_runtime_hotfixes
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

apply_runtime_hotfixes()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'InTaxi API'
    app_env: str = Field(default='development', alias='APP_ENV')

    bot_token: str = Field(default='', alias='BOT_TOKEN')
    session_secret: str = Field(default='change-me', alias='SESSION_SECRET')
    dev_tg_id: int = Field(default=89137224, alias='DEV_TG_ID')
    dev_full_name: str = Field(default='Dev User', alias='DEV_FULL_NAME')
    dev_username: str | None = Field(default='dev', alias='DEV_USERNAME')


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        BOT_TOKEN=os.getenv('BOT_TOKEN', ''),
        SESSION_SECRET=os.getenv('SESSION_SECRET', 'change-me'),
        DEV_TG_ID=int(os.getenv('DEV_TG_ID', '89137224')),
        DEV_FULL_NAME=os.getenv('DEV_FULL_NAME', 'Dev User'),
        DEV_USERNAME=os.getenv('DEV_USERNAME', 'dev') or None,
    )
