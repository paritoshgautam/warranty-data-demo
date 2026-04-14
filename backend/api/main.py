"""
FastAPI Main Application
Optimized warranty analytics API with proper error handling and CORS
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import after logging setup to avoid circular imports
from .services.data_service import DataService
from . import dependencies

# Global data service instance
data_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup/shutdown"""
    global data_service
    
    # Startup
    logger.info("Starting Warranty Analytics API...")
    try:
        data_service = DataService()
        data_service.load_data()
        dependencies.set_data_service(data_service)
        logger.info(f"Loaded {len(data_service.get_data())} warranty records")
        yield
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down Warranty Analytics API...")

# Create FastAPI app
app = FastAPI(
    title="Warranty Analytics API",
    description="High-performance API for warranty data analysis",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers after app creation
from .routes import warranty, analytics

# Include routers
app.include_router(warranty.router, prefix="/api/warranty", tags=["warranty"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "Warranty Analytics API",
        "version": "2.0.0",
        "status": "operational",
        "endpoints": {
            "warranty": "/api/warranty",
            "analytics": "/api/analytics",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        record_count = len(data_service.get_data()) if data_service else 0
        return {
            "status": "healthy",
            "records_loaded": record_count
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
