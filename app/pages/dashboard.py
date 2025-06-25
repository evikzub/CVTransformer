"""
Main dashboard page for CV Converter Web Application
Shows different content based on user role (admin/user)
"""

import streamlit as st
from ..auth.auth_service import AuthService
from ..utils.helpers import (
    show_success_message, show_error_message, format_datetime,
    init_session_state_defaults
)

def show_dashboard():
    """Display the main dashboard with role-based content"""
    # Initialize auth service and require authentication
    auth_service = AuthService()
    auth_service.require_authentication()
    
    # Get current user
    current_user = auth_service.get_current_user()
    
    # Initialize session state
    init_session_state_defaults()
    
    # Page header
    st.title("📊 CV Converter Dashboard")
    
    # Welcome message
    role_icon = "👑" if current_user.role == "admin" else "👤"
    st.markdown(f"Welcome back, **{current_user.username}** {role_icon}")
    
    # User info sidebar
    with st.sidebar:
        st.markdown("### 👤 User Information")
        st.write(f"**Username:** {current_user.username}")
        st.write(f"**Role:** {current_user.role.title()}")
        st.write(f"**Conversions:** {current_user.conversion_count}")
        st.write(f"**Last Login:** {format_datetime(current_user.last_login)}")
        st.write(f"**Member Since:** {format_datetime(current_user.created_at)}")
        
        st.markdown("---")
        
        # Navigation
        st.markdown("### 🧭 Navigation")
        
        if st.button("🎫 Tickets", use_container_width=True):
            st.query_params.page = "tickets"
            st.rerun()
        
        if st.button("🔄 CV Converter", use_container_width=True):
            st.query_params.page = "converter"
            st.rerun()
        
        if current_user.role == "admin":
            if st.button("👥 User Management", use_container_width=True):
                st.query_params.page = "admin_users"
                st.rerun()
                
            if st.button("⚙️ Settings", use_container_width=True):
                st.query_params.page = "admin_settings"
                st.rerun()
        
        st.markdown("---")
        
        # Logout button
        if st.button("🔓 Logout", use_container_width=True):
            auth_service.logout()
            st.rerun()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 🚀 Quick Actions")
        
        # Primary action cards
        with st.container():
            action_col1, action_col2 = st.columns(2)
            
            with action_col1:
                with st.container():
                    st.markdown("""
                    <div style="padding: 1rem; border: 2px solid #4CAF50; border-radius: 10px; text-align: center; margin-bottom: 1rem;">
                        <h4>📄 Convert CV</h4>
                        <p>Upload and convert your CV to corporate format</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("Start Conversion", key="start_conversion", type="primary", use_container_width=True):
                        st.query_params.page = "converter"
                        st.rerun()
            
            with action_col2:
                with st.container():
                    st.markdown("""
                    <div style="padding: 1rem; border: 2px solid #2196F3; border-radius: 10px; text-align: center; margin-bottom: 1rem;">
                        <h4>📋 View History</h4>
                        <p>See your previous conversions and downloads</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("View History", key="view_history", use_container_width=True):
                        st.info("📝 Conversion history feature coming soon!")
        
        # Admin-only actions
        if current_user.role == "admin":
            st.markdown("### 👑 Admin Actions")
            
            admin_col1, admin_col2 = st.columns(2)
            
            with admin_col1:
                with st.container():
                    st.markdown("""
                    <div style="padding: 1rem; border: 2px solid #FF9800; border-radius: 10px; text-align: center; margin-bottom: 1rem;">
                        <h4>👥 Manage Users</h4>
                        <p>View and manage user accounts and roles</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("Manage Users", key="manage_users", use_container_width=True):
                        st.query_params.page = "admin_users"
                        st.rerun()
            
            with admin_col2:
                with st.container():
                    st.markdown("""
                    <div style="padding: 1rem; border: 2px solid #9C27B0; border-radius: 10px; text-align: center; margin-bottom: 1rem;">
                        <h4>⚙️ System Settings</h4>
                        <p>Configure application settings and integrations</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("System Settings", key="system_settings", use_container_width=True):
                        st.info("⚙️ System settings feature coming soon!")
    
    with col2:
        st.markdown("### 📈 Statistics")
        
        # User statistics
        with st.container():
            st.metric("Your Conversions", current_user.conversion_count)
            
            # Show admin statistics if admin
            if current_user.role == "admin":
                try:
                    all_users = auth_service.user_manager.get_all_users()
                    total_users = len(all_users)
                    total_conversions = sum(user.conversion_count for user in all_users)
                    
                    st.metric("Total Users", total_users)
                    st.metric("Total Conversions", total_conversions)
                    
                except Exception as e:
                    st.error(f"Error loading statistics: {e}")
        
        # Recent activity placeholder
        st.markdown("### 📋 Recent Activity")
        st.info("📝 Recent activity tracking coming soon!")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "CV Converter Web Application | Powered by Streamlit"
        "</div>", 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    show_dashboard() 