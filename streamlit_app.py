"""
Main Streamlit application entry point for CV Converter Web Application
Handles routing, authentication, and page management
"""

import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Streamlit page
st.set_page_config(
    page_title="CV Converter",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import application modules
from app.auth.auth_service import AuthService
from app.pages.login import show_login_page
from app.pages.dashboard import show_dashboard
from app.pages.admin_users import show_admin_users
from app.pages.admin_settings import show_admin_settings
from app.pages.tickets import show_tickets_page
from app.utils.helpers import init_session_state_defaults

def main():
    """Main application function with routing logic"""
    
    # Initialize session state defaults
    init_session_state_defaults()
    
    # Initialize authentication service
    auth_service = AuthService()
    
    # Check authentication status
    current_user = auth_service.get_current_user()
    is_authenticated = current_user is not None
    
    # Get current page from query params or session state
    page = st.query_params.get("page", "login" if not is_authenticated else "dashboard")
    
    # Store current page in session state
    if "current_page" not in st.session_state:
        st.session_state.current_page = page
    
    # Update page if it changed
    if st.session_state.current_page != page:
        st.session_state.current_page = page
    
    # Hide Streamlit menu and footer for cleaner UI
    hide_streamlit_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
    
    # Custom CSS for better styling
    st.markdown("""
        <style>
        .stApp {
            background-color: #f5f5f5;
        }
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Route to appropriate page based on authentication and page parameter
    try:
        if not is_authenticated:
            # Show login page for unauthenticated users
            show_login_page()
        else:
            # Route authenticated users to appropriate pages
            if page == "dashboard" or page == "login":
                show_dashboard()
            
            elif page == "admin_users":
                # Check admin privileges
                if current_user.role == "admin":
                    show_admin_users()
                else:
                    st.error("🚫 Admin access required")
                    st.info("Redirecting to dashboard...")
                    st.query_params.page = "dashboard"
                    st.rerun()
            
            elif page == "admin_settings":
                # Check admin privileges
                if current_user.role == "admin":
                    show_admin_settings()
                else:
                    st.error("🚫 Admin access required")
                    st.info("Redirecting to dashboard...")
                    st.query_params.page = "dashboard"
                    st.rerun()
            
            elif page == "tickets":
                show_tickets_page()
            
            elif page == "converter":
                st.info("🔄 CV Converter page coming soon!")
                if st.button("← Back to Dashboard"):
                    st.query_params.page = "dashboard"
                    st.rerun()
            
            else:
                # Unknown page, redirect to dashboard
                st.error("🔍 Page not found")
                st.info("Redirecting to dashboard...")
                st.query_params.page = "dashboard"
                st.rerun()
                
    except Exception as e:
        st.error(f"Application error: {e}")
        
        # Show debug information if in debug mode
        if os.getenv("DEBUG", "False").lower() == "true":
            st.exception(e)
        
        # Provide fallback navigation
        st.markdown("---")
        st.markdown("### 🔧 Navigation")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🏠 Go to Dashboard"):
                st.query_params.page = "dashboard"
                st.rerun()
        
        with col2:
            if st.button("🔓 Logout"):
                auth_service.logout()
                st.query_params.page = "login"
                st.rerun()

if __name__ == "__main__":
    main() 