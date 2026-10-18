
import time
import uuid
from collections import defaultdict, deque
from math import ceil
from threading import Lock

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

EMAIL = "23f2005531@ds.study.iitm.ac.in"
ALLOWED_ORIGIN = "https://app-m7ulh9.example.com"

RATE_LIMIT = 9
WINDOW_SECONDS = 10

api = FastAPI(title="Middleware Stack API")

request_times = defaultdict(deque)
rate_lock = Lock()


# Middleware 1: Request context
@api.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.scope["request_id"] = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Middleware 2: Per-client rate limiting
@api.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.method == "OPTIONS" or request.url.path != "/ping":
        return await call_next(request)

    client_id = request.headers.get("X-Client-Id", "anonymous")
    now = time.monotonic()

    with rate_lock:
        timestamps = request_times[client_id]

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


# Endpoint
@api.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.scope["request_id"],
    }


# Middleware 3: Strict CORS — only approved origins receive ACAO.
# If the exam page origin differs from ALLOWED_ORIGIN, add its exact
# origin to this list. Never use "*" for this assignment.
app = CORSMiddleware(
    app=api,
    allow_origins=[
        ALLOWED_ORIGIN,
        # Add the exact exam page origin here if different.
    ],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["X-Request-ID", "X-Client-Id", "Content-Type"],
    expose_headers=["X-Request-ID", "Retry-After"],
)
