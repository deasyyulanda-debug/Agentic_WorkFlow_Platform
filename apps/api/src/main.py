"""
Agentic Workflow Platform - FastAPI Backend
Main application entry point
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

# Database initialization
from db.database import init_db

# Core infrastructure
from core import (
    settings,
    init_security,
    setup_logging,
    get_logger,
    AppException,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown tasks.
    """
    # Startup: Initialize logging
    logger = setup_logging(
        log_level=settings.LOG_LEVEL,
        log_format=settings.LOG_FORMAT
    )
    logger.info(
        f"Starting {settings.APP_NAME} v{settings.APP_VERSION}",
        extra={"environment": settings.ENVIRONMENT}
    )
    
    # Startup: Initialize security layer
    init_security(settings.SECRET_KEY)
    logger.info("Security layer initialized")
    
    # Startup: Initialize database
    await init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown: Cleanup resources
    logger.info("Shutting down application")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="UI-driven workflow platform with built-in safety rails",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler for custom exceptions
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """
    Handle custom application exceptions.
    Converts domain exceptions to proper HTTP responses.
    """
    logger = get_logger(__name__)
    logger.error(
        f"Application error: {exc.message}",
        extra={"status_code": exc.status_code, "details": exc.details}
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "details": exc.details
        }
    )


# Global exception handler for unexpected errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected exceptions.
    Logs error and returns generic 500 response.
    """
    logger = get_logger(__name__)
    logger.exception("Unexpected error occurred")
    
    # Don't leak internal error details in production
    if settings.is_production:
        message = "An internal error occurred"
    else:
        message = str(exc)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": message}
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


# Import routers
from api.settings_router import router as settings_router
from api.workflows_router import router as workflows_router
from api.runs_router import router as runs_router
from api.artifacts_router import router as artifacts_router
from api.rag_router import router as rag_router

# Register routers
app.include_router(settings_router, prefix="/api/v1/settings", tags=["Settings"])
app.include_router(workflows_router, prefix="/api/v1/workflows", tags=["Workflows"])
app.include_router(runs_router, prefix="/api/v1/runs", tags=["Runs"])
app.include_router(artifacts_router, prefix="/api/v1/artifacts", tags=["Artifacts"])
app.include_router(rag_router, prefix="/api/v1/rag", tags=["RAG Pipeline"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD
    )
