"""Application settings layer with environment-aware inheritance."""

from __future__ import annotations

import os
from enum import Enum
from functools import lru_cache
from typing import Dict, Type

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Supported deployment environments."""

    DEV = "dev"
    PROD = "prod"


class AppSettings(BaseSettings):
    """Base settings shared across environments."""

    environment: Environment = Field(default=Environment.DEV, env="APP_ENV")
    bot_token: str = Field(default="", env="BOT_TOKEN")
    payment_provider_token: str = Field(default="", env="PAYMENT_PROVIDER_TOKEN")
    wallet_mnemonic: str = Field(default="", env="WALLET_MNEMONIC")
    wallet_private_key: str = Field(default="", env="WALLET_PRIVATE_KEY")
    deposit_address: str = Field(default="", env="DEPOSIT_ADDRESS")
    ton_api_key: str = Field(default="", env="TON_API_KEY")
    run_in_mainnet: bool = Field(default=False, env="RUN_IN_MAINNET")

    star_price_usd: float = Field(default=0.0119, env="STAR_PRICE_USD")
    ton_price_usd: float = Field(default=2.28, env="TON_PRICE_USD")
    database_file: str = Field(default="bot_database.db", env="DATABASE_FILE")

    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/bot.log", env="LOG_FILE")
    log_max_bytes: int = Field(default=1_000_000, env="LOG_MAX_BYTES")
    log_backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")
    http_timeout: float = Field(default=10.0, env="HTTP_TIMEOUT")
    ton_max_retries: int = Field(default=3, env="TON_MAX_RETRIES")
    pricing_refresh_interval: int = Field(default=300, env="PRICING_REFRESH_INTERVAL")
    balance_refresh_interval: int = Field(default=60, env="BALANCE_REFRESH_INTERVAL")
    pricing_provider_url: str = Field(
        default="https://api.coingecko.com/api/v3/simple/price?ids=the-open-network&vs_currencies=usd",
        env="PRICING_PROVIDER_URL",
    )
    admin_user_ids: list[int] = Field(default_factory=list, env="ADMIN_USER_IDS")
    forced_subscription_enabled: bool = Field(
        default=False, env="FORCED_SUBSCRIPTION_ENABLED"
    )
    forced_subscription_channels: list[str] = Field(
        default_factory=list, env="FORCED_SUBSCRIPTION_CHANNELS"
    )
    maintenance_mode: bool = Field(default=False, env="MAINTENANCE_MODE")
    maintenance_message: str = Field(
        default="🛠️ البوت في وضع الصيانة حالياً، يرجى المحاولة لاحقاً.",
        env="MAINTENANCE_MESSAGE",
    )
    broadcast_batch_size: int = Field(default=100, env="BROADCAST_BATCH_SIZE")
    broadcast_delay_seconds: float = Field(
        default=0.5, env="BROADCAST_DELAY_SECONDS"
    )
    default_user_language: str = Field(default="ar", env="DEFAULT_USER_LANGUAGE")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def star_price_ton(self) -> float:
        """Return TON price for a single Telegram star."""

        return self.star_price_usd / self.ton_price_usd if self.ton_price_usd else 0.0

    @property
    def api_base_url(self) -> str:
        """Select TON Center endpoint based on the target network."""

        return (
            "https://toncenter.com/api/v2"
            if self.run_in_mainnet
            else "https://testnet.toncenter.com/api/v2"
        )

    @field_validator("admin_user_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, value):
        if isinstance(value, str):
            return [int(part.strip()) for part in value.split(",") if part.strip()]
        return value

    @field_validator("forced_subscription_channels", mode="before")
    @classmethod
    def parse_channels(cls, value):
        if isinstance(value, str):
            return [channel.strip() for channel in value.split(",") if channel.strip()]
        return value


class DevSettings(AppSettings):
    """Developer-friendly defaults."""

    model_config = SettingsConfigDict(
        env_file=".env.dev",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


class ProdSettings(AppSettings):
    """Production overrides."""

    log_level: str = Field(default="WARNING", env="LOG_LEVEL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


_ENVIRONMENT_MAP: Dict[Environment, Type[AppSettings]] = {
    Environment.DEV: DevSettings,
    Environment.PROD: ProdSettings,
}


@lru_cache()
def get_settings() -> AppSettings:
    """Resolve the active settings instance using the APP_ENV flag."""

    raw_env = os.getenv("APP_ENV", Environment.DEV.value)
    try:
        environment = Environment(raw_env)
    except ValueError:
        environment = Environment.DEV

    settings_cls = _ENVIRONMENT_MAP.get(environment, DevSettings)
    settings = settings_cls(environment=environment)
    # align environment field to the resolved enum (in case env file overrides it)
    settings.environment = environment
    return settings
