"""
Tickets interface page for CV Converter Web Application
Handles ticket listing, search, filtering, and creation
"""

import streamlit as st
from datetime import datetime
from ..auth.auth_service import AuthService
from ..models.ticket import TicketManager, Ticket
from ..utils.helpers import (
    show_success_message, show_error_message, show_warning_message, 
    show_info_message, format_datetime
)

def show_tickets_page():
    """Display the tickets interface page"""
    # Initialize auth service and require authentication
    auth_service = AuthService()
    auth_service.require_authentication()
    
    # Get current user
    current_user = auth_service.get_current_user()
    
    # Initialize ticket manager
    ticket_manager = TicketManager()
    
    # Page header
    st.title("🎫 Redmine Tickets")
    st.markdown(f"Ticket management | Logged in as **{current_user.username}**")
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
    
    # Initialize session state for tickets
    if "tickets_page" not in st.session_state:
        st.session_state.tickets_page = 1
    if "tickets_search" not in st.session_state:
        st.session_state.tickets_search = ""
    if "tickets_filter" not in st.session_state:
        st.session_state.tickets_filter = "this_week"
    if "tickets_status" not in st.session_state:
        st.session_state.tickets_status = "open"
    
    # Main content tabs
    tab1, tab2 = st.tabs(["📋 Ticket List", "➕ New Ticket"])
    
    with tab1:
        show_ticket_list(auth_service, ticket_manager, current_user)
    
    with tab2:
        show_new_ticket_form(auth_service, ticket_manager, current_user)

def show_ticket_list(auth_service: AuthService, ticket_manager: TicketManager, current_user):
    """Display the ticket list with filtering and pagination"""
    
    st.markdown("### 📋 Your Tickets")
    
    # Filters row
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        search_query = st.text_input(
            "🔍 Search tickets",
            value=st.session_state.tickets_search,
            placeholder="Search by ID, subject, or description...",
            key="search_input"
        )
        if search_query != st.session_state.tickets_search:
            st.session_state.tickets_search = search_query
            st.session_state.tickets_page = 1  # Reset to first page on search
    
    with col2:
        date_filter = st.selectbox(
            "📅 Date Range",
            options=["this_week", "last_week", "this_month", "last_month", "all"],
            format_func=lambda x: {
                "this_week": "This Week",
                "last_week": "Last Week", 
                "this_month": "This Month",
                "last_month": "Last Month",
                "all": "All Time"
            }[x],
            index=["this_week", "last_week", "this_month", "last_month", "all"].index(st.session_state.tickets_filter),
            key="date_filter"
        )
        if date_filter != st.session_state.tickets_filter:
            st.session_state.tickets_filter = date_filter
            st.session_state.tickets_page = 1
    
    with col3:
        status_filter = st.selectbox(
            "📊 Status",
            options=["open", "closed", "all"],
            format_func=lambda x: x.title(),
            index=["open", "closed", "all"].index(st.session_state.tickets_status),
            key="status_filter"
        )
        if status_filter != st.session_state.tickets_status:
            st.session_state.tickets_status = status_filter
            st.session_state.tickets_page = 1
    
    with col4:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    # Add credential status and options
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Check if we have session credentials
        credentials = auth_service.get_user_credentials()
        if credentials:
            st.success("🔐 Session credentials available - using your personal Redmine access")
        else:
            st.warning("🔑 Using system API key - may show limited tickets")
    
    with col2:
        if st.button("🔐 Enter Credentials", use_container_width=True):
            st.session_state.show_credential_form = True
    
    # Show credential form if requested
    if st.session_state.get("show_credential_form", False):
        show_credential_form(auth_service)
    
    # Load tickets with loading spinner
    with st.spinner("🔍 Loading tickets..."):
        # Get credentials - try session first, fallback to API key
        credentials = auth_service.get_user_credentials()
        
        if credentials:
            # Use stored session credentials
            username, password = credentials
            use_api_key = False
            st.info("🔐 Using session credentials for Redmine access")
        else:
            # Use API key method
            username = current_user.username
            password = ""
            use_api_key = True
            st.info("🔑 Using API key for Redmine access")
        
        tickets, total_count, error = ticket_manager.get_tickets(
            username=username,
            password=password,
            assigned_to_me=True,
            status_filter=st.session_state.tickets_status,
            date_filter=st.session_state.tickets_filter,
            search_query=st.session_state.tickets_search,
            page=st.session_state.tickets_page,
            use_api_key=use_api_key
        )

    if error:
        show_error_message(f"Failed to load tickets: {error}")
        st.markdown("**Possible solutions:**")
        st.markdown("- Check your Redmine credentials")
        st.markdown("- Verify network connection")
        st.markdown("- Contact administrator if API key is misconfigured")
        return
    
    # Display results summary
    if tickets:
        results_text = f"Showing {len(tickets)} of {total_count} tickets"
        if st.session_state.tickets_search:
            results_text += f" matching '{st.session_state.tickets_search}'"
        st.markdown(f"**{results_text}**")
    else:
        st.info("No tickets found matching your criteria.")
        return
    
    # Pagination controls (top)
    if total_count > ticket_manager.tickets_per_page:
        show_pagination_controls(total_count, ticket_manager.tickets_per_page, "top")
    
    # Tickets display
    for ticket in tickets:
        display_ticket_card(ticket)
    
    # Pagination controls (bottom)
    if total_count > ticket_manager.tickets_per_page:
        show_pagination_controls(total_count, ticket_manager.tickets_per_page, "bottom")

