"""High-performance regex engine using RE2 for PII pattern detection"""

try:
    import re2 as re
except ImportError:
    import re  # Fallback to standard library
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

from ..models.schemas import EntityType, MaskedEntity


class PatternStrength(Enum):
    """Confidence level of pattern matching"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class PIIPattern:
    """Represents a PII detection pattern"""
    name: str
    entity_type: EntityType
    pattern: str
    strength: PatternStrength
    format_preserver: Optional[str] = None


class RegexEngine:
    """Optimized regex engine using RE2 for PII detection"""
    
    def __init__(self):
        self.patterns: Dict[EntityType, List[PIIPattern]] = {}
        self.compiled_patterns: Dict[str, re.Regex] = {}
        self._initialize_patterns()
        self._compile_patterns()
    
    def _initialize_patterns(self):
        """Initialize common PII patterns"""
        # Email patterns
        email_patterns = [
            PIIPattern(
                name="standard_email",
                entity_type=EntityType.EMAIL,
                pattern=(
                    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                ),
                strength=PatternStrength.HIGH
            )
        ]
        
        # Credit card patterns
        cc_patterns = [
            PIIPattern(
                name="major_brands",
                entity_type=EntityType.CREDIT_CARD,
                pattern=(
                    r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|'
                    r'3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b'
                ),
                strength=PatternStrength.HIGH,
                format_preserver=r'[0-9]'
            )
        ]
        
        # Phone number patterns
        phone_patterns = [
            PIIPattern(
                name="us_phone",
                entity_type=EntityType.PHONE,
                pattern=(
                    r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?'
                    r'([0-9]{3})[-.\s]?([0-9]{4})\b'
                ),
                strength=PatternStrength.HIGH
            )
        ]
        
        # Social Security Number patterns
        ssn_patterns = [
            PIIPattern(
                name="us_ssn",
                entity_type=EntityType.SSN,
                pattern=r'\b\d{3}-?\d{2}-?\d{4}\b',
                strength=PatternStrength.HIGH
            )
        ]
        
        # API Key patterns
        api_key_patterns = [
            PIIPattern(
                name="secret_keys",
                entity_type=EntityType.API_KEY,
                pattern=r'\b(sk_|pk_)[a-zA-Z0-9]{32,}\b',
                strength=PatternStrength.HIGH
            )
        ]
        
        # Store patterns by entity type
        self.patterns = {
            EntityType.EMAIL: email_patterns,
            EntityType.CREDIT_CARD: cc_patterns,
            EntityType.PHONE: phone_patterns,
            EntityType.SSN: ssn_patterns,
            EntityType.API_KEY: api_key_patterns
        }
    
    def _compile_patterns(self):
        """Compile all regex patterns for performance"""
        for entity_type, patterns in self.patterns.items():
            for pattern in patterns:
                try:
                    compiled = re.compile(pattern.pattern)
                    self.compiled_patterns[pattern.name] = compiled
                except Exception as e:
                    raise ValueError(
                        f"Invalid regex pattern '{pattern.name}': {e}"
                    )
    
    def detect_entities(
        self, 
        text: str, 
        entity_types: Optional[List[EntityType]] = None
    ) -> List[MaskedEntity]:
        """
        Detect PII entities in text using regex patterns
        
        Args:
            text: Input text to scan
            entity_types: Specific entity types to detect (None = all)
            
        Returns:
            List of detected entities with positions and confidence
        """
        if not text:
            return []
        
        entities: List[MaskedEntity] = []
        search_types = entity_types or list(self.patterns.keys())
        
        for entity_type in search_types:
            if entity_type not in self.patterns:
                continue
                
            for pattern in self.patterns[entity_type]:
                compiled_pattern = self.compiled_patterns.get(pattern.name)
                if not compiled_pattern:
                    continue
                
                # Find all matches
                for match in compiled_pattern.finditer(text):  # type: ignore
                    # Calculate confidence based on pattern strength
                    confidence_map = {
                        PatternStrength.HIGH: 0.95,
                        PatternStrength.MEDIUM: 0.80,
                        PatternStrength.LOW: 0.60
                    }
                    
                    confidence = confidence_map[pattern.strength]
                    
                    # Adjust confidence based on match context
                    confidence = self._adjust_confidence(
                        match, 
                        pattern, 
                        confidence
                    )
                    
                    entity = MaskedEntity(
                        original_text=match.group(),
                        masked_text="",
                        entity_type=entity_type,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        confidence=confidence
                    )
                    entities.append(entity)
        
        # Sort by position and remove overlaps
        entities.sort(key=lambda x: (x.start_pos, -x.confidence))
        return self._remove_overlapping_entities(entities)
    
    def _adjust_confidence(
        self, 
        match: object, 
        pattern: PIIPattern, 
        base_confidence: float
    ) -> float:
        """Adjust confidence based on match characteristics"""
        matched_text = match.group()
        
        # Boost confidence for exact format matches
        if pattern.entity_type == EntityType.CREDIT_CARD:
            # Check if it's a valid credit card number
            cleaned = re.sub(r'[^0-9]', '', matched_text)
            if len(cleaned) >= 13 and self._luhn_check(cleaned):
                return min(1.0, base_confidence + 0.1)
        
        elif pattern.entity_type == EntityType.EMAIL:
            # Check email validity
            if '@' in matched_text and '.' in matched_text.split('@')[1]:
                return min(1.0, base_confidence + 0.05)
        
        return base_confidence
    
    def _luhn_check(self, card_number: str) -> bool:
        """Validate credit card number using Luhn algorithm"""
        def digits_of(n):
            return [int(d) for d in str(n)]
        
        digits = digits_of(card_number)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d * 2))
        return checksum % 10 == 0
    
    def _remove_overlapping_entities(
        self, 
        entities: List[MaskedEntity]
    ) -> List[MaskedEntity]:
        """Remove overlapping entities, keeping higher confidence ones"""
        if len(entities) <= 1:
            return entities
        
        result = []
        i = 0
        
        while i < len(entities):
            current = entities[i]
            j = i + 1
            condition = (
                j < len(entities) and 
                entities[j].start_pos < current.end_pos
            )
            while condition:
                # Overlap detected - keep higher confidence
                if entities[j].confidence > current.confidence:
                    current = entities[j]
                j += 1
            
            result.append(current)
            i = j
        
        return result
    
    def get_supported_entity_types(self) -> List[EntityType]:
        """Get list of supported entity types"""
        return list(self.patterns.keys())


# Singleton instance
regex_engine = RegexEngine()