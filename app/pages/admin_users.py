"""
Admin user management page for CV Converter Web Application
Allows admin users to view and manage user accounts and roles
"""

import streamlit as st
from ..auth.auth_service import AuthService
from ..utils.helpers import (
    show_success_message, show_error_message, display_user_card, format_datetime
)

def show_admin_users():
    """Display the admin user management page"""
    # Initialize auth service and require admin access
    auth_service = AuthService()
    auth_service.require_admin()
    
    # Get current user
    current_user = auth_service.get_current_user()
    
    # Page header
    st.title("👥 User Management")
    st.markdown(f"Managing users | Logged in as **{current_user.username}** (Admin)")
    st.markdown("---")
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("### 🧭 Navigation")
        
        if st.button("🏠 Dashboard", use_container_width=True):
            st.query_params.page = "dashboard"
            st.rerun()
        
        if st.button("🔄 CV Converter", use_container_width=True):
            st.query_params.page = "converter"
            st.rerun()
        
        st.markdown("---")
        
        # Logout button
        if st.button("🔓 Logout", use_container_width=True):
            auth_service.logout()
            st.rerun()
    
    # Load all users
    try:
        all_users = auth_service.user_manager.get_all_users()
    except Exception as e:
        show_error_message(f"Error loading users: {e}")
        return
    
    # Statistics summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Users", len(all_users))
    
    with col2:
        admin_count = len([u for u in all_users if u.role == "admin"])
        st.metric("Admins", admin_count)
    
    with col3:
        regular_count = len([u for u in all_users if u.role == "user"])
        st.metric("Regular Users", regular_count)
    
    with col4:
        total_conversions = sum(user.conversion_count for user in all_users)
        st.metric("Total Conversions", total_conversions)
    
    st.markdown("---")
    
    # User management section
    st.markdown("### 👤 User List")
    
    if not all_users:
        st.info("No users found in the system.")
        return
    
    # Search and filter
    search_col, filter_col = st.columns([2, 1])
    
    with search_col:
        search_term = st.text_input(
            "🔍 Search users",
            placeholder="Search by username...",
            help="Filter users by username"
        )
    
    with filter_col:
        role_filter = st.selectbox(
            "Filter by role",
            options=["All", "Admin", "User"],
            help="Filter users by their role"
        )
    
    # Filter users based on search and role filter
    filtered_users = all_users
    
    if search_term:
        filtered_users = [
            user for user in filtered_users 
            if search_term.lower() in user.username.lower()
        ]
    
    if role_filter != "All":
        filtered_users = [
            user for user in filtered_users 
            if user.role == role_filter.lower()
        ]
    
    # Display filtered users
    if not filtered_users:
        st.info("No users match your search criteria.")
        return
    
    # Handle user actions
    if "user_action" not in st.session_state:
        st.session_state.user_action = None
        st.session_state.user_action_id = None
    
    # Display user cards
    for user in filtered_users:
        with st.container():
            # User information display
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                st.write(f"**{user.username}**")
                if user.custom_fields:
                    for key, value in user.custom_fields.items():
                        if value:  # Only show non-empty fields
                            st.write(f"*{key}*: {value}")
            
            with col2:
                role_color = "🔴" if user.role == "admin" else "🔵"
                st.write(f"Role: {role_color} {user.role.title()}")
                st.write(f"ID: {user.redmine_user_id}")
            
            with col3:
                st.write(f"Conversions: {user.conversion_count}")
                st.write(f"Last Login: {format_datetime(user.last_login)}")
            
            with col4:
                # Action buttons (don't show for current user)
                if user.id != current_user.id:
                    # Role change button
                    if user.role == "user":
                        if st.button(f"🔼 Make Admin", key=f"promote_{user.id}"):
                            if auth_service.user_manager.update_user_role(user.id, "admin"):
                                show_success_message(f"Promoted {user.username} to admin")
                                st.rerun()
                            else:
                                show_error_message("Failed to update user role")
                    
                    elif user.role == "admin":
                        if st.button(f"🔽 Remove Admin", key=f"demote_{user.id}"):
                            if auth_service.user_manager.update_user_role(user.id, "user"):
                                show_success_message(f"Removed admin privileges from {user.username}")
                                st.rerun()
                            else:
                                show_error_message("Failed to update user role")
                    
                    # Delete user button with confirmation
                    if st.button(f"🗑️ Delete", key=f"delete_{user.id}"):
                        st.session_state.user_action = "delete"
                        st.session_state.user_action_id = user.id
                        st.session_state.user_to_delete = user.username
                        st.rerun()
                else:
                    st.write("*(Current User)*")
        
        st.divider()
    
    # Confirmation dialog for user deletion
    if st.session_state.user_action == "delete":
        st.markdown("---")
        st.error(f"⚠️ **Confirm User Deletion**")
        st.write(f"Are you sure you want to delete user **{st.session_state.user_to_delete}**?")
        st.write("This action cannot be undone.")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("✅ Yes, Delete", type="primary"):
                if auth_service.user_manager.delete_user(st.session_state.user_action_id):
                    show_success_message(f"User {st.session_state.user_to_delete} deleted successfully")
                else:
                    show_error_message("Failed to delete user")
                
                # Clear action state
                st.session_state.user_action = None
                st.session_state.user_action_id = None
                st.session_state.user_to_delete = None
                st.rerun()
        
        with col2:
            if st.button("❌ Cancel"):
                # Clear action state
                st.session_state.user_action = None
                st.session_state.user_action_id = None
                st.session_state.user_to_delete = None
                st.rerun()
    
    # Additional admin tools
    st.markdown("---")
    st.markdown("### 🔧 Admin Tools")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Refresh User List", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("📊 Export User Data", use_container_width=True):
            st.info("📋 User data export feature coming soon!")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        f"User Management | {len(all_users)} total users"
        "</div>", 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    show_admin_users() 