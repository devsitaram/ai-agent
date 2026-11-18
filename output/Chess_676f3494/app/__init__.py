# Application package
from fastapi import FastAPI


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="My Application",
        description="Auto-generated application",
        version="1.0.0",
    )
    return app
