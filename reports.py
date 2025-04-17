import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
import database as db
import excel_handler
import utils

def manage_report_templates():
    """Manage report templates (Admin only)."""
    if st.session_state.user_role != "admin":
        st.error("You don't have permission to access this page")
        return
    
    st.title("Report Template Management")
    
    # Create tabs for viewing and managing templates
    tab1, tab2 = st.tabs(["View Templates", "Add/Edit Template"])
    
    with tab1:
        # Get all report templates
        templates_df = db.get_report_templates()
        
        if templates_df is not None and not templates_df.empty:
            # Format the fields column to show it better
            templates_df['fields'] = templates_df['fields'].apply(lambda x: ', '.join(json.loads(x)) if isinstance(x, str) else '')
            
            # Display the templates
            st.dataframe(templates_df[['id', 'name', 'description', 'fields', 'department']], use_container_width=True)
            
            # Template deletion
            with st.expander("Delete Template"):
                template_to_delete = st.selectbox(
                    "Select template to delete",
                    options=templates_df['id'].tolist(),
                    format_func=lambda x: templates_df.loc[templates_df['id'] == x, 'name'].iloc[0]
                )
                
                if st.button("Delete Template"):
                    if db.delete_report_template(template_to_delete):
                        st.success("Template deleted successfully")
                        st.rerun()
                    else:
                        st.error("Failed to delete template")
        else:
            st.info("No report templates found")
    
    with tab2:
        # Get all departments for the dropdown
        departments = db.get_organization_departments()
        
        # Template editing/creation form
        edit_mode = False
        template_id = None
        
        # Check if we're in edit mode
        if st.checkbox("Edit Existing Template"):
            edit_mode = True
            if templates_df is not None and not templates_df.empty:
                template_to_edit = st.selectbox(
                    "Select template to edit",
                    options=templates_df['id'].tolist(),
                    format_func=lambda x: templates_df.loc[templates_df['id'] == x, 'name'].iloc[0]
                )
                
                # Get the template data
                template_data = db.get_report_template(template_to_edit)
                if template_data:
                    template_id = template_data['id']
                    default_name = template_data['name']
                    default_description = template_data['description']
                    default_fields = json.loads(template_data['fields'])
                    default_department_id = template_data['department_id']
                else:
                    st.error("Failed to load template data")
                    return
            else:
                st.info("No templates to edit")
                return
        else:
            default_name = ""
            default_description = ""
            default_fields = []
            default_department_id = None if departments.empty else departments['id'].iloc[0]
        
        # Form for adding/editing template
        with st.form("template_form"):
            name = st.text_input("Template Name", value=default_name if edit_mode else "")
            description = st.text_area("Description", value=default_description if edit_mode else "")
            
            # Dynamic fields section
            st.subheader("Template Fields")
            
            if edit_mode and default_fields:
                field_count = len(default_fields)
            else:
                field_count = 3  # Default number of fields
            
            field_count = st.number_input("Number of Fields", min_value=1, value=field_count)
            
            fields = []
            for i in range(field_count):
                field_default = default_fields[i] if edit_mode and i < len(default_fields) else ""
                field = st.text_input(f"Field {i+1}", value=field_default, key=f"field_{i}")
                if field:
                    fields.append(field)
            
            # Department selection
            if departments is not None and not departments.empty:
                department_options = departments['id'].tolist()
                department_names = {row['id']: row['name'] for _, row in departments.iterrows()}
                
                department_id = st.selectbox(
                    "Department",
                    options=department_options,
                    format_func=lambda x: department_names.get(x, "Unknown"),
                    index=department_options.index(default_department_id) if default_department_id in department_options else 0
                )
            else:
                st.error("No departments found. Please create departments first.")
                department_id = None
            
            # Submit button
            submit_button = st.form_submit_button("Submit")
            
            if submit_button:
                if not name:
                    st.error("Template name is required")
                elif not fields:
                    st.error("At least one field is required")
                elif department_id is None:
                    st.error("Please select a department")
                else:
                    # Convert fields to JSON string
                    fields_json = json.dumps(fields)
                    
                    success = False
                    if edit_mode:
                        # Update existing template
                        success = db.update_report_template(template_id, name, description, fields_json, department_id)
                        message = "Template updated successfully"
                    else:
                        # Add new template
                        success = db.add_report_template(name, description, fields_json, department_id)
                        message = "Template added successfully"
                    
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error("Operation failed")

