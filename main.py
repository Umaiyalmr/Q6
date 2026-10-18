
import time
import uuid
from collections import defaultdict, deque
from math import ceil
from threading import Lock

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Assigned configuration
EMAIL = "23f2005531@ds.study.iitm.ac.in"
ALLOWED_ORIGIN = "https://app-m7ulh9.example.com"

RATE_LIMIT = 9
WINDOW_SECONDS = 10

api = FastAPI(title="Middleware Stack API")

# Per-client sliding-window buckets
request_times = defaultdict(deque)
rate_lock = Lock()


# Middleware 1: Request context
@api.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id
    return response


# Middleware 2: Per-client rate limiting
@api.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # CORS preflight requests must not consume rate-limit quota.
    if request.method == "OPTIONS" or request.url.path != "/ping":
        return await call_next(request)

    client_id = request.headers.get("X-Client-Id", "anonymous")
    now = time.monotonic()

    with rate_lock:
        timestamps = request_times[client_id]

        # Remove requests outside the 10-second window.
        while timestamps and now - timestamps[0] >= WINDOW_SECONDS:
            timestamps.popleft()

        if len(timestamps) >= RATE_LIMIT:
            retry_after = max(
                1,
                ceil(WINDOW_SECONDS - (now - timestamps[0])),
            )

            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": str(retry_after)},
            )

        timestamps.append(now)

    return await call_next(request)


# Endpoint: GET /ping
@api.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.headers.get("X-Request-ID")
        or request.scope.get("request_id"),
    }


# Middleware 3: Strict CORS.
# Keep this wrapper at the bottom so CORS also covers 429 responses.
app = CORSMiddleware(
    app=api,
    allow_origins=[
        ALLOWED_ORIGIN,
        # Add the exam page's exact origin here if different.
    ],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["X-Request-ID", "X-Client-Id", "Content-Type"],
    expose_headers=["X-Request-ID", "Retry-After"],
)
