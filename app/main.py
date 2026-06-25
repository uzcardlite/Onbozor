import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings

logging.basicConfig(
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("onbozor")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting OnBozor API")
    yield
    logger.info("Shutting down")


app = FastAPI(title="OnBozor API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.exception_handler(Exception)
async def error_handler(request: Request, exc: Exception):
    logger.error("Error: %s %s — %s", request.method, request.url.path, exc)
    return JSONResponse(status_code=500, content={"error": "server_error"})


# ── Routers ──
try:
    from app.routers import auth, listings, shops, search, favourites
    from app.routers import referral, payments, notifications, admin, upload

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
    logger.info("All routers loaded")
except Exception as e:
    logger.error("Router import failed: %s", e, exc_info=True)


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
