import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.logger import logger
from app.middleware.upload import UploadValidationMiddleware
from app.middleware.version import VersionHeaderMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.routers import auth, clients, exports, health, templates, travel_types, users

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting MinaDoor API", extra={"environment": settings.ENVIRONMENT})
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.TEMP_EXPORT_DIR, exist_ok=True)
    yield
    # Shutdown
    from app.dependencies import redis_client
    await redis_client.aclose()
    logger.info("MinaDoor API shutdown complete")


app = FastAPI(
    title="MinaDoor Travel DB",
    version="1.0.0",
    lifespan=lifespan,
    # Disable auto-docs in production to avoid info leakage
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
)

# Middleware order matters: outermost = first to receive request
app.add_middleware(RequestIDMiddleware)
app.add_middleware(VersionHeaderMiddleware)
app.add_middleware(UploadValidationMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID"],
)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(
        "Unhandled error",
        extra={"request_id": request_id, "path": str(request.url), "error": str(exc)},
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "request_id": request_id},
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


# Routers
app.include_router(auth.router)
app.include_router(clients.router)
app.include_router(exports.router)
app.include_router(health.router)
app.include_router(templates.router)
app.include_router(travel_types.router)
app.include_router(users.router)


@app.get("/")
async def root():
    return {"service": "MinaDoor Travel DB API", "version": "1.0.0"}
