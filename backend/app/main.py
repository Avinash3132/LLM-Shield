"""LLMShield Gauntlet Backend Application Entrypoint."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .api import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifespan context."""
    # Ensure sandboxes directories exist
    settings.file_vault_dir.mkdir(parents=True, exist_ok=True)
    settings.crm_data_path.parent.mkdir(parents=True, exist_ok=True)
    settings.email_outbox_path.parent.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title=settings.app_name,
    description="Dual-Execution Runtime Authorization Platform for Indirect Prompt-Injection Defense",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration to allow local Next.js frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "docs_url": "/docs",
        "health_url": "/api/health",
    }
