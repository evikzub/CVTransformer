"""
Authentication service that coordinates JWT and Redmine authentication
Main entry point for all authentication operations
"""

from typing import Optional, Dict, Any, Tuple
import streamlit as st
from datetime import datetime

from .jwt_manager import JWTManager
from .redmine_client import RedmineClient
from ..models.user import UserManager, User
import os
from dotenv import load_dotenv

load_dotenv()

class AuthService:
    """Main authentication service handling login, session management, and user operations"""
    
    def __init__(self):
        """Initialize authentication service with required components"""
        self.jwt_manager = JWTManager()
        self.redmine_client = RedmineClient()
        
        # Initialize user manager with database path from environment
        db_path = os.getenv("SQLITE_DB_PATH", "data/cv_converter.db")
        self.user_manager = UserManager(db_path)
    
    def authenticate_user(self, username: str, password: str) -> Tuple[bool, Optional[str], Optional[User]]:
        """
        Authenticate user using Redmine credentials and create/update local user record
        
        Args:
            username: Redmine username
            password: Redmine password
            
        Returns:
            Tuple of (success, error_message, user_object)
        """
        try:
            # Authenticate with Redmine
            redmine_user_data = self.redmine_client.authenticate_user(username, password)
            
            if not redmine_user_data:
                return False, "Invalid Redmine credentials", None
            
            # Extract user information from Redmine response
            user_info = redmine_user_data.get("user", {})
            redmine_user_id = user_info.get("id")
            redmine_username = user_info.get("login", username)
            custom_fields = user_info.get("custom_fields", [])
            
            if not redmine_user_id:
                return False, "Unable to retrieve user information from Redmine", None
            
            # Convert custom fields to dict for storage
            custom_fields_dict = {}
            if custom_fields:
                for field in custom_fields:
                    custom_fields_dict[field.get("name", "")] = field.get("value", "")
            
            # Check if user exists in local database
            existing_user = self.user_manager.get_user_by_redmine_id(redmine_user_id)
            
            if existing_user:
                # Update last login for existing user
                self.user_manager.update_last_login(existing_user.id)
                user = existing_user
            else:
                # Create new user in local database
                user = self.user_manager.create_user(
                    redmine_user_id=redmine_user_id,
                    username=redmine_username,
                    custom_fields=custom_fields_dict
                )
            
            return True, None, user
            
        except Exception as e:
            return False, f"Authentication error: {str(e)}", None
    
    def create_session(self, user: User) -> str:
        """
        Create JWT session for authenticated user
        
        Args:
            user: Authenticated user object
            
        Returns:
            JWT token string
        """
        return self.jwt_manager.create_token(
            user_id=user.id,
            username=user.username,
            role=user.role
        )
    
    def get_current_user(self) -> Optional[User]:
        """
        Get current authenticated user from session
        
        Returns:
            User object if authenticated, None if not authenticated
        """
        token = st.session_state.get("jwt_token")
        if not token:
            return None
        
        # Check if token needs refresh
        if self.jwt_manager.should_refresh_token(token):
            new_token = self.jwt_manager.refresh_token(token)
            if new_token:
                st.session_state.jwt_token = new_token
                token = new_token
        
        # Verify token and get user
        payload = self.jwt_manager.verify_token(token)
        if not payload:
            # Token is invalid, clear session
            self.logout()
            return None
        
        user_id = payload.get("user_id")
        if user_id:
            return self.user_manager.get_user_by_id(user_id)
        
        return None
    
    def is_authenticated(self) -> bool:
        """
        Check if user is currently authenticated
        
        Returns:
            True if authenticated, False otherwise
        """
        return self.get_current_user() is not None
    
    def is_admin(self) -> bool:
        """
        Check if current user has admin role
        
        Returns:
            True if admin, False otherwise
        """
        user = self.get_current_user()
        return user is not None and user.role == "admin"
    
    def store_user_credentials(self, username: str, password: str):
        """
        Store user credentials temporarily in session for API calls
        Note: Only stores in memory for current session
        
        Args:
            username: Redmine username
            password: Redmine password
        """
        # Store credentials in session state (temporary)
        st.session_state.redmine_username = username
        st.session_state.redmine_password = password
    
    def get_user_credentials(self) -> Optional[Tuple[str, str]]:
        """
        Get stored user credentials from session
        
        Returns:
            Tuple of (username, password) if available, None otherwise
        """
        username = st.session_state.get("redmine_username")
        password = st.session_state.get("redmine_password")
        
        if username and password:
            return username, password
        return None
    
    def clear_user_credentials(self):
        """Clear stored user credentials from session"""
        if "redmine_username" in st.session_state:
            del st.session_state.redmine_username
        if "redmine_password" in st.session_state:
            del st.session_state.redmine_password
    
    def login(self, username: str, password: str) -> Tuple[bool, Optional[str]]:
        """
        Complete login process: authenticate and create session
        
        Args:
            username: Redmine username
            password: Redmine password
            
        Returns:
            Tuple of (success, error_message)
        """
        success, error, user = self.authenticate_user(username, password)
        
        if success and user:
            # Create JWT session
            token = self.create_session(user)
            st.session_state.jwt_token = token
            
            # Store user info in session for quick access
            st.session_state.user_id = user.id
            st.session_state.username = user.username
            st.session_state.user_role = user.role
            
            # Store credentials for API calls (session only)
            self.store_user_credentials(username, password)
            
            return True, None
        
        return False, error
    
    def logout(self):
        """Clear user session and logout"""
        # Clear all session state related to authentication
        session_keys_to_clear = [
            "jwt_token", "user_id", "username", "user_role",
            "redmine_username", "redmine_password"  # Clear credentials too
        ]
        
        for key in session_keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
    
    def require_authentication(self):
        """
        Authentication decorator/middleware for pages
        Redirects to login if not authenticated
        """
        if not self.is_authenticated():
            st.error("🔒 Please log in to access this page")
            st.stop()
    
    def require_admin(self):
        """
        Admin authorization decorator/middleware for pages
        Redirects if not admin user
        """
        self.require_authentication()
        
        if not self.is_admin():
            st.error("🚫 Admin access required")
            st.stop()
    
    def get_user_credentials_from_session(self) -> Optional[Tuple[str, str]]:
        """
        Get stored user credentials from session for API calls
        Note: In production, consider more secure credential storage
        
        Returns:
            Tuple of (username, password) if available, None otherwise
        """
        # For now, we don't store passwords in session for security
        # This would need to be implemented differently in production
        return None
    
    def test_redmine_connection(self) -> bool:
        """
        Test connection to Redmine API
        
        Returns:
            True if connection successful, False if failed
        """
        return self.redmine_client.test_connection() 