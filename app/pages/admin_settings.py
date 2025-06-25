"""
Admin settings page for CV Converter Web Application
Allows admin users to configure system settings and environment variables
"""

import streamlit as st
from datetime import datetime
from ..auth.auth_service import AuthService
from ..utils.env_manager import EnvManager
from ..utils.helpers import (
    show_success_message, show_error_message, show_warning_message, show_info_message
)

def show_admin_settings():
    """Display the admin settings page"""
    # Initialize auth service and require admin access
    auth_service = AuthService()
    auth_service.require_admin()
    
    # Get current user
    current_user = auth_service.get_current_user()
    
    # Initialize environment manager
    env_manager = EnvManager()
    
    # Page header
    st.title("⚙️ System Settings")
    st.markdown(f"System configuration | Logged in as **{current_user.username}** (Admin)")
    st.markdown("---")
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("### 🧭 Navigation")
        
        if st.button("🏠 Dashboard", use_container_width=True):
            st.query_params.page = "dashboard"
            st.rerun()
        
        if st.button("👥 User Management", use_container_width=True):
            st.query_params.page = "admin_users"
            st.rerun()
        
        if st.button("🔄 CV Converter", use_container_width=True):
            st.query_params.page = "converter"
            st.rerun()
        
        st.markdown("---")
        
        # Logout button
        if st.button("🔓 Logout", use_container_width=True):
            auth_service.logout()
            st.rerun()
    
    # Environment status overview
    st.markdown("### 📊 Environment Status")
    
    env_status = env_manager.get_env_status()
    
    # Status indicators
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        file_status = "✅ Exists" if env_status["file_exists"] else "❌ Missing"
        st.metric("Environment File", file_status)
    
    with col2:
        write_status = "✅ Writable" if env_status["can_write"] else "❌ Read-only"
        st.metric("File Permissions", write_status)
    
    with col3:
        if env_status["file_size"]:
            size_display = f"{env_status['file_size']} bytes"
        else:
            size_display = "N/A"
        st.metric("File Size", size_display)
    
    with col4:
        if env_status["last_modified"]:
            modified_time = datetime.fromtimestamp(env_status["last_modified"])
            modified_display = modified_time.strftime("%H:%M")
        else:
            modified_display = "N/A"
        st.metric("Last Modified", modified_display)
    
    # Show errors if any
    if env_status["error"]:
        show_error_message(f"Environment file error: {env_status['error']}")
        st.stop()
    
    st.markdown("---")
    
    # Configuration settings
    st.markdown("### 🔧 Configuration Settings")
    
    if not env_status["can_write"]:
        show_warning_message("Environment file is read-only. Settings cannot be changed.")
        st.markdown("**Current Settings (Read-only):**")
        
        for var_name, var_info in env_status["configurable_vars"].items():
            st.write(f"**{var_name}**: {var_info['value']} - *{var_info['description']}*")
    
    else:
        # Configuration form
        with st.form("settings_form"):
            st.markdown("**Configurable Settings:**")
            
            updated_values = {}
            
            for var_name, var_info in env_status["configurable_vars"].items():
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.markdown(f"**{var_name}**")
                    st.caption(var_info['description'])
                
                with col2:
                    if var_info['type'] == 'int':
                        updated_values[var_name] = st.number_input(
                            f"Value for {var_name}",
                            value=var_info['value'],
                            min_value=1,
                            step=1,
                            key=f"input_{var_name}",
                            label_visibility="collapsed"
                        )
                    else:
                        updated_values[var_name] = st.text_input(
                            f"Value for {var_name}",
                            value=str(var_info['value']),
                            key=f"input_{var_name}",
                            label_visibility="collapsed"
                        )
            
            # Form buttons
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                save_button = st.form_submit_button("💾 Save Changes", type="primary")
            
            with col2:
                reset_button = st.form_submit_button("🔄 Reset to Defaults")
        
        # Handle form submissions
        if save_button:
            success_count = 0
            error_count = 0
            
            for var_name, new_value in updated_values.items():
                success, error = env_manager.update_env_var(var_name, str(new_value))
                if success:
                    success_count += 1
                else:
                    show_error_message(f"Failed to update {var_name}: {error}")
                    error_count += 1
            
            if success_count > 0:
                show_success_message(f"Successfully updated {success_count} setting(s)")
                # Hot-reload environment
                env_manager.reload_env()
                st.rerun()
            
            if error_count == 0 and success_count == 0:
                show_info_message("No changes were made")
        
        if reset_button:
            success, error = env_manager.reset_to_defaults()
            if success:
                show_success_message("All settings reset to defaults")
                env_manager.reload_env()
                st.rerun()
            else:
                show_error_message(f"Failed to reset settings: {error}")
    
    # Security settings status
    st.markdown("---")
    st.markdown("### 🔒 Security Settings Status")
    
    security_col1, security_col2 = st.columns(2)
    
    with security_col1:
        jwt_status = "✅ Set" if env_status["hidden_vars_set"]["JWT_SECRET_KEY"] else "❌ Not Set"
        st.metric("JWT Secret Key", jwt_status)
    
    with security_col2:
        api_key_status = "✅ Set" if env_status["hidden_vars_set"]["REDMINE_API_KEY"] else "❌ Not Set"
        st.metric("Redmine API Key", api_key_status)
    
    if not all(env_status["hidden_vars_set"].values()):
        show_warning_message("Some security settings are not configured. Check your .env file.")
    
    # Redmine connection test
    st.markdown("---")
    st.markdown("### 🔗 Redmine Connection Test")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if st.button("🧪 Test Connection", type="primary"):
            with st.spinner("Testing Redmine connection..."):
                connection_ok = auth_service.test_redmine_connection()
            
            if connection_ok:
                show_success_message("Redmine connection successful!")
            else:
                show_error_message("Redmine connection failed. Check your configuration.")
    
    with col2:
        st.info("""
        **Connection Test verifies:**
        - Redmine URL accessibility
        - API key validity
        - Network connectivity
        """)
    
    # Advanced settings
    st.markdown("---")
    with st.expander("🔧 Advanced Settings"):
        st.markdown("**Environment File Information:**")
        st.code(f"File Path: {env_status['file_path']}")
        
        if env_status["file_exists"]:
            st.markdown("**File Contents Preview (non-sensitive):**")
            try:
                with open(env_manager.env_file_path, 'r') as f:
                    lines = f.readlines()
                
                preview_lines = []
                for line in lines:
                    # Hide sensitive values
                    if any(sensitive in line for sensitive in ["SECRET", "KEY", "TOKEN"]):
                        if "=" in line:
                            key_part = line.split("=")[0]
                            preview_lines.append(f"{key_part}=***HIDDEN***\n")
                        else:
                            preview_lines.append("***HIDDEN***\n")
                    else:
                        preview_lines.append(line)
                
                st.code("".join(preview_lines))
                
            except Exception as e:
                st.error(f"Cannot read file: {e}")
        
        # Manual reload button
        if st.button("🔄 Reload Environment Variables"):
            env_manager.reload_env()
            show_success_message("Environment variables reloaded")
            st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "System Settings | Configuration Management"
        "</div>", 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    show_admin_settings() 