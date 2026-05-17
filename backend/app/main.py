import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import CORS_ORIGINS
from app.logger import logger
from app.middleware.upload import UploadValidationMiddleware
from app.middleware.version import VersionHeaderMiddleware
from app.routers import auth, clients, exports, health, templates, travel_types, users

app = FastAPI(title="MinaDoor Travel DB", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(UploadValidationMiddleware)
app.add_middleware(VersionHeaderMiddleware)

# Exception handlers for safe error responses
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

# Include routers
app.include_router(auth.router)
app.include_router(clients.router)
app.include_router(exports.router)
app.include_router(health.router)
app.include_router(templates.router)
app.include_router(travel_types.router)
app.include_router(users.router)

@app.get("/")
async def root():
    return {"message": "MinaDoor Travel DB API v1"}

# For serving frontend static files (optional)
