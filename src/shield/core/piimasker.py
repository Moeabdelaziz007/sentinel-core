"""Main PIIMasker class - orchestrates the complete shielding pipeline"""

import time
from typing import List, Optional
from datetime import datetime

from ..models.schemas import (
    MaskRequest, 
    MaskResponse, 
    UnmaskRequest, 
    UnmaskResponse,
    ProcessingMode,
    MaskedEntity,
    EntityType
)
from .regex_engine import regex_engine
from .masking_engine import masking_engine
from ..utils.preprocessing import preprocessor


class PIIMasker:
    """Main orchestrator for PII detection and masking operations"""
    
    def __init__(self):
        self.regex_engine = regex_engine
        self.masking_engine = masking_engine
        self.preprocessor = preprocessor
        self._startup_time = datetime.utcnow()
        self._request_count = 0
    
    def mask(self, request: MaskRequest) -> MaskResponse:
        """
        Main masking operation - detects and masks PII in text
        
        Args:
            request: Masking request with text and configuration
            
        Returns:
            MaskResponse with masked text and metadata
        """
        start_time = time.perf_counter()
        self._request_count += 1
        
        # Input validation and preprocessing
        if not request.text.strip():
            return MaskResponse(
                original_text=request.text,
                masked_text=request.text,
                entities_found=[],
                processing_time_ms=0.0,
                mode_used=request.mode,
                session_id=request.session_id,
                timestamp=datetime.utcnow()
            )
        
        # Normalize text
        normalized_text = self.preprocessor.normalize_text(request.text)
        
        # Auto-select mode if not specified
        mode_used = request.mode
        if mode_used == ProcessingMode.BALANCED:
            suggested_mode = self.preprocessor.suggest_processing_mode(normalized_text)
            mode_used = suggested_mode
        
        # Detect entities based on mode
        entities = self._detect_entities(
            normalized_text, 
            mode_used, 
            request.entity_types
        )
        
        # Apply masking
        session_id = request.session_id or self.masking_engine.create_session()
        masked_text, updated_entities = self.masking_engine.mask_entities(
            normalized_text,
            entities,
            session_id,
            request.preserve_format
        )
        
        # Calculate processing time
        processing_time = (time.perf_counter() - start_time) * 1000
        
        return MaskResponse(
            original_text=request.text,
            masked_text=masked_text,
            entities_found=updated_entities,
            processing_time_ms=processing_time,
            mode_used=mode_used,
            session_id=session_id,
            timestamp=datetime.utcnow()
        )
    
    def unmask(self, request: UnmaskRequest) -> UnmaskResponse:
        """
        Restore original PII values from masked text
        
        Args:
            request: Unmasking request with session ID
            
        Returns:
            UnmaskResponse with restored text
        """
        start_time = time.perf_counter()
        
        try:
            original_text, restored_entities = self.masking_engine.unmask_text(
                request.masked_text,
                request.session_id
            )
            
            processing_time = (time.perf_counter() - start_time) * 1000
            
            return UnmaskResponse(
                masked_text=request.masked_text,
                original_text=original_text,
                entities_restored=restored_entities,
                processing_time_ms=processing_time,
                timestamp=datetime.utcnow()
            )
        
        except ValueError as e:
            raise ValueError(f"Unmasking failed: {str(e)}")
    
    def _detect_entities(
        self,
        text: str,
        mode: ProcessingMode,
        entity_types: Optional[List[EntityType]] = None
    ) -> List[MaskedEntity]:
        """Detect entities using appropriate engine based on mode"""
        if mode == ProcessingMode.SPEED:
            # Regex-only detection for maximum speed
            return self.regex_engine.detect_entities(text, entity_types)
        
        elif mode == ProcessingMode.ACCURACY:
            # TODO: Implement Presidio integration for full accuracy
            # For now, fall back to regex with enhanced patterns
            return self.regex_engine.detect_entities(text, entity_types)
        
        else:  # BALANCED mode
            # Use regex engine as primary detector
            return self.regex_engine.detect_entities(text, entity_types)
    
    def health_check(self) -> dict:
        """Return health check information"""
        uptime = (datetime.utcnow() - self._startup_time).total_seconds()
        
        stats = self.masking_engine.get_session_stats()
        
        return {
            "status": "healthy",
            "version": "0.1.0",
            "uptime_seconds": uptime,
            "requests_processed": self._request_count,
            "active_sessions": stats["active_sessions"],
            "total_mappings": stats["total_mappings"],
            "performance_metrics": {
                "average_latency_ms": 0,
                "peak_memory_mb": 0
            }
        }


# Global instance
shield = PIIMasker()