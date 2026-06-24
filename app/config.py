from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BOT_TOKEN: str
    DATABASE_URL: str

    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

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

    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    RATE_LIMIT_PER_MINUTE: int = 100

    SENTRY_DSN: str = ""
    WEBHOOK_URL: str = ""
    ENVIRONMENT: str = "development"

    ADMIN_IDS: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"

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
