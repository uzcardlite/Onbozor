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

if settings.SENTRY_DSN:
    try:
        import sentry_sdk
        sentry_sdk.init(dsn=settings.SENTRY_DSN, environment=settings.ENVIRONMENT, traces_sample_rate=0.1)
        logger.info("Sentry initialized")
    except Exception as e:
        logger.warning("Sentry init failed: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("OnBozor API starting (env=%s)", settings.ENVIRONMENT)
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
    return {"status": "ok", "version": "1.0.0", "env": settings.ENVIRONMENT}


@app.get("/")
def root():
    return {"message": "OnBozor API", "status": "running"}


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


@app.exception_handler(404)
async def not_found(request: Request, exc):
    return JSONResponse(status_code=404, content={"error": "not_found", "detail": "Sahifa topilmadi"})


@app.exception_handler(Exception)
async def global_error(request: Request, exc: Exception):
    logger.error("Error: %s %s — %s", request.method, request.url.path, exc, exc_info=True)
    if settings.SENTRY_DSN:
        try:
            import sentry_sdk
            sentry_sdk.capture_exception(exc)
        except Exception:
            pass
    return JSONResponse(status_code=500, content={"error": "server_error", "detail": "Serverda xatolik yuz berdi"})
