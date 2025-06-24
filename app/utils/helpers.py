"""
Utility functions and helpers for the CV Converter Web Application
"""

import streamlit as st
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import os
from pathlib import Path

def show_success_message(message: str):
    """Display success message with consistent styling"""
    st.success(f"✅ {message}")

def show_error_message(message: str):
    """Display error message with consistent styling"""
    st.error(f"❌ {message}")

def show_warning_message(message: str):
    """Display warning message with consistent styling"""
    st.warning(f"⚠️ {message}")

def show_info_message(message: str):
    """Display info message with consistent styling"""
    st.info(f"ℹ️ {message}")

def format_datetime(dt: Optional[datetime]) -> str:
    """
    Format datetime for display
    
    Args:
        dt: Datetime object to format
        
    Returns:
        Formatted datetime string
    """
    if not dt:
        return "Never"
    
    now = datetime.now()
    diff = now - dt
    
    if diff.days == 0:
        if diff.seconds < 3600:  # Less than 1 hour
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:  # Less than 1 day
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.days == 1:
        return "Yesterday"
    elif diff.days < 7:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    else:
        return dt.strftime("%Y-%m-%d %H:%M")

def validate_file_upload(uploaded_file, allowed_extensions: List[str], max_size_mb: int = 10) -> tuple[bool, Optional[str]]:
    """
    Validate uploaded file
    
    Args:
        uploaded_file: Streamlit uploaded file object
        allowed_extensions: List of allowed file extensions (without dots)
        max_size_mb: Maximum file size in MB
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not uploaded_file:
        return False, "No file uploaded"
    
    # Check file extension
    file_extension = uploaded_file.name.split('.')[-1].lower()
    if file_extension not in [ext.lower() for ext in allowed_extensions]:
        return False, f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
    
    # Check file size
    file_size_mb = uploaded_file.size / (1024 * 1024)  # Convert bytes to MB
    if file_size_mb > max_size_mb:
        return False, f"File too large. Maximum size: {max_size_mb}MB"
    
    return True, None

def ensure_directory_exists(directory_path: str):
    """
    Ensure directory exists, create if not
    
    Args:
        directory_path: Path to directory
    """
    Path(directory_path).mkdir(parents=True, exist_ok=True)

def clean_filename(filename: str) -> str:
    """
    Clean filename for safe file system storage
    
    Args:
        filename: Original filename
        
    Returns:
        Cleaned filename
    """
    # Remove or replace problematic characters
    import re
    # Replace problematic characters with underscores
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove extra spaces and trim
    cleaned = ' '.join(cleaned.split())
    return cleaned

def get_file_size_display(size_bytes: int) -> str:
    """
    Convert file size in bytes to human readable format
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        Human readable file size string
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

def create_download_button(file_content: bytes, filename: str, mime_type: str = "application/octet-stream") -> bool:
    """
    Create download button for file content
    
    Args:
        file_content: File content as bytes
        filename: Name for downloaded file
        mime_type: MIME type of file
        
    Returns:
        True if download button was clicked
    """
    return st.download_button(
        label=f"📥 Download {filename}",
        data=file_content,
        file_name=filename,
        mime=mime_type
    )

def display_user_card(user, show_admin_actions: bool = False):
    """
    Display user information card
    
    Args:
        user: User object to display
        show_admin_actions: Whether to show admin action buttons
    """
    with st.container():
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.write(f"**{user.username}**")
            if user.custom_fields:
                # Display relevant custom fields
                for key, value in user.custom_fields.items():
                    if value:  # Only show non-empty fields
                        st.write(f"*{key}*: {value}")
        
        with col2:
            role_color = "🔴" if user.role == "admin" else "🔵"
            st.write(f"Role: {role_color} {user.role.title()}")
            st.write(f"Conversions: {user.conversion_count}")
        
        with col3:
            st.write(f"Last Login: {format_datetime(user.last_login)}")
            st.write(f"Member Since: {format_datetime(user.created_at)}")
        
        if show_admin_actions and user.role != "admin":
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button(f"Make Admin", key=f"admin_{user.id}"):
                    return "make_admin", user.id
            with col2:
                if st.button(f"Remove User", key=f"remove_{user.id}"):
                    return "remove_user", user.id
    
    st.divider()
    return None, None

def show_loading_spinner(message: str = "Loading..."):
    """
    Show loading spinner with message
    
    Args:
        message: Loading message to display
    """
    with st.spinner(message):
        return True

def init_session_state_defaults():
    """Initialize default session state values"""
    defaults = {
        "step": 1,
        "uploaded_file": None,
        "selected_ticket": None,
        "processing_status": None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def reset_wizard_state():
    """Reset wizard state to beginning"""
    wizard_keys = ["step", "uploaded_file", "selected_ticket", "processing_status"]
    for key in wizard_keys:
        if key in st.session_state:
            del st.session_state[key]
    
    # Reinitialize defaults
    init_session_state_defaults()

def get_environment_status() -> Dict[str, Any]:
    """
    Get environment configuration status for admin dashboard
    
    Returns:
        Dictionary with environment status information
    """
    required_env_vars = [
        "REDMINE_URL", "JWT_SECRET_KEY", "SQLITE_DB_PATH"
    ]
    
    optional_env_vars = [
        "REDMINE_API_KEY", "DEFAULT_PROJECT_ID", "TEMP_FILES_PATH", "MAX_FILE_SIZE_MB"
    ]
    
    status = {
        "required": {},
        "optional": {},
        "all_required_set": True
    }
    
    for var in required_env_vars:
        value = os.getenv(var)
        status["required"][var] = {
            "set": bool(value),
            "value": value[:10] + "..." if value and len(value) > 10 else value
        }
        if not value:
            status["all_required_set"] = False
    
    for var in optional_env_vars:
        value = os.getenv(var)
        status["optional"][var] = {
            "set": bool(value),
            "value": value[:10] + "..." if value and len(value) > 10 else value
        }
    
    return status 