def assign_reports():
    """Assign reports to organizations (Admin and Department roles)."""
    if st.session_state.user_role not in ["admin", "department"]:
        st.error("You don't have permission to access this page")
        return
    
    st.title("Assign Reports")
    
    # Get report templates
    if st.session_state.user_role == "admin":
        # Admin can assign any report template
        templates_df = db.get_report_templates()
    else:
        # Department can only assign templates for their department
        # Filter templates by department_id matching user_org_id
        templates_df = db.get_report_templates()
        if templates_df is not None and not templates_df.empty:
            templates_df = templates_df[templates_df['department_id'] == st.session_state.user_org_id]
    
    # Get organizations (units)
    units_df = db.get_organization_units()
    
    if templates_df is None or templates_df.empty:
        st.error("No report templates available")
        return
    
    if units_df is None or units_df.empty:
        st.error("No units available to assign reports to")
        return
    
    # Create tabs for viewing and assigning reports
    tab1, tab2 = st.tabs(["Assigned Reports", "Assign New Report"])
    
    with tab1:
        # Get all assigned reports
        assigned_reports = db.get_assigned_reports()
        
        if assigned_reports is not None and not assigned_reports.empty:
            st.dataframe(assigned_reports, use_container_width=True)
        else:
            st.info("No reports have been assigned yet")
    
    with tab2:
        with st.form("assign_report_form"):
            # Template selection
            template_id = st.selectbox(
                "Select Report Template",
                options=templates_df['id'].tolist(),
                format_func=lambda x: templates_df.loc[templates_df['id'] == x, 'name'].iloc[0]
            )
            
            # Organization selection
            organization_id = st.selectbox(
                "Select Organization",
                options=units_df['id'].tolist(),
                format_func=lambda x: units_df.loc[units_df['id'] == x, 'name'].iloc[0]
            )
            
            # Due date selection
            min_date = datetime.now().date() + timedelta(days=1)
            default_due_date = datetime.now().date() + timedelta(days=7)
            due_date = st.date_input("Due Date", value=default_due_date, min_value=min_date)
            
            # Submit button
            submit_button = st.form_submit_button("Assign Report")
            
            if submit_button:
                if db.assign_report(template_id, organization_id, due_date):
                    st.success("Report assigned successfully")
                    st.rerun()
                else:
                    st.error("Failed to assign report")

