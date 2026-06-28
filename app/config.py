from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BOT_TOKEN: str = ""
    DATABASE_URL: str = "postgresql+asyncpg://localhost/onbozor"

    JWT_SECRET: str = "change-me-in-production-32chars!"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 43200  # 30 kun

    PAYME_MERCHANT_ID: str = ""
    PAYME_KEY: str = ""
    CLICK_MERCHANT_ID: str = ""
    CLICK_SECRET_KEY: str = ""
    CLICK_SERVICE_ID: str = ""

    FRONTEND_URL: str = "http://localhost:3000"

    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    SHOP_MONTHLY_PRICE: int = 100_000
    MAX_LISTINGS_PER_USER: int = 10
    REFERRAL_BONUS_PERCENT: int = 5

    CORS_ORIGINS: str = "https://onbozor.vercel.app,http://localhost:3000,http://localhost:5173"

    SENTRY_DSN: str = ""
    WEBHOOK_URL: str = ""
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    ADMIN_IDS: str = "37453466"
    CHANNEL_ID: str = "@sarvar_qurbandurdiyev"
    CHANNEL_USERNAME: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def channel(self) -> str:
        """Mandatory-subscription channel — prefers CHANNEL_USERNAME (the
        Railway variable), falls back to CHANNEL_ID, then the default."""
        return (self.CHANNEL_USERNAME or self.CHANNEL_ID or "").strip()

    @property
    def channel_link(self) -> str:
        """t.me link for the channel (only meaningful for @username channels)."""
        ch = self.channel
        if ch.startswith("@"):
            return f"https://t.me/{ch[1:]}"
        return f"https://t.me/{ch.lstrip('@')}"

    @property
    def admin_ids_list(self) -> list[int]:
        if not self.ADMIN_IDS:
            return []
        return [int(x.strip()) for x in self.ADMIN_IDS.split(",") if x.strip()]

    @property
    def cors_origins_list(self) -> list[str]:
        import json
        val = self.CORS_ORIGINS
        if val.startswith("["):
            return json.loads(val)
        return [x.strip() for x in val.split(",") if x.strip()]

    @property
    def async_database_url(self) -> str:
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    @property
    def sync_database_url(self) -> str:
        url = self.DATABASE_URL
        if "+asyncpg" in url:
            url = url.replace("+asyncpg", "")
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url


settings = Settings()
