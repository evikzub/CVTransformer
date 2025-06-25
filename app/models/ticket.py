"""
Ticket model and Redmine API integration for CV Converter Web Application
"""

import requests
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import os
from dotenv import load_dotenv
from ..auth.redmine_client import RedmineClient

load_dotenv()

@dataclass
class Ticket:
    """Ticket data model representing a Redmine issue"""
    id: int
    subject: str
    description: str = ""
    status_id: int = 1
    status_name: str = ""
    priority_id: int = 2
    priority_name: str = ""
    tracker_id: int = 0
    tracker_name: str = ""
    author_id: int = 0
    author_name: str = ""
    assigned_to_id: Optional[int] = None
    assigned_to_name: str = ""
    project_id: int = 1
    project_name: str = ""
    created_on: Optional[datetime] = None
    updated_on: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert ticket object to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'subject': self.subject,
            'description': self.description,
            'status_id': self.status_id,
            'status_name': self.status_name,
            'priority_id': self.priority_id,
            'priority_name': self.priority_name,
            'tracker_id': self.tracker_id,
            'tracker_name': self.tracker_name,
            'author_id': self.author_id,
            'author_name': self.author_name,
            'assigned_to_id': self.assigned_to_id,
            'assigned_to_name': self.assigned_to_name,
            'project_id': self.project_id,
            'project_name': self.project_name,
            'created_on': self.created_on.isoformat() if self.created_on else None,
            'updated_on': self.updated_on.isoformat() if self.updated_on else None
        }

class TicketManager:
    """Manages ticket operations with Redmine API integration"""
    
    def __init__(self):
        """Initialize ticket manager"""
        self.redmine_client = RedmineClient()
        self.default_project_id = os.getenv("DEFAULT_PROJECT_ID", "1")
        self.tickets_per_page = int(os.getenv("TICKETS_PER_PAGE", "15"))
    
    def get_this_week_date_range(self) -> Tuple[str, str]:
        """
        Get Monday-Sunday date range for current week
        
        Returns:
            Tuple of (start_date, end_date) in YYYY-MM-DD format
        """
        today = datetime.now().date()
        days_since_monday = today.weekday()  # Monday is 0
        
        start_of_week = today - timedelta(days=days_since_monday)
        end_of_week = start_of_week + timedelta(days=6)
        
        return start_of_week.strftime("%Y-%m-%d"), end_of_week.strftime("%Y-%m-%d")
    
    def parse_redmine_issue(self, issue_data: Dict[str, Any]) -> Ticket:
        """
        Parse Redmine issue data into Ticket object
        
        Args:
            issue_data: Raw issue data from Redmine API
            
        Returns:
            Ticket object
        """
        # Parse dates
        created_on = None
        updated_on = None
        
        if issue_data.get("created_on"):
            try:
                created_on = datetime.fromisoformat(issue_data["created_on"].replace('Z', '+00:00'))
            except ValueError:
                pass
        
        if issue_data.get("updated_on"):
            try:
                updated_on = datetime.fromisoformat(issue_data["updated_on"].replace('Z', '+00:00'))
            except ValueError:
                pass
        
        return Ticket(
            id=issue_data.get("id", 0),
            subject=issue_data.get("subject", ""),
            description=issue_data.get("description", ""),
            status_id=issue_data.get("status", {}).get("id", 1),
            status_name=issue_data.get("status", {}).get("name", ""),
            priority_id=issue_data.get("priority", {}).get("id", 2),
            priority_name=issue_data.get("priority", {}).get("name", ""),
            tracker_id=issue_data.get("tracker", {}).get("id", 0),
            tracker_name=issue_data.get("tracker", {}).get("name", ""),
            author_id=issue_data.get("author", {}).get("id", 0),
            author_name=issue_data.get("author", {}).get("name", ""),
            assigned_to_id=issue_data.get("assigned_to", {}).get("id") if issue_data.get("assigned_to") else None,
            assigned_to_name=issue_data.get("assigned_to", {}).get("name", "") if issue_data.get("assigned_to") else "",
            project_id=issue_data.get("project", {}).get("id", 1),
            project_name=issue_data.get("project", {}).get("name", ""),
            created_on=created_on,
            updated_on=updated_on
        )
    
    def set_params(self, param_name: str, param_value: str | list[str], operator: str = "=") -> list[tuple[str, str]]:
        """
        Set parameters for Redmine API request
        """
        params: list[tuple[str, str]] = []
        params.append(("f[]", param_name))
        params.append((f"op[{param_name}]", operator))
        if isinstance(param_value, list):
            for value in param_value:
                params.append((f"v[{param_name}][]", value))
        else:
            params.append((f"v[{param_name}][]", param_value))
        return params
    
    def get_tickets(self, username: str = "", password: str = "", 
                   project_id: Optional[str] = None,
                   assigned_to_me: bool = True,
                   status_filter: str = "open",
                   date_filter: str = "this_week",
                   search_query: str = "",
                   page: int = 1,
                   use_api_key: bool = True) -> Tuple[List[Ticket], int, Optional[str]]:
        """
        Get tickets from Redmine with filtering and pagination
        
        Args:
            username: Redmine username (optional if using API key)
            password: Redmine password (optional if using API key)
            project_id: Project ID filter (uses default if None)
            assigned_to_me: Filter to current user's tickets
            status_filter: Status filter ("open", "closed", "all")
            date_filter: Date filter ("this_week", "last_week", "this_month", "last_month", "all")
            search_query: Search query for id, subject, description
            page: Page number for pagination
            use_api_key: Use API key authentication instead of user credentials
            
        Returns:
            Tuple of (tickets_list, total_count, error_message)
        """
        # Build date filter parameters
        date_filter_params = {}
        if date_filter == "this_week":
            start_date, end_date = self.get_this_week_date_range()
            date_filter_params = {
                "f[]": "created_on",
                "op[created_on]": "><",
                "v[created_on][]": [start_date, end_date]
            }
        elif date_filter == "last_week":
            today = datetime.now().date()
            days_since_monday = today.weekday()
            this_monday = today - timedelta(days=days_since_monday)
            last_monday = this_monday - timedelta(days=7)
            last_sunday = last_monday + timedelta(days=6)
            
            date_filter_params = {
                "f[]": "created_on",
                "op[created_on]": "><",
                "v[created_on][]": [
                    last_monday.strftime("%Y-%m-%d"),
                    last_sunday.strftime("%Y-%m-%d")
                ]
            }
        elif date_filter == "this_month":
            today = datetime.now().date()
            start_of_month = today.replace(day=1)
            date_filter_params = {
                "f[]": "created_on",
                "op[created_on]": ">=",
                "v[created_on][]": start_of_month.strftime("%Y-%m-%d")
            }
        elif date_filter == "last_month":
            today = datetime.now().date()
            start_of_month = today.replace(day=1).replace(month=today.month - 1)
            date_filter_params = {
                "f[]": "created_on",
                "op[created_on]": ">=",
                "v[created_on][]": start_of_month.strftime("%Y-%m-%d")
            }
        
        # Get user ID for assignment filter if using API key
        assigned_to_user_id = None
        if use_api_key and assigned_to_me and username:
            # Get user ID by username
            user_data = self.redmine_client.get_user_by_login(username)
            if user_data:
                assigned_to_user_id = user_data.get("id")
        
        try:
            if use_api_key and self.redmine_client.api_key:
                # Use API key method
                issues = self.redmine_client.get_user_issues_with_api_key(
                    project_id=project_id or self.default_project_id,
                    assigned_to_user_id=assigned_to_user_id if assigned_to_me else None,
                    status_filter=status_filter,
                    limit=self.tickets_per_page,
                    offset=(page - 1) * self.tickets_per_page,
                    search_query=search_query,
                    date_filter_params=date_filter_params
                )
                
                if issues is None:
                    return [], 0, "Failed to fetch tickets using API key"
                
                # For API key, we don't get total count directly, so we estimate
                total_count = len(issues) + ((page - 1) * self.tickets_per_page)
                if len(issues) == self.tickets_per_page:
                    total_count += 1  # Indicate there might be more
                
            else:
                # Use username/password method
                if not username or not password:
                    return [], 0, "Username and password required for authentication"
                
                api_url = f"{self.redmine_client.base_url}/issues.json"
                
                # Build query parameters
                params: list[tuple[str, str]] = [
                    ("limit", self.tickets_per_page),
                    ("offset", (page - 1) * self.tickets_per_page),
                    ("sort", "parent:desc"),
                    ("set_filter", 1)
                ]
                
                # Project filter
                params.append(("project_id", project_id or self.default_project_id))
                
                # Assigned to filter
                if assigned_to_me:
                    # params["assigned_to_id"] = "me"
                    params.extend(self.set_params("author_id", "me"))
                
                # Tracker filter
                # if tracker_filter:
                params.extend(self.set_params("tracker_id", [5, 9]))
                
                # Status filter
                if status_filter == "open":
                    params.append(("status_id", "open"))
                elif status_filter == "closed":
                    params.append(("status_id", "closed"))
                
                # Add date filter params
                if date_filter_params:
                    params.extend(date_filter_params.items())
                
                # Search query
                if search_query:
                    params.append(("search", search_query))
                
                # Make API request
                response = requests.get(
                    api_url,
                    auth=(username, password),
                    headers={"Content-Type": "application/json"},
                    params=params,
                    timeout=15
                )
                
                print(f"Request URL: {response.request.url}")
                if response.status_code != 200:
                    print(f"API request failed: {response.status_code}")
                    print(f"Response: {response.text}")
                    return [], 0, f"API request failed: {response.status_code}"
                
                data = response.json()
                issues = data.get("issues", [])
                total_count = data.get("total_count", 0)
            
            # Parse issues into Ticket objects
            tickets = [self.parse_redmine_issue(issue) for issue in issues]
            
            return tickets, total_count, None
            
        except requests.exceptions.RequestException as e:
            return [], 0, f"Network error: {e}"
        except Exception as e:
            return [], 0, f"Error fetching tickets: {e}"
    
    def create_ticket(self, subject: str, description: str,
                     candidate_name: str = "", stack: str = "",
                     project_id: Optional[str] = None,
                     username: str = "", password: str = "",
                     use_api_key: bool = True,
                     assigned_to_user_id: Optional[int] = None) -> Tuple[Optional[Ticket], Optional[str]]:
        """
        Create a new ticket in Redmine
        
        Args:
            subject: Ticket subject
            description: Ticket description
            candidate_name: Candidate name for naming convention
            stack: Technology stack for naming convention
            project_id: Project ID (uses default if None)
            username: Redmine username (for user auth)
            password: Redmine password (for user auth)
            use_api_key: Use API key authentication instead of user credentials
            assigned_to_user_id: User ID to assign ticket to
            
        Returns:
            Tuple of (created_ticket, error_message)
        """
        # Apply naming convention if candidate info provided
        if candidate_name and stack:
            formatted_subject = f"{candidate_name} ({stack})"
            if subject and subject != formatted_subject:
                formatted_subject = f"{formatted_subject} - {subject}"
        else:
            formatted_subject = subject
        
        try:
            if use_api_key and self.redmine_client.api_key:
                # Use API key method
                created_issue = self.redmine_client.create_issue_with_api_key(
                    subject=formatted_subject,
                    description=description,
                    project_id=project_id or self.default_project_id,
                    assigned_to_user_id=assigned_to_user_id
                )
                
                if created_issue:
                    ticket = self.parse_redmine_issue(created_issue.get("issue", {}))
                    return ticket, None
                else:
                    return None, "Failed to create ticket using API key"
            
            else:
                # Use username/password method
                if not username or not password:
                    return None, "Username and password required for authentication"
                
                api_url = f"{self.redmine_client.base_url}/issues.json"
                
                # Prepare issue data
                issue_data = {
                    "issue": {
                        "project_id": project_id or self.default_project_id,
                        "subject": formatted_subject,
                        "description": description,
                        "tracker_id": 1,  # Default tracker
                        "status_id": 1,   # New
                        "priority_id": 2, # Normal
                    }
                }
                
                # Add assignment
                if assigned_to_user_id:
                    issue_data["issue"]["assigned_to_id"] = assigned_to_user_id
                else:
                    issue_data["issue"]["assigned_to_id"] = "me"  # Assign to current user
                
                response = requests.post(
                    api_url,
                    auth=(username, password),
                    headers={"Content-Type": "application/json"},
                    json=issue_data,
                    timeout=15
                )
                
                if response.status_code == 201:
                    created_issue = response.json()
                    ticket = self.parse_redmine_issue(created_issue.get("issue", {}))
                    return ticket, None
                else:
                    return None, f"Failed to create ticket: {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return None, f"Network error: {e}"
        except Exception as e:
            return None, f"Error creating ticket: {e}"
    
    def get_ticket_by_id(self, username: str, password: str, ticket_id: int) -> Tuple[Optional[Ticket], Optional[str]]:
        """
        Get a specific ticket by ID
        
        Args:
            username: Redmine username
            password: Redmine password
            ticket_id: Ticket ID
            
        Returns:
            Tuple of (ticket, error_message)
        """
        try:
            api_url = f"{self.redmine_client.base_url}/issues/{ticket_id}.json"
            
            response = requests.get(
                api_url,
                auth=(username, password),
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                ticket = self.parse_redmine_issue(data.get("issue", {}))
                return ticket, None
            else:
                return None, f"Ticket not found: {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return None, f"Network error: {e}"
        except Exception as e:
            return None, f"Error fetching ticket: {e}" 