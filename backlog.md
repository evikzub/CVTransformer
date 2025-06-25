# CV Converter Web Application - Product Backlog

## Epic 1: Authentication & User Management
Description: Implement secure user authentication and role-based access control
Priority: High
Features:

### F1.1: JWT Authentication System [x]
[x] Redmine user verification integration
    * Direct Redmine API call to /users/current.json for validation
[x] JWT token generation and validation
    * JWT creation after successful Redmine authentication
    * 12-hour JWT expiration with automatic refresh
    * Client-side JWT storage in Streamlit session state
    * Automatic token refresh (when < 1 hour remaining)
[x] Session management and token refresh
    * Session persistence across browser sessions
    * Automatic token refresh in background
[x] Login/logout functionality
    * Separate login page with username/password fields
    * No credential storage - validate on each login attempt
    * Toast/notification style error messages for Redmine connection issues

### F1.2: Role-Based Access Control [x]
[x] SQLite database setup for user roles
[x] Admin/User role definitions and permissions
[x] First-user-becomes-admin logic (empty table + successful auth)
[x] Role-based UI component visibility

### F1.3: User Management Interface [x]
[x] Admin dashboard for user management
[x] User role assignment
[x] User profile management
    * View/manage only users who have logged into the app
    * Info: Username, custom_fields values, last login, conversion count
User role promotion/demotion functionality

```
CVTransformer/
├── streamlit_app.py          # Main application entry point
├── .env.example              # Environment configuration template
├── requirements.txt          # Updated dependencies
└── app/
    ├── __init__.py
    ├── auth/                 # Authentication module
    │   ├── __init__.py
    │   ├── auth_service.py   # Main auth service (coordination)
    │   ├── jwt_manager.py    # JWT token management
    │   └── redmine_client.py # Redmine API integration
    ├── models/               # Data models
    │   ├── __init__.py
    │   └── user.py          # User model & database operations
    ├── pages/                # Streamlit pages
    │   ├── __init__.py
    │   ├── login.py         # Login page
    │   ├── dashboard.py     # Main dashboard
    │   └── admin_users.py   # Admin user management
    └── utils/                # Utilities
        ├── __init__.py
        └── helpers.py       # Helper functions
```


## Epic 2: Redmine Integration
Description: Connect the application with Redmine for ticket and file management
Features:

### F2.1: Redmine API Integration
Redmine authentication and API connection
Redmine Projects retrieval
```python
# API Endpoints
# projects
GET /projects.json → {projects: [{id, name, status}]}
# issues
GET /projects/{id}/issues.json?assigned_to_id=me&status_id=open&f[]=created_on&op[created_on]=><&v[created_on][]=start&v[created_on][]=end
POST /issues.json → Create new issue
```
System settings interface (Admin)
* Default project configuration
* File size and type restrictions
* Environment variable management based on the file ".env.example"
  * Read/write .env file programmatically
    * the admin interface should validate write permissions to the .env file before attempting changes
  * Hot-reload using python-dotenv with override
  * Admin interface for: DEFAULT_PROJECT_ID, MAX_FILE_SIZE_MB, TICKETS_PER_PAGE
  * TEMP_FILES_PATH and security keys not user-configurable (hide JWT_SECRET_KEY and REDMINE_API_KEY from the admin interface)

### F2.2: Redmine Tickets Integration
Redmine Ticket retrieval for default project
Tickets Interface (User)
* List and search tickets from the selected Default project 
  * Default filter: "this week" + assigned to current user + open status
    * Date Range: For "this week" filter, should be Monday-Sunday
  * 15 tickets per page with pagination
  * Real-time search across: id, subject, description
  * Lazy loading with loading spinners
  * Display fields: id, subject, status, author, assigned_to, created_on
* New ticket creation functionality
  * Required fields: subject, description
  * Defaults: tracker=0, status=1, priority=2 (Normal), assigned_to=current_user
  * Naming convention: {Candidate Name} ({Stack})
  * Auto-populate description with conversion metadata (name, contacts)
Error handling for API failures:
* Block workflow on API failures
* Toast notifications for connection errors
* Retry mechanisms with exponential backoff
* Clear error messages with suggested actions

## Epic 3: Core Application Foundation
Description: Establish the basic web application infrastructure and core functionality
Features:

### F3.1: Streamlit Application Setup
Basic Streamlit app structure and routing
Step-by-step navigation component
* Existing ticket search and selection
* Upload original document
* Download original document (no convertion yet)
Session state management
Progress indicators

### F3.2: Core Processing Integration
File upload and validation components
Temporary file management system
Basic error handling and logging
File preview functionality

### F3.3: File Storage Workflow
File attachment capabilities
Original file upload to Redmine tickets
File organization and naming conventions
Cleanup of temporary files

##
Docker containerization with proper volume mounting
Health check endpoints


## Epic 4: Processing & Workflow Management
Description: Implement the complete CV conversion workflow with monitoring
Features:

### F4.1: Conversion Pipeline
Integrate existing CLI CV conversion logic
End-to-end conversion workflow
Converted file attachment
Processing status tracking and updates
Conversion result validation
Retry mechanisms for failed conversions

### F4.2: Audit Trail & Logging
Error reporting and notifications
Conversion history tracking
User activity logging
System event logging
Audit trail database schema

## Epic 5: Administration & Monitoring
Description: Provide administrative tools and system monitoring capabilities
Priority: Medium
Features:

### F5.1: Admin Dashboard
Conversion statistics and analytics
System health monitoring
User activity overview (weekly, monthly)
Performance metrics display

### F5.3: Maintenance Tools
Database cleanup utilities
Temporary file cleanup automation
Log rotation and management
System backup triggers

## Epic 6: Security & Compliance
Description: Implement security measures and compliance features
Priority: Medium
Features:

### F6.1: Security Hardening
Input validation and sanitization
File type restrictions and scanning
Rate limiting implementation
--SSL/TLS configuration support

### F6.2: Data Protection
Temporary file encryption
Secure credential storage
Data retention policy enforcement
Access logging and monitoring

### F6.3: Compliance Features
Audit trail export functionality
Data retention reporting
User access reports
Compliance dashboard

## Epic 7: User Experience & Documentation
Description: Enhance user experience and provide comprehensive documentation
Priority: Low-Medium
Features:

### F7.1: User Experience Enhancements
??Improved error messages and help text
??Tooltips and inline guidance
??Keyboard shortcuts and accessibility
??Mobile-responsive design


## Epic 8: Future Integrations (Backlog)
Description: Planned future enhancements and integrations
Priority: Low
Features:

### F8.1: Email Integration
Email-based CV submission
Email notifications for completion
Email-based user management
SMTP configuration

### F8.2: Google Drive Integration
Google Drive file upload/download
Shared folder management
Google authentication integration
Automatic file organization

### F8.3: API Development
RESTful API endpoints
API authentication and authorization
API documentation and testing
Third-party integration support


