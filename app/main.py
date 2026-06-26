import time
import logging
from collections import defaultdict
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


_start_time = time.time()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("OnBozor API starting (env=%s)", settings.ENVIRONMENT)
    yield
    logger.info("OnBozor API shutting down")


app = FastAPI(
    title="OnBozor API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


# ── Rate Limiting ──
_rate_limits: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

RATE_RULES = {
    "POST:/auth/telegram": (5, 60),       # 5/min
    "POST:/listings": (10, 3600),          # 10/hour
    "POST:/upload/image": (20, 3600),      # 20/hour
    "GET:/search": (60, 60),              # 60/min
}
DEFAULT_RATE = (100, 60)                   # 100/min


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    path = request.url.path
    if path in ("/health", "/", "/docs", "/openapi.json"):
        return await call_next(request)

    client_ip = _get_client_ip(request)
    key = f"{request.method}:{path}"
    max_requests, window = RATE_RULES.get(key, DEFAULT_RATE)

    now = time.time()
    bucket = _rate_limits[client_ip][key]
    _rate_limits[client_ip][key] = [t for t in bucket if now - t < window]

    if len(_rate_limits[client_ip][key]) >= max_requests:
        return JSONResponse(
            status_code=429,
            content={"error": "rate_limit", "detail": f"Limitdan oshdi. {window} soniya kuting."},
        )

    _rate_limits[client_ip][key].append(now)
    return await call_next(request)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    ms = round((time.time() - start) * 1000, 1)
    if request.url.path not in ("/health",):
        logger.info("%s %s → %s (%sms)", request.method, request.url.path, response.status_code, ms)
    return response


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "uptime": int(time.time() - _start_time),
        "env": settings.ENVIRONMENT,
    }


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
_safe_include("app.routers.reviews")
_safe_include("app.routers.promotions")
_safe_include("app.routers.analytics")
_safe_include("app.routers.gamification")
_safe_include("app.routers.conversations")


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
