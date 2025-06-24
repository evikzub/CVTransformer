"""
Login page for CV Converter Web Application
Handles user authentication through Redmine integration
"""

import streamlit as st
from ..auth.auth_service import AuthService
from ..utils.helpers import show_error_message, show_success_message, show_info_message

def show_login_page():
    """Display the login page with authentication form"""
    # Initialize auth service
    auth_service = AuthService()
    
    # Page header
    st.title("🔐 CV Converter - Login")
    st.markdown("---")
    
    # Check if already authenticated
    if auth_service.is_authenticated():
        current_user = auth_service.get_current_user()
        st.success(f"✅ Already logged in as **{current_user.username}** ({current_user.role})")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("🏠 Go to Dashboard", type="primary"):
                st.query_params.page = "dashboard"
                st.rerun()
        with col2:
            if st.button("🔓 Logout"):
                auth_service.logout()
                st.rerun()
        return
    
    # Test Redmine connection
    st.info("🔗 Testing Redmine connection...")
    if not auth_service.test_redmine_connection():
        show_error_message("Unable to connect to Redmine. Please check your configuration.")
        st.stop()
    
    show_info_message("Redmine connection successful")
    
    # Login form
    st.markdown("### Enter your Redmine credentials")
    
    with st.form("login_form", clear_on_submit=False):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            username = st.text_input(
                "👤 Username",
                placeholder="Enter your Redmine username",
                help="Use your Redmine login username"
            )
            
            password = st.text_input(
                "🔑 Password",
                type="password",
                placeholder="Enter your Redmine password",
                help="Use your Redmine login password"
            )
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing
            login_button = st.form_submit_button(
                "🔐 Login",
                type="primary",
                use_container_width=True
            )
    
    # Handle login submission
    if login_button:
        if not username or not password:
            show_error_message("Please enter both username and password")
            return
        
        # Show loading spinner during authentication
        with st.spinner("🔍 Authenticating with Redmine..."):
            success, error_message = auth_service.login(username, password)
        
        if success:
            show_success_message("Login successful! Redirecting...")
            # Add a small delay to show success message
            st.balloons()
            st.rerun()
        else:
            show_error_message(f"Login failed: {error_message}")
    
    # Additional information
    st.markdown("---")
    
    with st.expander("ℹ️ Login Information"):
        st.markdown("""
        **Login Requirements:**
        - Use your existing Redmine credentials
        - Your account must be active in Redmine
        - No additional registration required
        
        **First Time Users:**
        - The first user to login becomes an admin automatically
        - Subsequent users will have regular user access
        - Admins can promote other users later
        
        **Security:**
        - Passwords are never stored locally
        - Authentication is verified directly with Redmine
        - Sessions use secure JWT tokens
        """)
    
    # Environment status for debugging (only in debug mode)
    import os
    if os.getenv("DEBUG", "False").lower() == "true":
        st.markdown("---")
        with st.expander("🔧 Debug Information"):
            from ..utils.helpers import get_environment_status
            env_status = get_environment_status()
            
            st.markdown("**Environment Variables:**")
            for var, info in env_status["required"].items():
                status_icon = "✅" if info["set"] else "❌"
                st.write(f"{status_icon} {var}: {'Set' if info['set'] else 'Not Set'}")

if __name__ == "__main__":
    show_login_page() 