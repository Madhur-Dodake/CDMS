import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("cdms.access")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [ACCESS] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request logging and process duration tracking."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip logging for high-frequency health probes or websockets
        if request.url.path in ("/health", "/api/health"):
            return await call_next(request)

        start_time = time.time()
        client_host = request.client.host if request.client else "unknown"

        try:
            response: Response = await call_next(request)
            duration_ms = round((time.time() - start_time) * 1000, 2)
            response.headers["X-Process-Time"] = f"{duration_ms}ms"

            logger.info(
                f"{request.method} {request.url.path} - {response.status_code} ({duration_ms}ms) [client={client_host}]"
            )
            return response
        except Exception as exc:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.error(
                f"{request.method} {request.url.path} - FAILED ({duration_ms}ms) [client={client_host}] error: {exc}"
            )
            raise exc
