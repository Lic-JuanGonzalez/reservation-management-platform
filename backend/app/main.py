from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_client import make_asgi_app
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import IntegrityError

from app.api.exception_handlers import (
    generic_exception_handler,
    integrity_error_handler,
    validation_exception_handler,
)
from app.api.v1.middleware.correlation_id import CorrelationIdMiddleware
from app.api.v1.middleware.rate_limiter import limiter
from app.api.v1.middleware.security_headers import SecurityHeadersMiddleware
from app.api.v1.routers import auth, reports, reservations, resources, tenants, dev
from app.core.config import settings
from app.core.database import engine
from app.core.logging import configure_logging
from app.core.redis_client import close_redis_pool
import app.infrastructure.database.models  # noqa: F401 — registers all ORM mappers

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging()
    logger.info(
        "application_startup",
        env=settings.APP_ENV,
        version=settings.APP_VERSION,
    )
    yield
    await engine.dispose()
    await close_redis_pool()
    logger.info("application_shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Enterprise multi-tenant SaaS Reservation Platform API",
        docs_url="/api/docs" if not settings.is_production else None,
        redoc_url="/api/redoc" if not settings.is_production else None,
        openapi_url="/api/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # Rate limiter state
    app.state.limiter = limiter

    # Middleware (order matters — outermost first)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Correlation-ID"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CorrelationIdMiddleware)

    # Exception handlers
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(IntegrityError, integrity_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, generic_exception_handler)

    # API v1 routers
    api_prefix = "/api/v1"
    app.include_router(auth.router, prefix=api_prefix)
    app.include_router(tenants.router, prefix=api_prefix)
    app.include_router(resources.router, prefix=api_prefix)
    app.include_router(reservations.router, prefix=api_prefix)
    app.include_router(reports.router, prefix=api_prefix)

    if not settings.is_production:
        app.include_router(dev.router, prefix=api_prefix)

    # Prometheus metrics endpoint
    if settings.PROMETHEUS_ENABLED:
        metrics_app = make_asgi_app()
        app.mount("/metrics", metrics_app)

    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        return {"status": "healthy", "version": settings.APP_VERSION}

    @app.get("/ready", tags=["Health"])
    async def readiness_check() -> dict[str, str]:
        try:
            from app.core.database import engine as db_engine
            async with db_engine.connect() as conn:
                await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        except Exception as exc:
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail="Database unavailable") from exc
        return {"status": "ready"}

    return app


app = create_app()
