from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.database import create_all_tables
from app.routers import cart, health, orders, products


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: set up resources on startup, tear down on shutdown."""
    # ── Startup ────────────────────────────────────────────────
    await create_all_tables()

    yield

    # ── Shutdown ───────────────────────────────────────────────
    # Nothing to explicitly close; SQLAlchemy disposes the engine pool
    # automatically when the process exits.


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=settings.APP_DESCRIPTION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        contact={
            "name": "fscart Team",
            "email": "support@fscart.example.com",
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
        openapi_tags=[
            {
                "name": "products",
                "description": "Manage the product catalogue.",
            },
            {
                "name": "cart",
                "description": "Shopping cart operations — add, update, remove items.",
            },
            {
                "name": "orders",
                "description": "Place and track orders.",
            },
            {
                "name": "health",
                "description": "Liveness and readiness probes.",
            },
        ],
    )

    # ── CORS ───────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=settings.ALLOW_CREDENTIALS,
        allow_methods=settings.ALLOWED_METHODS,
        allow_headers=settings.ALLOWED_HEADERS,
    )

    # ── Routers ────────────────────────────────────────────────
    app.include_router(health.router)
    app.include_router(products.router)
    app.include_router(cart.router)
    app.include_router(orders.router)

    @app.get("/", include_in_schema=False)
    async def root() -> dict:
        return {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs",
        }

    return app


app = create_app()
