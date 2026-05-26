from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

class UploadValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only for import endpoint
        if request.url.path == "/api/v1/clients/import" and request.method == "POST":
            content_type = request.headers.get("content-type", "")
            if "multipart/form-data" not in content_type:
                return await call_next(request)
            # Read the file to validate (this middleware runs before the route)
            # We'll read the body asynchronously, check size/mime, then set back.
            body = await request.body()
            # Not ideal to read body twice, so we'll delegate to endpoint handler.
            # Instead, we'll implement validation inside the import service or in the endpoint.
            pass
        return await call_next(request)
