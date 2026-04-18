import logging
import os
import time

from fastapi import FastAPI
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


def build_logger() -> logging.Logger:
    logger = logging.getLogger("cloud_api")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                '{"time":"%(asctime)s","level":"%(levelname)s",'
                '"service":"cloud-api","message":"%(message)s"}'
            )
        )
        logger.addHandler(handler)

    logger.propagate = False
    return logger


logger = build_logger()
app = FastAPI(title="Cloud API", version="1.0.0")
STARTED_AT = time.time()

REQUEST_COUNT = Counter(
    "cloud_api_requests_total",
    "Total HTTP requests handled by the API.",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "cloud_api_request_duration_seconds",
    "HTTP request latency in seconds.",
    ["method", "path"],
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


@app.middleware("http")
async def collect_metrics(request: Request, call_next):
    started_at = time.perf_counter()
    path = request.url.path
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        elapsed = time.perf_counter() - started_at
        REQUEST_COUNT.labels(request.method, path, str(status_code)).inc()
        REQUEST_LATENCY.labels(request.method, path).observe(elapsed)


app.add_middleware(SecurityHeadersMiddleware)


@app.get("/")
def root() -> dict:
    return {
        "service": "cloud-api",
        "status": "ok",
        "env": os.getenv("APP_ENV", "DEV"),
    }


@app.get("/health")
def health() -> dict:
    logger.info("health check called")
    return {
        "status": "ok",
        "env": os.getenv("APP_ENV", "DEV"),
    }


@app.get("/ready")
def ready() -> dict:
    logger.info("readiness check called")
    return {
        "status": "ready",
        "env": os.getenv("APP_ENV", "DEV"),
        "uptime_seconds": round(time.time() - STARTED_AT, 2),
    }


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
