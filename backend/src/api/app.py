"""
FastAPI application for AWS CIEM Tool
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time

from ..utils import settings, app_logger as logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting AWS CIEM Tool API")
    logger.info(f"Environment: {'Development' if settings.debug else 'Production'}")
    logger.info(f"AWS Region: {settings.aws_default_region}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AWS CIEM Tool API")


# Create FastAPI application
app = FastAPI(
    title="AWS CIEM Tool API",
    description="Cloud Infrastructure Entitlement Management for AWS",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AWS CIEM Tool",
        "version": "0.1.0"
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "AWS CIEM Tool API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }


# AWS connection test endpoint
@app.get("/api/v1/aws/test", tags=["AWS"])
async def test_aws_connection():
    """Test AWS connection and permissions"""
    from ..utils import aws_client_manager
    
    try:
        results = aws_client_manager.test_connection()
        return JSONResponse(content=results)
    except Exception as e:
        logger.error(f"AWS connection test failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The requested resource {request.url.path} was not found"
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=settings.debug
    )
