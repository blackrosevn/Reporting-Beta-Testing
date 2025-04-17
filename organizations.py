import streamlit as st
import pandas as pd
import database as db

def manage_organizations():
    """Manage organizations in the system (Admin only)."""
    if st.session_state.user_role != "admin":
        st.error("You don't have permission to access this page")
        return
    
    st.title("Organization Management")
    
    # Get all organizations
    organizations_df = db.get_organizations()
    
    # Create tabs for viewing and managing organizations
    tab1, tab2 = st.tabs(["View Organizations", "Add/Edit Organization"])
    
    with tab1:
        if organizations_df is not None and not organizations_df.empty:
            # Create a parent name column for better display
            orgs_with_parent = organizations_df.copy()
            orgs_with_parent['parent_name'] = None
            
            for idx, row in orgs_with_parent.iterrows():
                if row['parent_id'] is not None:
                    parent_row = orgs_with_parent[orgs_with_parent['id'] == row['parent_id']]
                    if not parent_row.empty:
                        orgs_with_parent.at[idx, 'parent_name'] = parent_row.iloc[0]['name']
            
            # Display the organizations
            st.dataframe(orgs_with_parent[['id', 'name', 'type', 'parent_name']], use_container_width=True)
            
            # Organization deletion
            with st.expander("Delete Organization"):
                org_to_delete = st.selectbox(
                    "Select organization to delete",
                    options=organizations_df['id'].tolist(),
                    format_func=lambda x: organizations_df.loc[organizations_df['id'] == x, 'name'].iloc[0]
                )
                
                if st.button("Delete Organization"):
                    # Check if this organization has dependent organizations
                    if organizations_df is not None and not organizations_df.empty:
                        dependents = organizations_df[organizations_df['parent_id'] == org_to_delete]
                        if not dependents.empty:
                            st.error("Cannot delete this organization as it has dependent organizations.")
                            return
                    
                    if db.delete_organization(org_to_delete):
                        st.success("Organization deleted successfully")
                        st.rerun()
                    else:
                        st.error("Failed to delete organization")
        else:
            st.info("No organizations found")
    
    with tab2:
        # Organization editing/creation form
        edit_mode = False
        org_id = None
        
        # Check if we're in edit mode
        if st.checkbox("Edit Existing Organization"):
            edit_mode = True
            if organizations_df is not None and not organizations_df.empty:
                org_to_edit = st.selectbox(
                    "Select organization to edit",
                    options=organizations_df['id'].tolist(),
                    format_func=lambda x: organizations_df.loc[organizations_df['id'] == x, 'name'].iloc[0]
                )
                
                # Get the organization data
                org_data = organizations_df.loc[organizations_df['id'] == org_to_edit].iloc[0]
                org_id = org_data['id']
                default_name = org_data['name']
                default_type = org_data['type']
                default_parent_id = org_data['parent_id']
            else:
                st.info("No organizations to edit")
                return
        else:
            default_name = ""
            default_type = "unit"
            default_parent_id = None
        
        # Form for adding/editing organization
        with st.form("organization_form"):
            name = st.text_input("Organization Name", value=default_name if edit_mode else "")
            
            # Organization type
            org_type = st.selectbox(
                "Organization Type",
                options=["unit", "department", "holding"],
                index=["unit", "department", "holding"].index(default_type) if edit_mode else 0
            )
            
            # Parent organization selection
            parent_options = [None]  # None means no parent
            if organizations_df is not None and not organizations_df.empty:
                # Filter out the current org (for edit mode) and potential circular references
                filtered_orgs = organizations_df
                if edit_mode:
                    filtered_orgs = organizations_df[organizations_df['id'] != org_id]
                
                parent_options.extend(filtered_orgs['id'].tolist())
                
                parent_name_map = {None: "None (Top Level)"}
                for _, org in filtered_orgs.iterrows():
                    parent_name_map[org['id']] = org['name']
                
                parent_id = st.selectbox(
                    "Parent Organization",
                    options=parent_options,
                    format_func=lambda x: parent_name_map.get(x, "Unknown"),
                    index=parent_options.index(default_parent_id) if default_parent_id in parent_options else 0
                )
            else:
                parent_id = None
            
            # Submit button
            submit_button = st.form_submit_button("Submit")
            
            if submit_button:
                if not name:
                    st.error("Organization name is required")
                else:
                    success = False
                    if edit_mode:
                        # Update existing organization
                        success = db.update_organization(org_id, name, org_type, parent_id)
                        message = "Organization updated successfully"
                    else:
                        # Add new organization
                        success = db.add_organization(name, org_type, parent_id)
                        message = "Organization added successfully"
                    
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error("Operation failed")
