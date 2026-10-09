import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.core.logging import logger
from app.core.request_context import set_current_request_id, get_current_request_id
from app.core.errors import AppException
from app.core.rate_limit import limiter
from app.api.router import api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting BookLeaf Author Support & Communication Portal API")
    yield
    logger.info("Shutting down BookLeaf API")


app = FastAPI(
    title="BookLeaf Author Support & Communication Portal",
    description="Production-grade operational support and author communication platform for BookLeaf Publishing.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Rate Limiter State & Middleware
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|([a-zA-Z0-9_-]+\.)*vercel\.app)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request Context & Logging Middleware
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:12]}"
    set_current_request_id(req_id)

    start_time = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start_time) * 1000, 2)

    response.headers["X-Request-ID"] = req_id

    # Avoid logging spam on health checks
    if not request.url.path.endswith(("/health", "/ready")):
        logger.info(
            f"{request.method} {request.url.path} status={response.status_code} duration={duration_ms}ms"
        )

    return response


# Domain Exception Handler
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    req_id = get_current_request_id()
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
            "request_id": req_id,
        },
    )


# Request Validation Error Handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    req_id = get_current_request_id()
    errors = exc.errors()
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Input validation failed for this request.",
                "details": errors,
            },
            "request_id": req_id,
        },
    )


# Rate Limit Exceeded Handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    req_id = get_current_request_id()
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "success": False,
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": f"Too many requests. Rate limit exceeded: {exc.detail}.",
                "details": str(exc.detail),
            },
            "request_id": req_id,
        },
    )


# Generic Fallback Exception Handler
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    req_id = get_current_request_id()
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected internal server error occurred. Please contact system support.",
            },
            "request_id": req_id,
        },
    )


# Register API v1
app.include_router(api_v1_router)


# Root Welcome Route
@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "BookLeaf Author Support & Communication Portal API",
        "status": "online",
        "docs_url": "/docs",
        "health_url": "/api/v1/health",
        "version": "1.0.0",
    }

