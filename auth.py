import streamlit as st
import pandas as pd
import database as db
import utils

def login_page():
    """Display the login page for user authentication."""
    st.title("Vinatex Report Portal")
    
    # Center the login form
    _, login_col, _ = st.columns([1, 2, 1])
    
    with login_col:
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if not username or not password:
                st.error("Please enter both username and password")
            else:
                user = db.validate_user(username, password)
                if user:
                    # Store user information in session state
                    st.session_state.authenticated = True
                    st.session_state.user_id = user['id']
                    st.session_state.user_role = user['role']
                    st.session_state.user_org_id = user['organization_id']
                    st.session_state.username = user['username']
                    st.rerun()
                else:
                    st.error("Invalid username or password")

def logout():
    """Log out the current user."""
    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.user_role = None
    st.session_state.user_org_id = None
    st.session_state.username = None

def manage_users():
    """Manage users in the system (Admin only)."""
    if st.session_state.user_role != "admin":
        st.error("You don't have permission to access this page")
        return
    
    st.title("User Management")
    
    # Get all users
    users_df = db.get_users()
    
    # Create tabs for viewing and managing users
    tab1, tab2 = st.tabs(["View Users", "Add/Edit User"])
    
    with tab1:
        if users_df is not None and not users_df.empty:
            st.dataframe(users_df, use_container_width=True)
            
            # User deletion
            with st.expander("Delete User"):
                user_to_delete = st.selectbox(
                    "Select user to delete",
                    options=users_df['id'].tolist(),
                    format_func=lambda x: users_df.loc[users_df['id'] == x, 'username'].iloc[0]
                )
                
                if st.button("Delete User"):
                    if db.delete_user(user_to_delete):
                        st.success("User deleted successfully")
                        st.rerun()
                    else:
                        st.error("Failed to delete user")
        else:
            st.info("No users found")
    
    with tab2:
        # Get all organizations for the dropdown
        organizations = db.get_organizations()
        
        # User editing/creation form
        edit_mode = False
        user_id = None
        
        # Check if we're in edit mode
        if st.checkbox("Edit Existing User"):
            edit_mode = True
            if users_df is not None and not users_df.empty:
                user_to_edit = st.selectbox(
                    "Select user to edit",
                    options=users_df['id'].tolist(),
                    format_func=lambda x: users_df.loc[users_df['id'] == x, 'username'].iloc[0]
                )
                
                # Get the user data
                user_data = users_df.loc[users_df['id'] == user_to_edit].iloc[0]
                user_id = user_data['id']
                default_username = user_data['username']
                default_role = user_data['role']
                
                # Find the organization_id for this user
                org_id = None
                for _, org in organizations.iterrows():
                    if org['name'] == user_data['organization']:
                        org_id = org['id']
                        break
            else:
                st.info("No users to edit")
                return
        else:
            default_username = ""
            default_role = "unit"
            org_id = None
        
        # Form for adding/editing user
        with st.form("user_form"):
            username = st.text_input("Username", value=default_username if edit_mode else "")
            
            # Password field (required for new users, optional for editing)
            if edit_mode:
                password = st.text_input("Password (leave blank to keep current)", type="password")
                st.info("Leave password blank to keep the current password.")
            else:
                password = st.text_input("Password", type="password")
            
            # Role selection
            role = st.selectbox(
                "Role",
                options=["admin", "department", "unit"],
                index=["admin", "department", "unit"].index(default_role) if edit_mode else 0
            )
            
            # Organization selection
            if organizations is not None and not organizations.empty:
                organization_id = st.selectbox(
                    "Organization",
                    options=organizations['id'].tolist(),
                    format_func=lambda x: organizations.loc[organizations['id'] == x, 'name'].iloc[0],
                    index=organizations['id'].tolist().index(org_id) if org_id is not None else 0
                )
            else:
                st.error("No organizations found. Please create organizations first.")
                organization_id = None
            
            # Submit button
            submit_button = st.form_submit_button("Submit")
            
            if submit_button:
                if not username:
                    st.error("Username is required")
                elif not password and not edit_mode:
                    st.error("Password is required for new users")
                elif organization_id is None:
                    st.error("Please select an organization")
                else:
                    success = False
                    if edit_mode:
                        # Update existing user
                        success = db.update_user(user_id, username, password, role, organization_id)
                        message = "User updated successfully"
                    else:
                        # Add new user
                        success = db.add_user(username, password, role, organization_id)
                        message = "User added successfully"
                    
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error("Operation failed")
