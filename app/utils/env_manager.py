"""
Environment variable management utility for CV Converter Web Application
Handles .env file operations with validation and hot-reload capability
"""

import os
import stat
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dotenv import load_dotenv, set_key, unset_key
import streamlit as st

class EnvManager:
    """Manages environment variables with hot-reload and validation"""
    
    def __init__(self, env_file_path: str = ".env"):
        """Initialize environment manager"""
        self.env_file_path = env_file_path
        self.env_file = Path(env_file_path)
        
        # Configurable settings (visible in admin interface)
        self.configurable_vars = {
            "DEFAULT_PROJECT_ID": {
                "type": "int",
                "description": "Default Redmine project ID for new tickets",
                "default": "1"
            },
            "MAX_FILE_SIZE_MB": {
                "type": "int", 
                "description": "Maximum file size in MB for uploads",
                "default": "10"
            },
            "TICKETS_PER_PAGE": {
                "type": "int",
                "description": "Number of tickets to display per page",
                "default": "15"
            },
            "REDMINE_URL": {
                "type": "url",
                "description": "Redmine instance URL",
                "default": "https://your-redmine-instance.com"
            },
            "TEMP_FILES_PATH": {
                "type": "path",
                "description": "Path for temporary file storage",
                "default": "data/temp"
            }
        }
        
        # Hidden settings (not configurable in admin interface)
        self.hidden_vars = {
            "JWT_SECRET_KEY",
            "REDMINE_API_KEY"
        }
    
    def validate_file_permissions(self) -> Tuple[bool, Optional[str]]:
        """
        Validate that we can read and write to the .env file
        
        Returns:
            Tuple of (can_write, error_message)
        """
        try:
            # Check if file exists
            if not self.env_file.exists():
                # Try to create it
                try:
                    self.env_file.touch()
                    return True, None
                except Exception as e:
                    return False, f"Cannot create .env file: {e}"
            
            # Check read permissions
            if not os.access(self.env_file_path, os.R_OK):
                return False, "No read permission for .env file"
            
            # Check write permissions
            if not os.access(self.env_file_path, os.W_OK):
                return False, "No write permission for .env file"
            
            # Test actual write by appending and removing a comment
            try:
                with open(self.env_file_path, 'a') as f:
                    f.write("\n# Test write - will be removed\n")
                
                # Remove the test line
                with open(self.env_file_path, 'r') as f:
                    lines = f.readlines()
                
                with open(self.env_file_path, 'w') as f:
                    for line in lines:
                        if not line.strip().startswith("# Test write"):
                            f.write(line)
                
                return True, None
                
            except Exception as e:
                return False, f"Cannot write to .env file: {e}"
                
        except Exception as e:
            return False, f"Error validating file permissions: {e}"
    
    def get_current_values(self) -> Dict[str, Any]:
        """
        Get current values of configurable environment variables
        
        Returns:
            Dictionary of current values
        """
        current_values = {}
        
        for var_name, var_config in self.configurable_vars.items():
            current_value = os.getenv(var_name, var_config["default"])
            
            # Convert to appropriate type
            if var_config["type"] == "int":
                try:
                    current_values[var_name] = int(current_value)
                except ValueError:
                    current_values[var_name] = int(var_config["default"])
            else:
                current_values[var_name] = current_value
        
        return current_values
    
    def validate_value(self, var_name: str, value: Any) -> Tuple[bool, Optional[str]]:
        """
        Validate a configuration value
        
        Args:
            var_name: Environment variable name
            value: Value to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if var_name not in self.configurable_vars:
            return False, f"Unknown configuration variable: {var_name}"
        
        var_config = self.configurable_vars[var_name]
        
        # Type validation
        if var_config["type"] == "int":
            try:
                int_value = int(value)
                if int_value <= 0:
                    return False, f"{var_name} must be a positive integer"
            except ValueError:
                return False, f"{var_name} must be a valid integer"
        
        elif var_config["type"] == "url":
            if not value or not value.startswith(('http://', 'https://')):
                return False, f"{var_name} must be a valid URL starting with http:// or https://"
        
        elif var_config["type"] == "path":
            # Validate path format (basic check)
            if not value or len(value.strip()) == 0:
                return False, f"{var_name} cannot be empty"
        
        return True, None
    
    def update_env_var(self, var_name: str, value: str) -> Tuple[bool, Optional[str]]:
        """
        Update an environment variable in the .env file
        
        Args:
            var_name: Variable name
            value: New value
            
        Returns:
            Tuple of (success, error_message)
        """
        # Validate permissions first
        can_write, error = self.validate_file_permissions()
        if not can_write:
            return False, error
        
        # Validate the value
        is_valid, validation_error = self.validate_value(var_name, value)
        if not is_valid:
            return False, validation_error
        
        try:
            # Update the .env file
            set_key(self.env_file_path, var_name, str(value))
            
            # Hot-reload the environment variable
            os.environ[var_name] = str(value)
            
            return True, None
            
        except Exception as e:
            return False, f"Error updating {var_name}: {e}"
    
    def reload_env(self):
        """Hot-reload environment variables from .env file"""
        try:
            load_dotenv(self.env_file_path, override=True)
        except Exception as e:
            st.error(f"Error reloading environment: {e}")
    
    def get_env_status(self) -> Dict[str, Any]:
        """
        Get comprehensive environment status for admin dashboard
        
        Returns:
            Dictionary with environment status information
        """
        status = {
            "file_exists": self.env_file.exists(),
            "file_path": str(self.env_file.absolute()),
            "can_write": False,
            "file_size": 0,
            "last_modified": None,
            "configurable_vars": {},
            "hidden_vars_set": {},
            "error": None
        }
        
        # Check file permissions
        can_write, error = self.validate_file_permissions()
        status["can_write"] = can_write
        status["error"] = error
        
        if self.env_file.exists():
            try:
                file_stat = self.env_file.stat()
                status["file_size"] = file_stat.st_size
                status["last_modified"] = file_stat.st_mtime
            except Exception as e:
                status["error"] = f"Error reading file stats: {e}"
        
        # Get configurable variables
        current_values = self.get_current_values()
        for var_name, var_config in self.configurable_vars.items():
            status["configurable_vars"][var_name] = {
                "value": current_values.get(var_name),
                "description": var_config["description"],
                "type": var_config["type"],
                "default": var_config["default"]
            }
        
        # Check if hidden variables are set (without showing values)
        for var_name in self.hidden_vars:
            status["hidden_vars_set"][var_name] = bool(os.getenv(var_name))
        
        return status
    
    def reset_to_defaults(self) -> Tuple[bool, Optional[str]]:
        """
        Reset all configurable variables to their default values
        
        Returns:
            Tuple of (success, error_message)
        """
        can_write, error = self.validate_file_permissions()
        if not can_write:
            return False, error
        
        try:
            for var_name, var_config in self.configurable_vars.items():
                success, error = self.update_env_var(var_name, var_config["default"])
                if not success:
                    return False, f"Error resetting {var_name}: {error}"
            
            return True, None
            
        except Exception as e:
            return False, f"Error resetting to defaults: {e}" 