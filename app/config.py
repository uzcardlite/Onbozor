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

    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    RATE_LIMIT_PER_MINUTE: int = 100

    SENTRY_DSN: str = ""
    WEBHOOK_URL: str = ""
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"


settings = Settings()
