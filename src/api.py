"""FastAPI application for Sentinel Shield"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import uvicorn
import logging

from .shield.core.piimasker import shield
from .shield.models.schemas import (
    MaskRequest,
    MaskResponse,
    UnmaskRequest,
    UnmaskResponse,
    HealthCheckResponse
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Sentinel Shield API",
    description="AI Security Middleware for PII Protection",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Health"])
async def root() -> Dict[str, str]:
    """Root endpoint"""
    return {"message": "🛡️ Sentinel Shield - AI Security Middleware"}

@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    try:
        health_data = shield.health_check()
        return HealthCheckResponse(**health_data)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mask", response_model=MaskResponse, tags=["PII Protection"])
async def mask_pii(request: MaskRequest):
    """
    Mask PII entities in text
    
    Detects and masks sensitive information like emails, credit cards,
    phone numbers, and API keys while preserving text structure.
    """
    try:
        logger.info(f"Masking request received - Mode: {request.mode}")
        response = shield.mask(request)
        logger.info(f"Masking completed in {response.processing_time_ms:.2f}ms")
        return response
    except Exception as e:
        logger.error(f"Masking failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/unmask", response_model=UnmaskResponse, tags=["PII Protection"])
async def unmask_pii(request: UnmaskRequest):
    """
    Restore original PII values from masked text
    
    Requires the session ID used during the original masking operation.
    """
    try:
        logger.info(f"Unmasking request received for session {request.session_id}")
        response = shield.unmask(request)
        logger.info(f"Unmasking completed in {response.processing_time_ms:.2f}ms")
        return response
    except Exception as e:
        logger.error(f"Unmasking failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/supported-types", tags=["Metadata"])
async def get_supported_entity_types():
    """Get list of supported PII entity types"""
    try:
        types = shield.regex_engine.get_supported_entity_types()
        return {"entity_types": [t.value for t in types]}
    except Exception as e:
        logger.error(f"Failed to get entity types: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats", tags=["Monitoring"])
async def get_statistics():
    """Get system statistics and performance metrics"""
    try:
        health_data = shield.health_check()
        # Add more detailed statistics here
        stats = {
            **health_data,
            "performance_metrics": {
                "average_latency_ms": 0,  # TODO: Implement latency tracking
                "peak_memory_mb": 0,      # TODO: Implement memory tracking
            }
        }
        return stats
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "src.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )