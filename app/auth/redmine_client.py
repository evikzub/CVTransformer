"""
Redmine API client for authentication and user data retrieval
"""

import requests
from typing import Optional, Dict, Any, List
import os
from dotenv import load_dotenv

load_dotenv()

class RedmineClient:
    """Handles communication with Redmine API for authentication and data retrieval"""
    
    def __init__(self):
        """Initialize Redmine client with configuration from environment"""
        self.base_url = os.getenv("REDMINE_URL", "").rstrip('/')
        self.api_key = os.getenv("REDMINE_API_KEY", "")
        self.default_project_id = os.getenv("DEFAULT_PROJECT_ID", "1")
        
        if not self.base_url:
            raise ValueError("REDMINE_URL environment variable is required")
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user with Redmine using username/password
        
        Args:
            username: Redmine username
            password: Redmine password
            
        Returns:
            User data dict if authentication successful, None if failed
        """
        try:
            # Use Redmine API endpoint to get current user info
            api_url = f"{self.base_url}/users/current.json"
            
            response = requests.get(
                api_url,
                auth=(username, password),
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Redmine authentication error: {e}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user information by Redmine user ID
        
        Args:
            user_id: Redmine user ID
            
        Returns:
            User data dict if found, None if not found or error
        """
        try:
            api_url = f"{self.base_url}/users/{user_id}.json"
            
            # Use API key for administrative access
            headers = {"X-Redmine-API-Key": self.api_key}
            
            response = requests.get(api_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Redmine user lookup error: {e}")
            return None
    
    def get_user_projects(self, username: str, password: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get projects accessible to user
        
        Args:
            username: Redmine username
            password: Redmine password
            
        Returns:
            List of project dicts if successful, None if failed
        """
        try:
            api_url = f"{self.base_url}/projects.json"
            
            response = requests.get(
                api_url,
                auth=(username, password),
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("projects", [])
            else:
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Redmine projects error: {e}")
            return None
    
    def get_user_issues(self, username: str, password: str, 
                       project_id: Optional[str] = None,
                       limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """
        Get issues assigned to or created by user
        
        Args:
            username: Redmine username
            password: Redmine password
            project_id: Optional project ID filter
            limit: Maximum number of issues to return
            
        Returns:
            List of issue dicts if successful, None if failed
        """
        try:
            api_url = f"{self.base_url}/issues.json"
            
            params = {
                "assigned_to_id": "me",
                "limit": limit,
                "sort": "updated_on:desc"
            }
            
            if project_id:
                params["project_id"] = project_id
            
            response = requests.get(
                api_url,
                auth=(username, password),
                headers={"Content-Type": "application/json"},
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("issues", [])
            else:
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Redmine issues error: {e}")
            return None
    
    def create_issue(self, username: str, password: str, 
                    subject: str, description: str,
                    project_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Create a new issue in Redmine
        
        Args:
            username: Redmine username
            password: Redmine password
            subject: Issue subject/title
            description: Issue description
            project_id: Project ID (uses default if not provided)
            
        Returns:
            Created issue dict if successful, None if failed
        """
        try:
            api_url = f"{self.base_url}/issues.json"
            
            issue_data = {
                "issue": {
                    "project_id": project_id or self.default_project_id,
                    "subject": subject,
                    "description": description
                }
            }
            
            response = requests.post(
                api_url,
                auth=(username, password),
                headers={"Content-Type": "application/json"},
                json=issue_data,
                timeout=10
            )
            
            if response.status_code == 201:
                return response.json()
            else:
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Redmine issue creation error: {e}")
            return None
    
    def upload_file_to_issue(self, username: str, password: str,
                           issue_id: int, file_path: str, 
                           filename: str) -> bool:
        """
        Upload file attachment to Redmine issue
        
        Args:
            username: Redmine username
            password: Redmine password
            issue_id: Redmine issue ID
            file_path: Local file path
            filename: Display filename
            
        Returns:
            True if upload successful, False if failed
        """
        try:
            # First upload the file
            upload_url = f"{self.base_url}/uploads.json"
            
            with open(file_path, 'rb') as f:
                response = requests.post(
                    upload_url,
                    auth=(username, password),
                    headers={"Content-Type": "application/octet-stream"},
                    data=f,
                    timeout=30
                )
            
            if response.status_code != 201:
                return False
                
            upload_data = response.json()
            token = upload_data.get("upload", {}).get("token")
            
            if not token:
                return False
            
            # Then attach the uploaded file to the issue
            issue_url = f"{self.base_url}/issues/{issue_id}.json"
            
            update_data = {
                "issue": {
                    "uploads": [{
                        "token": token,
                        "filename": filename
                    }]
                }
            }
            
            response = requests.put(
                issue_url,
                auth=(username, password),
                headers={"Content-Type": "application/json"},
                json=update_data,
                timeout=10
            )
            
            return response.status_code == 204
            
        except (requests.exceptions.RequestException, FileNotFoundError, IOError) as e:
            print(f"Redmine file upload error: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test connection to Redmine API
        
        Returns:
            True if connection successful, False if failed
        """
        try:
            api_url = f"{self.base_url}/projects.json"
            headers = {"X-Redmine-API-Key": self.api_key} if self.api_key else {}
            
            response = requests.get(api_url, headers=headers, timeout=5)
            return response.status_code == 200
            
        except requests.exceptions.RequestException:
            return False 