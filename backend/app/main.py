from fastapi import FastAPI

from app.api.v1.health import router
from app.core.config import Settings, get_settings
from app.core.cors import NormalizedCORSMiddleware
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestIdMiddleware

API_PREFIX = "/api/v1"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings if settings is not None else get_settings()
    configure_logging(settings.log_level)
    production = settings.app_env == "prod"
    application = FastAPI(
        title="ChainScope",
        debug=False,
        docs_url=None if production else "/docs",
        redoc_url=None if production else "/redoc",
        openapi_url=None if production else "/openapi.json",
    )
    register_error_handlers(application)
    application.include_router(router, prefix=API_PREFIX)
    if settings.cors_origins:
        application.add_middleware(
            NormalizedCORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PATCH", "DELETE"],
            allow_headers=["Content-Type", "X-CSRF-Token"],
            expose_headers=["X-Request-ID"],
        )
    application.add_middleware(RequestIdMiddleware)
    return application


app = create_app()