def display_ticket_card(ticket: Ticket):
    """Display a single ticket card"""
    with st.container():
        # Ticket header
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"### #{ticket.id}: {ticket.subject}")
        
        with col2:
            status_color = "🟢" if ticket.status_name.lower() in ["new", "open"] else "🔴"
            st.markdown(f"**Status:** {status_color} {ticket.status_name}")
        
        with col3:
            priority_icon = "🔥" if ticket.priority_name.lower() == "high" else "📝"
            st.markdown(f"**Priority:** {priority_icon} {ticket.priority_name}")
        
        # Ticket details
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if ticket.description:
                with st.expander("📄 Description"):
                    st.write(ticket.description)
            else:
                st.caption("*No description*")
        
        with col2:
            st.write(f"**Author:** {ticket.author_name}")
            if ticket.assigned_to_name:
                st.write(f"**Assigned:** {ticket.assigned_to_name}")
            # st.write(f"**Created:** {format_datetime(ticket.created_on)}")
            # st.write(f"**Updated:** {format_datetime(ticket.updated_on)}")
            st.write(f"**Created:** {ticket.created_on}")
            st.write(f"**Updated:** {ticket.updated_on}")
        
        # Action buttons
        col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
        
        with col1:
            if st.button("👁️ View", key=f"view_{ticket.id}"):
                st.session_state.selected_ticket = ticket.id
                show_info_message(f"Selected ticket #{ticket.id}")
        
        with col2:
            if st.button("📎 Attach File", key=f"attach_{ticket.id}"):
                st.session_state.attach_to_ticket = ticket.id
                show_info_message("File attachment feature coming soon!")
        
        with col3:
            if st.button("🔄 Convert CV", key=f"convert_{ticket.id}"):
                st.session_state.convert_ticket = ticket.id
                st.query_params.page = "converter"
                st.query_params.ticket_id = str(ticket.id)
                st.rerun()
        
        st.divider()

def show_pagination_controls(total_count: int, per_page: int, position: str):
    """Display pagination controls"""
    total_pages = (total_count + per_page - 1) // per_page
    current_page = st.session_state.tickets_page
    
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
    
    with col1:
        if st.button("⏮️ First", key=f"first_{position}", disabled=current_page <= 1):
            st.session_state.tickets_page = 1
            st.rerun()
    
    with col2:
        if st.button("⏪ Prev", key=f"prev_{position}", disabled=current_page <= 1):
            st.session_state.tickets_page = max(1, current_page - 1)
            st.rerun()
    
    with col3:
        st.markdown(f"<div style='text-align: center; padding: 0.5rem;'>Page {current_page} of {total_pages}</div>", 
                   unsafe_allow_html=True)
    
    with col4:
        if st.button("Next ⏩", key=f"next_{position}", disabled=current_page >= total_pages):
            st.session_state.tickets_page = min(total_pages, current_page + 1)
            st.rerun()
    
    with col5:
        if st.button("Last ⏭️", key=f"last_{position}", disabled=current_page >= total_pages):
            st.session_state.tickets_page = total_pages
            st.rerun()

