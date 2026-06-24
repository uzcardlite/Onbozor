import time
import logging
from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine

logging.basicConfig(
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("onbozor")

# ── Sentry ──
if settings.SENTRY_DSN:
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            traces_sample_rate=0.2,
        )
        logger.info("Sentry initialized (env=%s)", settings.ENVIRONMENT)
    except Exception as e:
        logger.warning("Sentry init failed: %s", e)


async def _setup_bot_webhook():
    if not settings.WEBHOOK_URL:
        logger.info("WEBHOOK_URL not set, skipping webhook setup")
        return
    try:
        import httpx
        api_url = f"https://api.telegram.org/bot{settings.BOT_TOKEN}/setWebhook"
        webhook_url = f"{settings.WEBHOOK_URL}/bot/webhook"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(api_url, json={
                "url": webhook_url,
                "allowed_updates": ["message", "callback_query"],
                "drop_pending_updates": True,
            })
            data = resp.json()
            if data.get("ok"):
                logger.info("Bot webhook set: %s", webhook_url)
            else:
                logger.error("Bot webhook failed: %s", data)
    except Exception as e:
        logger.error("Webhook setup error: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting OnBozor API (env=%s)", settings.ENVIRONMENT)
    async with engine.begin() as conn:
        from sqlalchemy import text
        await conn.execute(text("SELECT 1"))
    logger.info("Database connection OK")
    await _setup_bot_webhook()
    yield
    await engine.dispose()
    logger.info("Shutdown complete")


app = FastAPI(
    title="OnBozor API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url=None,
)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Rate Limiting ──
_rate_store: dict[str, list[float]] = defaultdict(list)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    path = request.url.path
    if path.startswith(("/docs", "/openapi", "/health")):
        return await call_next(request)

    client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    if not client_ip:
        client_ip = request.client.host if request.client else "unknown"

    now = time.time()
    timestamps = _rate_store[client_ip]
    _rate_store[client_ip] = [t for t in timestamps if now - t < 60.0]

    if len(_rate_store[client_ip]) >= settings.RATE_LIMIT_PER_MINUTE:
        return JSONResponse(
            status_code=429,
            content={"error": "rate_limit", "detail": "So'rovlar soni limitdan oshdi. 1 daqiqa kuting."},
        )

    _rate_store[client_ip].append(now)
    return await call_next(request)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000, 1)
    logger.info("%s %s → %s (%sms)", request.method, request.url.path, response.status_code, duration)
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled: %s %s — %s", request.method, request.url.path, exc, exc_info=True)
    if settings.SENTRY_DSN:
        try:
            import sentry_sdk
            sentry_sdk.capture_exception(exc)
        except Exception:
            pass
    return JSONResponse(
        status_code=500,
        content={"error": "server_error", "detail": "Serverda xatolik yuz berdi"},
    )


# ── Routers (lazy import to avoid circular deps) ──
from app.routers import auth, listings, shops, search, favourites, referral, payments, notifications, admin, upload

app.include_router(auth.router)
app.include_router(listings.router)
app.include_router(shops.router)
app.include_router(search.router)
app.include_router(favourites.router)
app.include_router(referral.router)
app.include_router(payments.router)
app.include_router(notifications.router)
app.include_router(admin.router)
app.include_router(upload.router)


@app.get("/health")
async def health_check():
    from sqlalchemy import text
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    status = "ok" if db_ok else "degraded"
    code = 200 if db_ok else 503
    return JSONResponse(
        status_code=code,
        content={"status": status, "database": "ok" if db_ok else "error", "version": "1.0.0"},
    )


@app.post("/bot/webhook")
async def bot_webhook(request: Request):
    try:
        from telegram import Update
        from app.bot_app import get_bot_application

        bot_app = await get_bot_application()
        data = await request.json()
        update = Update.de_json(data, bot_app.bot)
        await bot_app.process_update(update)
        return {"ok": True}
    except Exception as e:
        logger.exception("Bot webhook error: %s", e)
        return JSONResponse(status_code=200, content={"ok": False, "error": str(e)})
