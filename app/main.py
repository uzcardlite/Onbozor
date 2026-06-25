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


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("OnBozor API starting")
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


@app.exception_handler(Exception)
async def global_error(request: Request, exc: Exception):
    logger.error("Error: %s %s — %s", request.method, request.url.path, exc)
    return JSONResponse(status_code=500, content={"error": str(exc)})