def show_new_ticket_form(auth_service: AuthService, ticket_manager: TicketManager, current_user):
    """Display the new ticket creation form"""
    
    st.markdown("### ➕ Create New Ticket")
    
    with st.form("new_ticket_form"):
        # Basic ticket information
        col1, col2 = st.columns([2, 1])
        
        with col1:
            subject = st.text_input(
                "📋 Subject *",
                placeholder="Brief description of the ticket",
                help="Required field"
            )
            
            description = st.text_area(
                "📄 Description *",
                placeholder="Detailed description of the ticket",
                height=100,
                help="Required field"
            )
        
        with col2:
            st.markdown("**📝 Naming Convention**")
            st.caption("For CV conversion tickets, use:")
            
            candidate_name = st.text_input(
                "👤 Candidate Name",
                placeholder="e.g., John Doe",
                help="Will be used in ticket title"
            )
            
            stack = st.text_input(
                "💻 Technology Stack",
                placeholder="e.g., Python Developer",
                help="Will be used in ticket title"
            )
            
            if candidate_name and stack:
                st.success(f"📌 Title preview: **{candidate_name} ({stack})**")
        
        # Additional metadata
        st.markdown("---")
        st.markdown("**🔧 Additional Information**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # This would be populated from CV extraction in the future
            contacts = st.text_area(
                "📞 Contact Information",
                placeholder="Phone, email, LinkedIn (extracted from CV)",
                help="This will be auto-populated from CV parsing"
            )
        
        with col2:
            additional_notes = st.text_area(
                "📝 Additional Notes",
                placeholder="Any additional information",
                help="Optional field"
            )
        
        # Form submission
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            submit_button = st.form_submit_button("✅ Create Ticket", type="primary")
        
        with col2:
            clear_button = st.form_submit_button("🗑️ Clear Form")
    
    # Handle form submission
    if submit_button:
        if not subject or not description:
            show_error_message("Subject and description are required fields")
            return
        
        # Combine description with additional info
        full_description = description
        if contacts:
            full_description += f"\n\n**Contact Information:**\n{contacts}"
        if additional_notes:
            full_description += f"\n\n**Additional Notes:**\n{additional_notes}"
        
        # Create ticket
        with st.spinner("🎫 Creating ticket..."):
            # Get credentials - try session first, fallback to API key
            credentials = auth_service.get_user_credentials()
            
            if credentials:
                # Use stored session credentials
                username, password = credentials
                use_api_key = False
            else:
                # Use API key method
                username = current_user.username
                password = ""
                use_api_key = True
            
            ticket, error = ticket_manager.create_ticket(
                subject=subject,
                description=full_description,
                candidate_name=candidate_name,
                stack=stack,
                username=username,
                password=password,
                use_api_key=use_api_key
            )
        
        if ticket:
            show_success_message(f"Ticket #{ticket.id} created successfully!")
            st.balloons()
            # Clear form by rerunning
            st.rerun()
        else:
            show_error_message(f"Failed to create ticket: {error}")
    
    if clear_button:
        st.rerun()

def show_credential_form(auth_service: AuthService):
    """Display form for entering Redmine credentials"""
    st.markdown("### 🔐 Enter Redmine Credentials")
    st.info("Enter your Redmine credentials to access tickets with your personal permissions. Credentials are stored temporarily in your session only.")
    
    with st.form("redmine_credentials"):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input(
                "👤 Redmine Username", 
                value=st.session_state.get("username", ""),
                help="Your Redmine username"
            )
        
        with col2:
            password = st.text_input(
                "🔒 Redmine Password", 
                type="password",
                help="Your Redmine password (stored in session only)"
            )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            submit = st.form_submit_button("✅ Save Credentials", type="primary")
        
        with col2:
            clear = st.form_submit_button("🗑️ Clear Credentials")
        
        with col3:
            cancel = st.form_submit_button("❌ Cancel")
    
    if submit:
        if not username or not password:
            show_error_message("Both username and password are required")
            return
        
        # Store credentials in session
        auth_service.store_user_credentials(username, password)
        st.session_state.show_credential_form = False
        show_success_message("Credentials saved for this session!")
        st.rerun()
    
    if clear:
        auth_service.clear_user_credentials()
        st.session_state.show_credential_form = False
        show_success_message("Credentials cleared!")
        st.rerun()
    
    if cancel:
        st.session_state.show_credential_form = False
        st.rerun()

if __name__ == "__main__":
    show_tickets_page() 