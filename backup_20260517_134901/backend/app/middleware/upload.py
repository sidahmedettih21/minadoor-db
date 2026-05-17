from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
# Upload validation is handled in the endpoint via validate_import_file.
# This middleware is kept for extension (e.g., global file size rejection
# before the body is parsed by the route handler).

IMPORT_PATHS = {"/api/v1/clients/import/preview"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


class UploadValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "POST" and request.url.path in IMPORT_PATHS:
            content_length = request.headers.get("Content-Length")
            if content_length and int(content_length) > MAX_UPLOAD_BYTES:
                from starlette.responses import JSONResponse
                return JSONResponse(
                    status_code=413,
                    content={"detail": "File too large (max 10 MB)"},
                )
        return await call_next(request)
