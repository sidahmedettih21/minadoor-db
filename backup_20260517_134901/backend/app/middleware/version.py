from starlette.middleware.base import BaseHTTPMiddleware

class VersionHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/api/v1"):
            response.headers["X-API-Version"] = "1"
            # When deprecating, set:
            # response.headers["Deprecation"] = "true"
            # response.headers["Sunset"] = "Sat, 01 Jan 2027 00:00:00 GMT"
        return response
