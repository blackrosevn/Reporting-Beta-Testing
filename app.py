import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# Import local modules
import database as db
import auth
import reports
import organizations
import excel_handler
import utils

# Initialize session state variables if they don't exist
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_org_id' not in st.session_state:
    st.session_state.user_org_id = None
if 'username' not in st.session_state:
    st.session_state.username = None

# Page configuration
st.set_page_config(
    page_title="Vinatex Report Portal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Authentication
if not st.session_state.authenticated:
    auth.login_page()
else:
    # Main application
    st.sidebar.title(f"Welcome, {st.session_state.username}")
    
    # Logout button
    if st.sidebar.button("Logout"):
        auth.logout()
        st.rerun()
    
    # Navigation
    page = st.sidebar.selectbox(
        "Navigation",
        options=utils.get_navigation_options()
    )
    
    # Display the page content
    if page == "Dashboard":
        display_dashboard()
    elif page == "Report Templates":
        reports.manage_report_templates()
    elif page == "Assign Reports":
        reports.assign_reports()
    elif page == "My Reports":
        reports.view_my_reports()
    elif page == "Submit Report":
        reports.submit_report()
    elif page == "Report Status":
        reports.view_report_status()
    elif page == "Organizations":
        organizations.manage_organizations()
    elif page == "Users":
        auth.manage_users()
    else:
        st.warning("Page not found")

def display_dashboard():
    st.title("Vinatex Report Portal Dashboard")
    
    # Display different dashboards based on user role
    if st.session_state.user_role == "admin":
        admin_dashboard()
    elif st.session_state.user_role == "department":
        department_dashboard()
    elif st.session_state.user_role == "unit":
        unit_dashboard()

def admin_dashboard():
    st.subheader("System Overview")
    
    # Create columns for metrics
    col1, col2, col3, col4 = st.columns(4)
    
    # Fetch statistics from database
    total_reports = db.get_total_reports()
    pending_reports = db.get_reports_by_status("pending")
    completed_reports = db.get_reports_by_status("completed")
    total_users = db.get_total_users()
    
    # Display metrics
    col1.metric("Total Report Templates", total_reports["templates"])
    col2.metric("Assigned Reports", total_reports["assigned"])
    col3.metric("Completed Reports", completed_reports)
    col4.metric("Pending Reports", pending_reports)
    
    # Create columns for charts
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.subheader("Report Submission Status")
        status_data = db.get_report_status_data()
        if status_data is not None and not status_data.empty:
            fig = px.pie(
                status_data, 
                values='count', 
                names='status', 
                color='status',
                color_discrete_map={
                    'completed': '#0066b2',
                    'pending': '#fcba03',
                    'overdue': '#fc0303'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No report status data available")
    
    with chart_col2:
        st.subheader("Reports by Organization")
        org_data = db.get_report_by_organization()
        if org_data is not None and not org_data.empty:
            fig = px.bar(
                org_data, 
                x='organization', 
                y='count',
                color='status',
                color_discrete_map={
                    'completed': '#0066b2',
                    'pending': '#fcba03',
                    'overdue': '#fc0303'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No organization report data available")
    
    # Recent activity
    st.subheader("Recent Activity")
    recent_activity = db.get_recent_activity()
    if recent_activity is not None and not recent_activity.empty:
        st.dataframe(recent_activity, use_container_width=True)
    else:
        st.info("No recent activity found")

def department_dashboard():
    st.subheader("Department Overview")
    
    # Create columns for metrics
    col1, col2, col3 = st.columns(3)
    
    # Fetch statistics from database for this department
    dept_id = st.session_state.user_org_id
    dept_reports = db.get_department_reports(dept_id)
    pending_reports = db.get_department_reports_by_status(dept_id, "pending")
    completed_reports = db.get_department_reports_by_status(dept_id, "completed")
    
    # Display metrics
    col1.metric("Assigned Reports", dept_reports)
    col2.metric("Completed Reports", completed_reports)
    col3.metric("Pending Reports", pending_reports)
    
    # Report submission status chart
    st.subheader("Report Submission Status")
    status_data = db.get_department_report_status(dept_id)
    if status_data is not None and not status_data.empty:
        fig = px.pie(
            status_data, 
            values='count', 
            names='status', 
            color='status',
            color_discrete_map={
                'completed': '#0066b2',
                'pending': '#fcba03',
                'overdue': '#fc0303'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No report status data available")
    
    # Recent submissions
    st.subheader("Recent Submissions")
    recent_submissions = db.get_department_recent_submissions(dept_id)
    if recent_submissions is not None and not recent_submissions.empty:
        st.dataframe(recent_submissions, use_container_width=True)
    else:
        st.info("No recent submissions found")

def unit_dashboard():
    st.subheader("My Reports Overview")
    
    # Create columns for metrics
    col1, col2, col3 = st.columns(3)
    
    # Fetch statistics from database for this unit
    unit_id = st.session_state.user_org_id
    assigned_reports = db.get_unit_assigned_reports(unit_id)
    completed_reports = db.get_unit_reports_by_status(unit_id, "completed")
    pending_reports = db.get_unit_reports_by_status(unit_id, "pending")
    
    # Display metrics
    col1.metric("Assigned Reports", assigned_reports)
    col2.metric("Completed Reports", completed_reports)
    col3.metric("Pending Reports", pending_reports)
    
    # Report due dates
    st.subheader("Upcoming Report Due Dates")
    upcoming_reports = db.get_unit_upcoming_reports(unit_id)
    if upcoming_reports is not None and not upcoming_reports.empty:
        st.dataframe(upcoming_reports, use_container_width=True)
    else:
        st.info("No upcoming reports found")
    
    # Action needed reports
    st.subheader("Reports Requiring Action")
    action_needed = db.get_unit_action_needed_reports(unit_id)
    if action_needed is not None and not action_needed.empty:
        for _, report in action_needed.iterrows():
            with st.expander(f"{report['report_name']} - Due: {report['due_date']}"):
                st.write(f"**Description:** {report['description']}")
                st.write(f"**Status:** {report['status']}")
                
                # Add submission button
                if st.button(f"Submit Report", key=f"submit_{report['id']}"):
                    st.session_state.current_report = report['id']
                    st.session_state.current_report_name = report['report_name']
                    st.rerun()
    else:
        st.info("No reports require immediate action")

if __name__ == "__main__":
    # Ensure database connection is established
    db.initialize_connection()
