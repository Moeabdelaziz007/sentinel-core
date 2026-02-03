"""Honeytoken Factory - Generates realistic-looking fake credentials"""

import secrets
import string
import base64
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime

from pydantic import BaseModel, Field


class TokenType(str, Enum):
    """Types of honeytokens supported"""
    AWS_ACCESS_KEY = "aws_access_key"
    OPENAI_API_KEY = "openai_api_key"
    DATABASE_URL = "database_url"
    GENERIC_API_KEY = "generic_api_key"
    JWT_TOKEN = "jwt_token"


class HoneyToken(BaseModel):
    """Schema for honeytoken representation"""
    token_value: str = Field(..., description="The generated honeytoken value")
    token_type: TokenType = Field(..., description="Type of the honeytoken")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    metadata: Dict[str, str] = Field(default_factory=dict)


class HoneyTokenFactory:
    """Factory for generating realistic-looking fake credentials"""
    
    def __init__(self, seed: Optional[str] = None):
        """
        Initialize the honeytoken factory
        
        Args:
            seed: Optional seed for deterministic generation (for testing)
        """
        self.seed = seed
        self._aws_regions = [
            "us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"
        ]
        self._services = [
            "s3", "ec2", "lambda", "rds", "dynamodb"
        ]
    
    def generate_aws_access_key(self) -> HoneyToken:
        """
        Generate realistic AWS access key pair
        
        Returns:
            HoneyToken with AWS-style credentials
        """
        # AWS Access Key ID format: AKIA + 16 random chars
        key_chars = string.ascii_uppercase + string.digits
        access_key_id = "AKIA" + self._generate_random_string(16, key_chars)
        
        # AWS Secret Access Key: 40 random characters
        secret_chars = string.ascii_letters + string.digits + "/+="
        secret_access_key = self._generate_random_string(40, secret_chars)
        
        # Create combined credential string
        credential_pair = (
            f"AWS_ACCESS_KEY_ID={access_key_id}\n"
            f"AWS_SECRET_ACCESS_KEY={secret_access_key}"
        )
        
        return HoneyToken(
            token_value=credential_pair,
            token_type=TokenType.AWS_ACCESS_KEY,
            metadata={
                "access_key_id": access_key_id,
                "region": secrets.choice(self._aws_regions),
                "service": secrets.choice(self._services)
            }
        )
    
    def generate_openai_api_key(self) -> HoneyToken:
        """
        Generate realistic OpenAI API key
        
        Returns:
            HoneyToken with OpenAI-style key
        """
        # OpenAI key format: sk- + prefix + random chars
        prefixes = ["proj", "svcacct", "user", "org"]
        prefix = secrets.choice(prefixes)
        
        # Random part (typically 24-48 chars)
        random_part = self._generate_random_string(
            secrets.choice([24, 32, 48]), 
            string.ascii_letters + string.digits
        )
        
        api_key = f"sk-{prefix}-{random_part}"
        
        return HoneyToken(
            token_value=api_key,
            token_type=TokenType.OPENAI_API_KEY,
            metadata={
                "prefix": prefix,
                "organization": f"org-{self._generate_random_string(12, string.ascii_lowercase + string.digits)}"
            }
        )
    
    def generate_database_url(self) -> HoneyToken:
        """
        Generate realistic database connection string
        
        Returns:
            HoneyToken with database URL
        """
        db_types = ["postgresql", "mysql", "mongodb"]
        db_type = secrets.choice(db_types)
        
        # Generate realistic credentials
        username = secrets.choice(["admin", "root", "postgres", "dbuser"])
        password = self._generate_random_string(16, string.ascii_letters + string.digits + "!@#$%^&*")
        hostname = f"{secrets.choice(['prod', 'staging', 'internal'])}-db.{secrets.choice(['company.com', 'internal', 'local'])}"
        database = secrets.choice(["production", "users", "analytics", "logs"])
        
        if db_type == "postgresql":
            db_url = f"postgresql://{username}:{password}@{hostname}:5432/{database}"
        elif db_type == "mysql":
            db_url = f"mysql://{username}:{password}@{hostname}:3306/{database}"
        else:  # mongodb
            db_url = f"mongodb://{username}:{password}@{hostname}:27017/{database}"
        
        return HoneyToken(
            token_value=db_url,
            token_type=TokenType.DATABASE_URL,
            metadata={
                "db_type": db_type,
                "hostname": hostname,
                "database": database
            }
        )
    
    def generate_generic_api_key(self) -> HoneyToken:
        """
        Generate generic API key with common prefixes
        
        Returns:
            HoneyToken with generic API key
        """
        prefixes = ["sk-", "pk-", "api_", "token_", "secret_"]
        prefix = secrets.choice(prefixes)
        
        # Generate key body
        key_body = self._generate_random_string(
            secrets.choice([32, 48, 64]),
            string.ascii_letters + string.digits + "-_"
        )
        
        api_key = prefix + key_body
        
        return HoneyToken(
            token_value=api_key,
            token_type=TokenType.GENERIC_API_KEY,
            metadata={
                "prefix": prefix.replace("-", "").replace("_", ""),
                "length": str(len(api_key))
            }
        )
    
    def generate_jwt_token(self) -> HoneyToken:
        """
        Generate realistic JWT token structure
        
        Returns:
            HoneyToken with JWT-like structure
        """
        # Header (base64 encoded)
        header = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').decode().rstrip('=')
        
        # Payload (fake claims)
        payload_data = {
            "iss": "https://fake-auth.company.com",
            "sub": f"user-{self._generate_random_string(8, string.ascii_lowercase + string.digits)}",
            "aud": "https://api.company.com",
            "exp": int(datetime.now().timestamp()) + 3600,
            "iat": int(datetime.now().timestamp()),
            "scope": "read:users write:logs"
        }
        
        import json
        payload = base64.urlsafe_b64encode(json.dumps(payload_data).encode()).decode().rstrip('=')
        
        # Signature (fake - just random bytes)
        signature = base64.urlsafe_b64encode(
            self._generate_random_bytes(32)
        ).decode().rstrip('=')
        
        jwt_token = f"{header}.{payload}.{signature}"
        
        return HoneyToken(
            token_value=jwt_token,
            token_type=TokenType.JWT_TOKEN,
            metadata={
                "algorithm": "HS256",
                "issuer": payload_data["iss"]
            }
        )
    
    def generate_batch(self, count: int = 5) -> List[HoneyToken]:
        """
        Generate a batch of different honeytokens
        
        Args:
            count: Number of tokens to generate
            
        Returns:
            List of honeytokens
        """
        generators = [
            self.generate_aws_access_key,
            self.generate_openai_api_key,
            self.generate_database_url,
            self.generate_generic_api_key,
            self.generate_jwt_token
        ]
        
        tokens = []
        for i in range(count):
            generator = generators[i % len(generators)]
            tokens.append(generator())
        
        return tokens
    
    def _generate_random_string(self, length: int, charset: str) -> str:
        """Generate cryptographically secure random string"""
        return ''.join(secrets.choice(charset) for _ in range(length))
    
    def _generate_random_bytes(self, length: int) -> bytes:
        """Generate cryptographically secure random bytes"""
        return secrets.token_bytes(length)


# Global instance
factory = HoneyTokenFactory()