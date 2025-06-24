# CV Converter Web Application - Requirements Specification

1. Project Overview
Objective: Scale the existing Python-based "CV Converter" CLI tool to a web-based application that automates transformation of CVs into standardized corporate resume format (.docx) for organization-wide use.
Current State: Local CLI tool for ad-hoc PDF-to-DOCX transformations
Target State: Web application with user management, integrated file storage, and streamlined workflow

1. Technical Architecture

2.1 Technology Stack
Frontend: Streamlit web application with multi-step wizard interface
Backend: Python-based processing engine (existing CV conversion logic)
Authentication: JWT-based authentication system
Deployment: Docker container-based deployment
Database: SQLite for user role management
File Integration: Redmine for persistent file storage

2.2 System Components
cv-converter-web/
├── app/
│   ├── auth/          # JWT authentication logic
│   ├── pages/         # Streamlit pages (wizard steps)
│   ├── core/          # Existing CV processing logic
│   ├── models/        # User/role data models
│   └── utils/         # Helpers, validators
├── data/              # SQLite database, temp files
├── docker/            # Dockerfile, docker-compose
└── requirements.txt

3. Functional Requirements
3.1 User Interface

* Multi-step wizard workflow:
  * Step 1 (File Upload):
    * Redmine ticket selection (select ticket from the list with context search by subject or number) or creation (checkbox)
    * File upload and validation 
      * convertion pdf/word to text
  * Step 2 (Context Review):
    * Preview CV in text and confirmation. Ability to edit the context.
    * Processing and progress tracking
  * Step 3 (Download Results)
    * Download results
* Session state management for wizard navigation
* Progress indicators and status feedback
* File upload validation for supported formats (pdf, word, txt)

3.2 Authentication & Authorization
* JWT-based authentication with Redmine user verification
  * Separate login page with username/password fields
  * Direct Redmine API call to /users/current.json for validation
  * No credential storage - validate on each login attempt
  * JWT creation after successful Redmine authentication
  * 12-hour JWT expiration with automatic refresh
  * Client-side JWT storage in Streamlit session state
* Role-based access control:
  * User Role: Can convert CVs, access own conversion history, view own tickets from Redmine
  * Admin Role: All user capabilities + user management + system statistics
* First user becomes admin automatically (empty table + successful auth)
* Session management with token refresh
  * Session persistence across browser sessions
  * Toast/notification style error messages for Redmine connection issues
  * Automatic token refresh in background

3.3 User Management
* User identification via Redmine authentication
* Role storage in local SQLite database
  * SQLite schema should include:
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    redmine_user_id INTEGER UNIQUE,
    username TEXT,
    custom_fields TEXT, -- JSON string of Redmine custom fields
    role TEXT CHECK(role IN ('admin', 'user')),
    last_login TIMESTAMP,
    conversion_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
* Admin capabilities:
  * View/manage only users who have logged into the app
  * Promote/demote user roles
  * View user directory
  * Access conversion statistics

3.4 File Processing Workflow
* Upload: Validate and temporarily store CV files
* Configure: User selects processing options
* Redmine Integration:
  * Select existing ticket OR create new ticket in default project
  * Search/filter existing tickets
* Process: Convert CV using existing logic
* Store: Upload original and converted files to selected Redmine ticket
* Cleanup: Remove temporary files after processing

3.5 Redmine Integration
* Ticket Management: Create new tickets or update existing ones
* File Attachment: Attach both original and converted files
* Project Configuration: Default project ID in environment configuration (in SQLite database on the later stage)
* View User's tickets: View user Tickets from Default project ID for selected period (this week (default) | last week | last 2 weeks | this month | last month | any) 
* User Access Validation: Verify user permissions for selected tickets

1. Technical Requirements
4.1 Environment Configuration
```env
REDMINE_URL=
REDMINE_API_KEY=
DEFAULT_PROJECT_ID=
JWT_SECRET_KEY=
SQLITE_DB_PATH=
TEMP_FILES_PATH=
MAX_FILE_SIZE_MB=
```

4.2 Data Storage
* SQLite Database: User roles and conversion audit trail
* Temporary Storage: Local file system for pre-processing
* Persistent Storage: Redmine ticket attachments

4.3 Security Requirements
* API Credential Security: Environment variables for sensitive data
* File Validation: Type checking and sanitization
* Size Limits: Maximum file size enforcement
* Cleanup Strategy: Automated temporary file deletion

4.4 Docker Deployment
* Volume Persistence: SQLite database and temporary files
* Health Checks: Container monitoring endpoints
* Logging Configuration: Structured logging for troubleshooting

5. Non-Functional Requirements
5.1 Performance
* Expected Volume: Low to moderate (not high-volume processing)
* Processing Time: Reasonable response times for CV conversion
* Resource Management: Efficient temporary file cleanup

5.2 Reliability
* Error Handling: Graceful failure management with user feedback
* Retry Mechanisms: Option to retry failed conversions
* Audit Trail: Complete logging of conversion activities

5.3 Usability
* Intuitive Interface: Simple wizard-based workflow
* Clear Feedback: Progress indicators and error messages
* Search Functionality: Easy ticket selection in Redmine integration

6. Future Considerations
* Email Integration: Planned for later phases
* Google Drive Integration: Planned for later phases
* API Endpoints: Architecture ready for REST API exposure
* HR System Integration: When HR system becomes available

7. Outstanding Items to Define
7.1 Operational Requirements
 Monitoring Strategy: Application health and performance monitoring
 Backup Strategy: Database and configuration backup procedures
 Maintenance Windows: Update and maintenance scheduling
 Support Process: User support and troubleshooting procedures

7.2 Security & Compliance
 Data Retention Policy: How long to keep conversion logs and temporary files
 Access Audit Requirements: User access logging and review processes
 SSL/TLS Configuration: HTTPS requirements for deployment
 Compliance Requirements: Any regulatory or company policy compliance needs

7.3 Integration Details
 Redmine API Limitations: Rate limits, authentication methods, API version
 Network Requirements: Firewall rules, internal network access
 Single Sign-On: Future integration with company authentication systems
 File Format Support: Complete list of input/output formats to support

7.4 Deployment & Operations
 Hosting Environment: Internal servers vs. cloud deployment specifics
 Scalability Planning: Resource allocation and scaling triggers
 Disaster Recovery: Backup and recovery procedures
 Update Strategy: Application update and rollback procedures

7.5 User Training & Documentation
 User Documentation: End-user guides and tutorials
 Admin Documentation: System administration and troubleshooting guides
 Training Requirements: User onboarding and training materials
 Change Management: Rollout strategy and user communication plan
RetryClaude does not have the ability to run the code it generates yet.Claude can make mistakes. Please double-check responses.