"""Input preprocessing and text normalization utilities"""

import unicodedata
from typing import Tuple, List
from ..models.schemas import ProcessingMode


class TextPreprocessor:
    """Handles text normalization and preprocessing 
    for optimal PII detection"""
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalize text for consistent processing
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        # Normalize Unicode characters
        normalized = unicodedata.normalize('NFKC', text)
        
        # Convert to consistent case for certain operations
        # (but preserve original for masking)
        return normalized
    
    @staticmethod
    def estimate_complexity(text: str) -> Tuple[int, int, bool]:
        """
        Estimate text complexity for routing decisions
        
        Returns:
            Tuple of (character_count, entity_density_estimate, is_complex)
        """
        char_count = len(text)
        
        # Simple heuristic for entity density
        # Count potential entity indicators
        entity_indicators = [
            '@',  # email
            '.',  # email/URL
            '-',  # formatted numbers
            '(',  # phone numbers
            ')',  # phone numbers
            '+',  # international numbers
            '_',  # API keys
            '='   # encoded data
        ]
        
        indicator_count = sum(
            text.count(indicator) 
            for indicator in entity_indicators
        )
        density_ratio = indicator_count / max(char_count, 1)
        
        # Complexity thresholds
        is_complex = (
            char_count > 1000 or  # Long text
            density_ratio > 0.1 or  # High entity density
            any(c in text for c in ['{', '}', '[', ']'])  # Structured data
        )
        
        return char_count, int(density_ratio * 100), is_complex
    
    @staticmethod
    def suggest_processing_mode(text: str) -> ProcessingMode:
        """
        Suggest optimal processing mode based on text characteristics
        
        Args:
            text: Input text
            
        Returns:
            Recommended ProcessingMode
        """
        complexity = TextPreprocessor.estimate_complexity(text)
        char_count, density, is_complex = complexity
        
        # Decision logic for mode selection
        if char_count < 100:
            # Short texts - use speed mode for maximum performance
            return ProcessingMode.SPEED
        elif char_count > 2000 or is_complex:
            # Long or complex texts - use accuracy mode
            return ProcessingMode.ACCURACY
        else:
            # Medium texts - balanced approach
            return ProcessingMode.BALANCED
    
    @staticmethod
    def chunk_large_text(text: str, max_chunk_size: int = 1000) -> List[str]:
        """
        Split large text into manageable chunks
        
        Args:
            text: Input text
            max_chunk_size: Maximum chunk size in characters
            
        Returns:
            List of text chunks
        """
        if len(text) <= max_chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + max_chunk_size, len(text))
            
            # Try to split at sentence boundaries
            if end < len(text):
                # Look for sentence endings within reasonable window
                split_points = ['. ', '! ', '? ', '\n\n']
                best_split = end
                
                for i in range(max(0, end - 100), end):
                    if any(text[i:i+2] == point for point in split_points):
                        best_split = i + 2
                        break
                
                end = best_split
            
            chunks.append(text[start:end])
            start = end
        
        return chunks


# Global instance
preprocessor = TextPreprocessor()