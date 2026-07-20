from __future__ import annotations

from typing import Annotated, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    BOT_TOKEN: str
    REPLICATE_API_KEY: str = ""
    REPLICATE_MODEL_VERSION: str = (
        "stability-ai/sdxl:39ed52f2319f9412e0a15b39cd4e64ea96cda24ab38ff7c5015c60b7c05e7a55"
    )
    SD_API_URL: str = "http://localhost:7860"
    SD_API_KEY: str = ""
    ACTIVE_BACKEND: Literal["replicate", "sd"] = "replicate"
    # NoDecode: pydantic-settings would otherwise JSON-decode the env value
    # before the validator runs, crashing on "123,456"-style input.
    ADMIN_IDS: Annotated[list[int], NoDecode] = []
    RATE_LIMIT_WINDOW: int = 60
    RATE_LIMIT_MAX: int = 5
    FREE_DAILY_CREDITS: int = 3
    DB_PATH: str = "bot.db"

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v: object) -> list[int]:
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return v  # type: ignore[return-value]


config = Config()
