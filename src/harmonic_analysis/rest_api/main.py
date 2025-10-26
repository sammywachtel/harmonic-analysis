"""
FastAPI application factory for harmonic analysis REST API.

Opening move: Create and configure the FastAPI application.
This module provides the main entry point for the REST API server.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI


def create_app() -> "FastAPI":
    """
    Create and configure the FastAPI application.

    Main play: Set up the app with CORS, routes, and OpenAPI documentation.
    This factory pattern allows easy testing and multiple app instances.

    Returns:
        Configured FastAPI application instance

    Example:
        >>> from harmonic_analysis.rest_api.main import create_app
        >>> app = create_app()
        >>> # Run with: uvicorn main:app --reload
    """
    # Opening move: check FastAPI is available
    try:
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "FastAPI is required for the REST API. "
            "Install it with 'pip install fastapi uvicorn[standard] python-multipart'."
        ) from exc

    # Main play: create the app with metadata
    app = FastAPI(
        title="Harmonic Analysis API",
        description=(
            "REST API for comprehensive harmonic and modal analysis. "
            "Analyze chord progressions, melodies, scales, and uploaded music files."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Big play: configure CORS for local development
    # Allow requests from frontend (typically localhost:5173 for Vite)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",  # Vite default
            "http://localhost:3000",  # React/Next.js default
            "http://localhost:8080",  # Alternative dev port
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Victory lap: include routes
    from .routes import router

    app.include_router(router)

    return app


# Create default app instance for uvicorn
# Usage: uvicorn harmonic_analysis.rest_api.main:app --reload
app = create_app()


if __name__ == "__main__":
    # Local development entry point
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
