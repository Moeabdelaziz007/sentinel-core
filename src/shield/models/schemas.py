"""Pydantic models for API schemas and data validation"""

from typing import Dict, List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


class EntityType(str, Enum):
    """Supported PII entity types"""
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    CREDIT_CARD = "CREDIT_CARD"
    SSN = "SSN"
    API_KEY = "API_KEY"
    ADDRESS = "ADDRESS"
    NAME = "NAME"
    CUSTOM = "CUSTOM"


class ProcessingMode(str, Enum):
    """Processing modes for different performance requirements"""
    SPEED = "speed"  # Regex-only, fastest
    BALANCED = "balanced"  # Hybrid approach
    ACCURACY = "accuracy"  # Full NLP, most accurate


class MaskRequest(BaseModel):
    """Request model for PII masking"""
    text: str = Field(..., description="Text to be processed for PII masking")
    mode: ProcessingMode = Field(
        default=ProcessingMode.BALANCED,
        description="Processing mode - affects speed vs accuracy tradeoff"
    )
    entity_types: Optional[List[EntityType]] = Field(
        default=None,
        description="Specific entity types to detect (None = all)"
    )
    preserve_format: bool = Field(
        default=True,
        description="Whether to preserve format of masked entities"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for reversible masking"
    )


class MaskedEntity(BaseModel):
    """Represents a detected and masked entity"""
    original_text: str
    masked_text: str
    entity_type: EntityType
    start_pos: int
    end_pos: int
    confidence: float = Field(ge=0.0, le=1.0)


class MaskResponse(BaseModel):
    """Response model for PII masking"""
    original_text: str
    masked_text: str
    entities_found: List[MaskedEntity]
    processing_time_ms: float
    mode_used: ProcessingMode
    session_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class UnmaskRequest(BaseModel):
    """Request model for PII unmasking"""
    masked_text: str
    session_id: str


class UnmaskResponse(BaseModel):
    """Response model for PII unmasking"""
    masked_text: str
    original_text: str
    entities_restored: List[MaskedEntity]
    processing_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    version: str
    uptime_seconds: float
    performance_metrics: Dict[str, Union[int, float]]