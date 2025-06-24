"""
JWT token management for CV Converter Web Application
Handles JWT creation, validation, and refresh functionality
"""

import jwt
from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

class JWTManager:
    """Manages JWT token operations for user authentication"""
    
    def __init__(self):
        """Initialize JWT manager with configuration from environment"""
        self.secret_key = os.getenv("JWT_SECRET_KEY", "default-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.token_expiry_hours = 12  # As per requirements
        self.refresh_threshold_hours = 1  # Refresh token if less than 1 hour remaining
        
    def create_token(self, user_id: int, username: str, role: str) -> str:
        """
        Create a new JWT token for authenticated user
        
        Args:
            user_id: Internal user ID
            username: Redmine username
            role: User role (admin/user)
            
        Returns:
            JWT token string
        """
        now = datetime.now(UTC)
        payload = {
            "user_id": user_id,
            "username": username,
            "role": role,
            "iat": now,  # Issued at
            "exp": now + timedelta(hours=self.token_expiry_hours)  # Expiration
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded payload dict if valid, None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def is_token_expired(self, token: str) -> bool:
        """
        Check if token is expired
        
        Args:
            token: JWT token string
            
        Returns:
            True if expired, False if valid
        """
        payload = self.verify_token(token)
        return payload is None
    
    def should_refresh_token(self, token: str) -> bool:
        """
        Check if token should be refreshed (less than 1 hour remaining)
        
        Args:
            token: JWT token string
            
        Returns:
            True if should refresh, False otherwise
        """
        payload = self.verify_token(token)
        if not payload:
            return False
            
        exp_timestamp = payload.get("exp")
        if not exp_timestamp:
            return False
            
        expiry_time = datetime.fromtimestamp(exp_timestamp, UTC)
        refresh_time = expiry_time - timedelta(hours=self.refresh_threshold_hours)
        
        return datetime.now(UTC) >= refresh_time
    
    def refresh_token(self, token: str) -> Optional[str]:
        """
        Refresh JWT token if it's still valid but near expiry
        
        Args:
            token: Current JWT token string
            
        Returns:
            New JWT token string if refresh successful, None if failed
        """
        payload = self.verify_token(token)
        if not payload:
            return None
            
        # Create new token with same user data
        return self.create_token(
            user_id=payload["user_id"],
            username=payload["username"],
            role=payload["role"]
        )
    
    def decode_token_payload(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decode token payload without verification (for debugging)
        
        Args:
            token: JWT token string
            
        Returns:
            Payload dict if decodable, None if malformed
        """
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except jwt.InvalidTokenError:
            return None 