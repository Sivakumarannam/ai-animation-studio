"""
FastAPI application entry point — Module 1 + Module 2 fully wired.

Startup sequence:
  1. Configure structlog
  2. Initialise database connection pool
  3. Register AI providers (LLM, Image, TTS, Subtitle, Renderer, SEO)
  4. Register workflow steps (in execution order)
  5. Register content plugins (Telugu Family Comedy, etc.)
  6. Mount all routers under /api/v1
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from apps.api.config import get_settings
from apps.api.routers import assets, auth, characters, health, plugins, projects, scenes, stories
from apps.api.routers import generation, ws as ws_router
from apps.api.routers import (
    expressions,
    poses,
    character_templates,
    library,
    compositions,
    asset_manager,
)
from database.connection import close_db, init_db
from packages.core.exceptions import AppError
from shared.constants import API_V1_PREFIX

settings = get_settings()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer() if settings.DEBUG else structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(
        getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    ),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)
logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("startup", app=settings.APP_NAME, version=settings.APP_VERSION)

    # 1. Database
    init_db(
        settings.DATABASE_URL,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
    )

    # 2. AI Providers (DI registry)
    from agents.registry import get_provider_registry
    from agents.provider_factory import setup_providers
    provider_registry = get_provider_registry()
    setup_providers(settings, provider_registry)

    # 3. Workflow Steps
    from workflow.registry import get_step_registry
    from workflow.setup import register_workflow_steps
    step_registry = get_step_registry()
    register_workflow_steps(step_registry, provider_registry)

    # 4. Content Plugins
    from plugins.registry import get_registry
    from plugins.content_types.telugu_family_comedy.plugin import TeluguFamilyComedyPlugin
    plugin_registry = get_registry()
    plugin_registry.register(TeluguFamilyComedyPlugin())
    logger.info("plugins_registered", count=len(plugin_registry.list_plugins()))

    yield

    # Shutdown
    logger.info("shutdown")
    await close_db()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Generic AI Animation Studio Platform — Plugin-based, provider-agnostic",
    docs_url=f"{API_V1_PREFIX}/docs",
    redoc_url=f"{API_V1_PREFIX}/redoc",
    openapi_url=f"{API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    status_map = {
        "NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "CONFLICT": status.HTTP_409_CONFLICT,
        "AUTHENTICATION_ERROR": status.HTTP_401_UNAUTHORIZED,
        "AUTHORIZATION_ERROR": status.HTTP_403_FORBIDDEN,
        "VALIDATION_ERROR": status.HTTP_422_UNPROCESSABLE_ENTITY,
    }
    http_status = status_map.get(exc.code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    return JSONResponse(
        status_code=http_status,
        content={"code": exc.code, "message": exc.message, "detail": exc.detail},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled_error", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"},
    )


# ---------------------------------------------------------------------------
# Routers — v1 sub-app
# ---------------------------------------------------------------------------

v1 = FastAPI(title=settings.APP_NAME)

# Module 1 — Core platform
v1.include_router(health.router)
v1.include_router(auth.router)
v1.include_router(projects.router)
v1.include_router(stories.router)
v1.include_router(scenes.router)
v1.include_router(characters.router)
v1.include_router(assets.router)
v1.include_router(plugins.router)

# Module 1 — AI generation + WebSocket progress
v1.include_router(generation.router)
v1.include_router(ws_router.router)

# Module 2 — Animation Engine
v1.include_router(expressions.router)
v1.include_router(poses.router)
v1.include_router(character_templates.router)
v1.include_router(library.router)
v1.include_router(compositions.router)
v1.include_router(asset_manager.router)

app.mount(API_V1_PREFIX, v1)
