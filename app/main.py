import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logging.basicConfig(
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("onbozor")


async def _setup_webhook():
    try:
        from app.config import settings
        if not settings.WEBHOOK_URL or not settings.BOT_TOKEN:
            logger.info("WEBHOOK_URL or BOT_TOKEN not set, skipping webhook")
            return
        import httpx
        webhook_url = f"{settings.WEBHOOK_URL}/bot/webhook"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"https://api.telegram.org/bot{settings.BOT_TOKEN}/setWebhook",
                json={"url": webhook_url, "drop_pending_updates": True},
            )
            logger.info("Webhook setup: %s", resp.json())
    except Exception as e:
        logger.error("Webhook setup failed: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("OnBozor API starting")
    await _setup_webhook()
    yield
    logger.info("OnBozor API shutting down")


app = FastAPI(title="OnBozor API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "OnBozor API"}


def _safe_include(module_path: str, attr: str = "router"):
    try:
        import importlib
        mod = importlib.import_module(module_path)
        router = getattr(mod, attr)
        app.include_router(router)
        logger.info("Router loaded: %s", module_path)
    except Exception as e:
        logger.error("Failed to load %s: %s", module_path, e)


_safe_include("app.routers.auth")
_safe_include("app.routers.listings")
_safe_include("app.routers.shops")
_safe_include("app.routers.search")
_safe_include("app.routers.favourites")
_safe_include("app.routers.referral")
_safe_include("app.routers.payments")
_safe_include("app.routers.notifications")
_safe_include("app.routers.admin")
_safe_include("app.routers.upload")


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
        logger.error("Bot webhook error: %s", e)
        return {"ok": False}


@app.exception_handler(Exception)
async def global_error(request: Request, exc: Exception):
    logger.error("Error: %s %s — %s", request.method, request.url.path, exc)
    return JSONResponse(status_code=500, content={"error": str(exc)})