def view_my_reports():
    """View reports assigned to the user's organization."""
    if st.session_state.user_role == "unit":
        # For units, show reports assigned to them
        st.title("My Assigned Reports")
        assigned_reports = db.get_organization_assigned_reports(st.session_state.user_org_id)
        
        if assigned_reports is not None and not assigned_reports.empty:
            # Display reports with expanders for details
            for _, report in assigned_reports.iterrows():
                with st.expander(f"{report['report_name']} - Due: {report['due_date']}"):
                    st.write(f"**Description:** {report['description']}")
                    st.write(f"**Status:** {report['status']}")
                    
                    # Display submission if completed
                    if report['status'] == 'completed':
                        submission = db.get_report_submission(report['id'])
                        if submission:
                            st.write(f"**Submitted at:** {submission['submitted_at']}")
                            st.write("**Submitted data:**")
                            
                            try:
                                data = json.loads(submission['data'])
                                for field, value in data.items():
                                    st.write(f"**{field}:** {value}")
                            except:
                                st.write(submission['data'])
                            
                            # Download as Excel button
                            if st.button(f"Download as Excel", key=f"download_{report['id']}"):
                                excel_file = excel_handler.create_excel_from_report(report, submission)
                                st.download_button(
                                    label="Download Excel",
                                    data=excel_file,
                                    file_name=f"{report['report_name']}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    key=f"dl_{report['id']}"
                                )
                    
                    # Show submit button for pending reports
                    if report['status'] == 'pending':
                        if st.button(f"Submit Report", key=f"submit_{report['id']}"):
                            st.session_state.current_report = report['id']
                            st.session_state.current_report_name = report['report_name']
                            st.rerun()
        else:
            st.info("No reports assigned to your organization")
    
    elif st.session_state.user_role in ["admin", "department"]:
        # For admin and department roles, show reports they manage
        st.title("Reports Overview")
        
        # Get all assigned reports or filter by department
        if st.session_state.user_role == "admin":
            assigned_reports = db.get_assigned_reports()
        else:
            # Get reports for templates belonging to this department
            assigned_reports = db.get_assigned_reports()
            # TODO: Filter by department
        
        if assigned_reports is not None and not assigned_reports.empty:
            # Add filters
            status_filter = st.multiselect(
                "Filter by Status",
                options=["pending", "completed", "overdue"],
                default=[]
            )
            
            # Apply filters
            filtered_reports = assigned_reports
            if status_filter:
                filtered_reports = filtered_reports[filtered_reports['status'].isin(status_filter)]
            
            # Display filtered reports
            st.dataframe(filtered_reports, use_container_width=True)
            
            # Show details for selected report
            if not filtered_reports.empty:
                selected_report_id = st.selectbox(
                    "Select Report to View Details",
                    options=filtered_reports['id'].tolist(),
                    format_func=lambda x: f"{filtered_reports.loc[filtered_reports['id'] == x, 'report_name'].iloc[0]} - {filtered_reports.loc[filtered_reports['id'] == x, 'organization'].iloc[0]}"
                )
                
                # Get full report details and submission if available
                report_details = assigned_reports[assigned_reports['id'] == selected_report_id].iloc[0]
                submission = db.get_report_submission(selected_report_id)
                
                st.subheader(f"Report Details: {report_details['report_name']}")
                st.write(f"**Organization:** {report_details['organization']}")
                st.write(f"**Due Date:** {report_details['due_date']}")
                st.write(f"**Status:** {report_details['status']}")
                
                if submission:
                    st.write(f"**Submitted at:** {submission['submitted_at']}")
                    st.write("**Submitted data:**")
                    
                    try:
                        data = json.loads(submission['data'])
                        for field, value in data.items():
                            st.write(f"**{field}:** {value}")
                    except:
                        st.write(submission['data'])
                    
                    # Download as Excel button
                    if st.button(f"Download as Excel", key=f"download_{selected_report_id}"):
                        excel_file = excel_handler.create_excel_from_report(report_details, submission)
                        st.download_button(
                            label="Download Excel",
                            data=excel_file,
                            file_name=f"{report_details['report_name']}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
        else:
            st.info("No reports found")

def submit_report():
    """Submit a report."""
    if st.session_state.user_role != "unit":
        st.error("Only unit users can submit reports")
        return
    
    st.title("Submit Report")
    
    # Check if we're coming from a specific report
    if 'current_report' in st.session_state:
        report_id = st.session_state.current_report
        report_name = st.session_state.current_report_name
        
        # Clear the current report from session
        del st.session_state.current_report
        del st.session_state.current_report_name
    else:
        # Get pending reports for the unit
        assigned_reports = db.get_organization_assigned_reports(st.session_state.user_org_id)
        if assigned_reports is None or assigned_reports.empty:
            st.info("No pending reports to submit")
            return
        
        # Filter for pending reports
        pending_reports = assigned_reports[assigned_reports['status'] == 'pending']
        if pending_reports.empty:
            st.info("No pending reports to submit")
            return
        
        # Let user select a report to submit
        report_id = st.selectbox(
            "Select Report to Submit",
            options=pending_reports['id'].tolist(),
            format_func=lambda x: f"{pending_reports.loc[pending_reports['id'] == x, 'report_name'].iloc[0]} - Due: {pending_reports.loc[pending_reports['id'] == x, 'due_date'].iloc[0]}"
        )
        
        report_name = pending_reports.loc[pending_reports['id'] == report_id, 'report_name'].iloc[0]
    
    # Get the report template fields
    report_details = db.get_organization_assigned_reports(st.session_state.user_org_id)
    report_details = report_details[report_details['id'] == report_id].iloc[0]
    fields = json.loads(report_details['fields'])
    
    st.subheader(f"Submit Report: {report_name}")
    st.write(f"Due Date: {report_details['due_date']}")
    
    # Create tabs for manual entry and Excel upload
    tab1, tab2 = st.tabs(["Manual Entry", "Excel Upload"])
    
    with tab1:
        with st.form("report_submission_form"):
            # Create input fields based on the template
            field_values = {}
            for field in fields:
                value = st.text_input(field)
                field_values[field] = value
            
            # Submit button
            submit_button = st.form_submit_button("Submit Report")
            
            if submit_button:
                # Validate that all fields have values
                if all(field_values.values()):
                    # Convert to JSON
                    data_json = json.dumps(field_values)
                    
                    # Submit the report
                    if db.submit_report_data(report_id, data_json):
                        st.success("Report submitted successfully")
                        # Clear the form
                        for field in fields:
                            st.session_state[field] = ""
                        st.rerun()
                    else:
                        st.error("Failed to submit report")
                else:
                    st.error("All fields are required")
    
    with tab2:
        st.write("Upload your report data in Excel format")
        
        # Download template button
        template_excel = excel_handler.create_report_template(fields)
        st.download_button(
            label="Download Template",
            data=template_excel,
            file_name=f"{report_name}_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # Upload file
        uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
        
        if uploaded_file is not None:
            # Process the uploaded file
            try:
                field_values = excel_handler.parse_excel_report(uploaded_file, fields)
                
                # Show the parsed data
                st.subheader("Parsed Data")
                for field, value in field_values.items():
                    st.write(f"**{field}:** {value}")
                
                # Submit button
                if st.button("Submit Report Data"):
                    # Convert to JSON
                    data_json = json.dumps(field_values)
                    
                    # Submit the report
                    if db.submit_report_data(report_id, data_json):
                        st.success("Report submitted successfully")
                        st.rerun()
                    else:
                        st.error("Failed to submit report")
            except Exception as e:
                st.error(f"Error processing Excel file: {str(e)}")

def view_report_status():
    """View the status of all reports (Admin and Department roles)."""
    if st.session_state.user_role not in ["admin", "department"]:
        st.error("You don't have permission to access this page")
        return
    
    st.title("Report Status")
    
    # Get all assigned reports
    if st.session_state.user_role == "admin":
        assigned_reports = db.get_assigned_reports()
    else:
        # Filter reports by department
        assigned_reports = db.get_assigned_reports()
        # TODO: Filter by department
    
    if assigned_reports is not None and not assigned_reports.empty:
        # Add filters
        status_filter = st.multiselect(
            "Filter by Status",
            options=["pending", "completed", "overdue"],
            default=[]
        )
        
        organization_filter = st.multiselect(
            "Filter by Organization",
            options=assigned_reports['organization'].unique().tolist(),
            default=[]
        )
        
        # Apply filters
        filtered_reports = assigned_reports
        if status_filter:
            filtered_reports = filtered_reports[filtered_reports['status'].isin(status_filter)]
        if organization_filter:
            filtered_reports = filtered_reports[filtered_reports['organization'].isin(organization_filter)]
        
        # Display filtered reports
        st.dataframe(filtered_reports, use_container_width=True)
        
        # Status summary
        st.subheader("Status Summary")
        status_counts = filtered_reports['status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        
        # Create a pie chart
        import plotly.express as px
        fig = px.pie(
            status_counts, 
            values='Count', 
            names='Status',
            color='Status',
            color_discrete_map={
                'completed': '#0066b2',
                'pending': '#fcba03',
                'overdue': '#fc0303'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Export to Excel
        if st.button("Export to Excel"):
            excel_file = excel_handler.create_status_report(filtered_reports)
            st.download_button(
                label="Download Excel Report",
                data=excel_file,
                file_name="report_status.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.info("No reports found")
