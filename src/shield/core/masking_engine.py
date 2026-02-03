"""Deterministic masking engine with reversible token generation"""

import hashlib
import hmac
import uuid
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import threading

from cryptography.fernet import Fernet
import base64
import os

from ..models.schemas import MaskedEntity, EntityType


@dataclass
class SessionMapping:
    """Stores mapping between original and masked values for a session"""
    original_to_masked: Dict[str, str] = field(default_factory=dict)
    masked_to_original: Dict[str, str] = field(default_factory=dict)
    # (start, end, masked_value)
    entity_positions: List[Tuple[int, int, str]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)


class MaskingEngine:
    """Secure, deterministic masking engine with session-based reversibility"""
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize the masking engine

        Args:
            secret_key: Secret key for encryption 
                       (if None, generates random key)
        """
        if secret_key is None:
            secret_key = base64.urlsafe_b64encode(os.urandom(32)).decode()
        
        self.secret_key = secret_key.encode()
        self._sessions: Dict[str, SessionMapping] = {}
        self._lock = threading.RLock()
        
        # Initialize Fernet for encryption
        self._fernet = Fernet(base64.urlsafe_b64encode(
            hashlib.sha256(self.secret_key).digest()
        ))
    
    def create_session(self, session_id: Optional[str] = None) -> str:
        """
        Create a new masking session
        
        Args:
            session_id: Custom session ID (if None, generates UUID)
            
        Returns:
            Session ID
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        with self._lock:
            self._sessions[session_id] = SessionMapping()
        
        return session_id
    
    def mask_entities(
        self, 
        text: str, 
        entities: List[MaskedEntity], 
        session_id: Optional[str] = None,
        preserve_format: bool = True
    ) -> Tuple[str, List[MaskedEntity]]:
        """
        Mask detected entities in text

        Args:
            text: Original text
            entities: List of entities to mask
            session_id: Session ID for reversibility (creates new if None)
            preserve_format: Whether to preserve original format

        Returns:
            Tuple of (masked_text, updated_entities)
        """
        if not entities:
            return text, entities
        
        # Create session if needed
        if session_id is None:
            session_id = self.create_session()
        
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = SessionMapping()
            
            session = self._sessions[session_id]
            session.last_accessed = datetime.utcnow()
        
        # Sort entities by position (reverse order to avoid index shifting)
        sorted_entities = sorted(
            entities, 
            key=lambda x: x.start_pos, 
            reverse=True
        )
        
        masked_text = text
        updated_entities = []
        
        for entity in sorted_entities:
            original_value = entity.original_text
            masked_value = self._generate_masked_token(
                original_value, 
                entity.entity_type, 
                session_id, 
                preserve_format
            )
            
            # Store mapping
            with self._lock:
                session.original_to_masked[original_value] = masked_value
                session.masked_to_original[masked_value] = original_value
                session.entity_positions.append((
                    entity.start_pos, 
                    entity.end_pos, 
                    masked_value
                ))
            
            # Update entity with masked value
            updated_entity = MaskedEntity(
                original_text=original_value,
                masked_text=masked_value,
                entity_type=entity.entity_type,
                start_pos=entity.start_pos,
                end_pos=entity.end_pos,
                confidence=entity.confidence
            )
            updated_entities.append(updated_entity)
            
            # Apply masking to text
            masked_text = (
                masked_text[:entity.start_pos] + 
                masked_value + 
                masked_text[entity.end_pos:]
            )
        
        return masked_text, updated_entities
    
    def unmask_text(
        self, 
        masked_text: str, 
        session_id: str
    ) -> Tuple[str, List[MaskedEntity]]:
        """
        Restore original values from masked text using session mapping
        
        Args:
            masked_text: Text with masked entities
            session_id: Session ID containing the mapping
            
        Returns:
            Tuple of (original_text, restored_entities)
        """
        with self._lock:
            if session_id not in self._sessions:
                raise ValueError(f"Session {session_id} not found")
            
            session = self._sessions[session_id]
            session.last_accessed = datetime.utcnow()
        
        original_text = masked_text
        restored_entities = []
        
        # Process in reverse order to maintain positions
        for start_pos, end_pos, masked_value in reversed(
            session.entity_positions
        ):
            if masked_value in session.masked_to_original:
                original_value = session.masked_to_original[masked_value]
                
                # Restore in text
                original_text = (
                    original_text[:start_pos] + 
                    original_value + 
                    original_text[start_pos + len(masked_value):]
                )
                
                # Create restored entity record
                restored_entity = MaskedEntity(
                    original_text=original_value,
                    masked_text=masked_value,
                    entity_type=self._infer_entity_type(original_value),
                    start_pos=start_pos,
                    end_pos=start_pos + len(original_value),
                    confidence=1.0
                )
                restored_entities.append(restored_entity)
        
        return original_text, restored_entities
    
    def _generate_masked_token(
        self,
        original_value: str, 
        entity_type: EntityType, 
        session_id: str, 
        preserve_format: bool
    ) -> str:
        """Generate deterministic masked token"""
        if preserve_format:
            return self._format_preserving_mask(original_value, entity_type)
        else:
            return self._cryptographic_mask(original_value, session_id)
    
    def _format_preserving_mask(self, value: str, entity_type: EntityType) -> str:
        """Generate format-preserving masked token"""
        if entity_type == EntityType.EMAIL:
            # Preserve email format: user@domain.com -> masked@domain.com
            if '@' in value:
                local_part, domain = value.split('@', 1)
                return f"masked@{domain}"
            return "masked@example.com"
        
        elif entity_type == EntityType.CREDIT_CARD:
            # Preserve credit card format: keep last 4 digits
            digits_only = ''.join(c for c in value if c.isdigit())
            if len(digits_only) >= 4:
                prefix = 'X' * (len(digits_only) - 4)
                # Reconstruct with original separators
                masked_parts = []
                digit_idx = 0
                for char in value:
                    if char.isdigit():
                        if digit_idx < len(prefix):
                            masked_parts.append(prefix[digit_idx])
                            digit_idx += 1
                        else:
                            masked_parts.append(char)
                    else:
                        masked_parts.append(char)
                return ''.join(masked_parts)
            suffix = value[-4:] if len(value) >= 4 else "XXXX"
            return "XXXX-XXXX-XXXX-" + suffix
        
        elif entity_type == EntityType.PHONE:
            # Preserve phone format: keep last 4 digits
            digits_only = ''.join(c for c in value if c.isdigit())
            if len(digits_only) >= 4:
                prefix = '*' * (len(digits_only) - 4)
                # Reconstruct with original format
                masked_parts = []
                digit_idx = 0
                for char in value:
                    if char.isdigit():
                        if digit_idx < len(prefix):
                            masked_parts.append(prefix[digit_idx])
                            digit_idx += 1
                        else:
                            masked_parts.append(char)
                    else:
                        masked_parts.append(char)
                return ''.join(masked_parts)
            return "***-***-" + value[-4:] if len(value) >= 4 else "****"
        
        elif entity_type == EntityType.SSN:
            # Format: XXX-XX-1234
            return "***-**-" + value[-4:] if len(value) >= 4 else "******"
        
        elif entity_type == EntityType.API_KEY:
            # Preserve length but mask content
            return "*" * len(value)
        
        else:
            # Generic masking
            return f"[{entity_type.value}_MASKED]"
    
    def _cryptographic_mask(self, value: str, session_id: str) -> str:
        """Generate cryptographically secure masked token"""
        # Combine value with session ID for uniqueness
        combined = f"{session_id}:{value}".encode()
        
        # Generate HMAC for deterministic but secure masking
        hmac_obj = hmac.new(self.secret_key, combined, hashlib.sha256)
        digest = hmac_obj.hexdigest()[:16]  # Take first 16 chars
        
        return f"MASK_{digest.upper()}"
    
    def _infer_entity_type(self, value: str) -> EntityType:
        """Infer entity type from value (for restoration)"""
        # Simple heuristic-based inference
        if '@' in value and '.' in value:
            return EntityType.EMAIL
        elif re.search(r'\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}', value):
            return EntityType.CREDIT_CARD
        elif re.search(r'\d{3}-?\d{2}-?\d{4}', value):
            return EntityType.SSN
        elif re.search(r'(sk_|pk_)[a-zA-Z0-9]{32,}', value):
            return EntityType.API_KEY
        elif re.search(r'[\d\-\(\)\s]{10,}', value):
            return EntityType.PHONE
        else:
            return EntityType.CUSTOM
    
    def cleanup_expired_sessions(self, max_age_hours: int = 24):
        """Remove expired sessions"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        with self._lock:
            expired_sessions = [
                sid for sid, session in self._sessions.items()
                if session.last_accessed < cutoff_time
            ]
            
            for sid in expired_sessions:
                del self._sessions[sid]
            
            return len(expired_sessions)
    
    def get_session_stats(self) -> Dict:
        """Get statistics about active sessions"""
        with self._lock:
            return {
                "active_sessions": len(self._sessions),
                "total_mappings": sum(
                    len(session.original_to_masked) 
                    for session in self._sessions.values()
                )
            }


# Global instance
masking_engine = MaskingEngine()