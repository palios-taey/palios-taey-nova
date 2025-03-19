"""
PALIOS-TAEY: AI-to-AI execution management platform

Main application entry point
"""
import logging
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from palios_taey.api import router
from palios_taey.core.errors import NotFoundError, ValidationError


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="PALIOS-TAEY",
    description="AI-to-AI execution management platform",
    version="0.1.0",
)


# Add exception handlers
@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


@app.exception_handler(NotFoundError)
async def not_found_error_handler(request: Request, exc: NotFoundError):
    """Handle not found errors."""
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)},
    )


# Add health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


# Include API router
app.include_router(router, prefix="/api")


if __name__ == "__main__":
    logger.info("Starting PALIOS-TAEY application")
    uvicorn.run(app, host="0.0.0.0", port=8080)
