import os
import psycopg2
import pandas as pd
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import streamlit as st

# Database connection parameters
db_params = {
    'host': os.getenv('PGHOST', 'localhost'),
    'database': os.getenv('PGDATABASE', 'vinatex_reports'),
    'user': os.getenv('PGUSER', 'postgres'),
    'password': os.getenv('PGPASSWORD', 'postgres'),
    'port': os.getenv('PGPORT', '5432')
}

@st.cache_resource
def initialize_connection():
    """Establish a connection to the PostgreSQL database and return the connection object."""
    try:
        conn = psycopg2.connect(**db_params)
        return conn
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

def get_connection():
    """Get a database connection from the cached resource."""
    return initialize_connection()

def execute_query(query, params=None, fetch=True):
    """Execute a SQL query and return the results."""
    conn = get_connection()
    if conn is None:
        return None
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            
            if fetch:
                results = cursor.fetchall()
                return pd.DataFrame(results) if results else pd.DataFrame()
            else:
                conn.commit()
                return True
    except Exception as e:
        st.error(f"Query execution error: {e}")
        conn.rollback()
        return None

# User Authentication Functions
def validate_user(username, password):
    """Validate user credentials and return user information if valid."""
    query = """
    SELECT u.id, u.username, u.role, u.organization_id
    FROM users u
    WHERE u.username = %s AND u.password = %s
    """
    result = execute_query(query, (username, password))
    
    if result is not None and not result.empty:
        return result.iloc[0].to_dict()
    return None

def get_users():
    """Get all users."""
    query = """
    SELECT u.id, u.username, u.role, o.name as organization
    FROM users u
    LEFT JOIN organizations o ON u.organization_id = o.id
    ORDER BY u.username
    """
    return execute_query(query)

def add_user(username, password, role, organization_id):
    """Add a new user to the system."""
    query = """
    INSERT INTO users (username, password, role, organization_id)
    VALUES (%s, %s, %s, %s)
    RETURNING id
    """
    result = execute_query(query, (username, password, role, organization_id), fetch=True)
    return result is not None

def update_user(user_id, username, password, role, organization_id):
    """Update an existing user."""
    # If password is empty, don't update it
    if password:
        query = """
        UPDATE users
        SET username = %s, password = %s, role = %s, organization_id = %s
        WHERE id = %s
        """
        params = (username, password, role, organization_id, user_id)
    else:
        query = """
        UPDATE users
        SET username = %s, role = %s, organization_id = %s
        WHERE id = %s
        """
        params = (username, role, organization_id, user_id)
    
    return execute_query(query, params, fetch=False)

def delete_user(user_id):
    """Delete a user by ID."""
    query = "DELETE FROM users WHERE id = %s"
    return execute_query(query, (user_id,), fetch=False)

# Organization Management Functions
def get_organizations():
    """Get all organizations."""
    query = """
    SELECT id, name, type, parent_id
    FROM organizations
    ORDER BY name
    """
    return execute_query(query)

def add_organization(name, org_type, parent_id=None):
    """Add a new organization."""
    query = """
    INSERT INTO organizations (name, type, parent_id)
    VALUES (%s, %s, %s)
    RETURNING id
    """
    result = execute_query(query, (name, org_type, parent_id), fetch=True)
    return result is not None

def update_organization(org_id, name, org_type, parent_id=None):
    """Update an existing organization."""
    query = """
    UPDATE organizations
    SET name = %s, type = %s, parent_id = %s
    WHERE id = %s
    """
    return execute_query(query, (name, org_type, parent_id, org_id), fetch=False)

def delete_organization(org_id):
    """Delete an organization by ID."""
    query = "DELETE FROM organizations WHERE id = %s"
    return execute_query(query, (org_id,), fetch=False)

def get_organization_units():
    """Get all member units."""
    query = """
    SELECT id, name
    FROM organizations
    WHERE type = 'unit'
    ORDER BY name
    """
    return execute_query(query)

def get_organization_departments():
    """Get all functional departments."""
    query = """
    SELECT id, name
    FROM organizations
    WHERE type = 'department'
    ORDER BY name
    """
    return execute_query(query)

# Report Template Management Functions
def get_report_templates():
    """Get all report templates."""
    query = """
    SELECT rt.id, rt.name, rt.description, rt.fields, rt.created_at, rt.updated_at,
           o.name as department
    FROM report_templates rt
    LEFT JOIN organizations o ON rt.department_id = o.id
    ORDER BY rt.name
    """
    return execute_query(query)

def get_report_template(template_id):
    """Get a specific report template by ID."""
    query = """
    SELECT id, name, description, fields, department_id
    FROM report_templates
    WHERE id = %s
    """
    result = execute_query(query, (template_id,))
    if result is not None and not result.empty:
        return result.iloc[0].to_dict()
    return None

def add_report_template(name, description, fields, department_id):
    """Add a new report template."""
    query = """
    INSERT INTO report_templates (name, description, fields, department_id)
    VALUES (%s, %s, %s, %s)
    RETURNING id
    """
    result = execute_query(query, (name, description, fields, department_id), fetch=True)
    return result is not None

def update_report_template(template_id, name, description, fields, department_id):
    """Update an existing report template."""
    query = """
    UPDATE report_templates
    SET name = %s, description = %s, fields = %s, department_id = %s, updated_at = NOW()
    WHERE id = %s
    """
    return execute_query(query, (name, description, fields, department_id, template_id), fetch=False)

def delete_report_template(template_id):
    """Delete a report template by ID."""
    query = "DELETE FROM report_templates WHERE id = %s"
    return execute_query(query, (template_id,), fetch=False)

# Report Assignment Functions
def assign_report(template_id, organization_id, due_date):
    """Assign a report to an organization."""
    query = """
    INSERT INTO assigned_reports (template_id, organization_id, due_date, status)
    VALUES (%s, %s, %s, 'pending')
    RETURNING id
    """
    result = execute_query(query, (template_id, organization_id, due_date), fetch=True)
    return result is not None

def get_assigned_reports():
    """Get all assigned reports."""
    query = """
    SELECT ar.id, rt.name as report_name, o.name as organization, ar.due_date, ar.status
    FROM assigned_reports ar
    JOIN report_templates rt ON ar.template_id = rt.id
    JOIN organizations o ON ar.organization_id = o.id
    ORDER BY ar.due_date
    """
    return execute_query(query)

def get_organization_assigned_reports(organization_id):
    """Get reports assigned to a specific organization."""
    query = """
    SELECT ar.id, rt.name as report_name, rt.description, ar.due_date, ar.status,
           rt.fields, ar.template_id
    FROM assigned_reports ar
    JOIN report_templates rt ON ar.template_id = rt.id
    WHERE ar.organization_id = %s
    ORDER BY ar.due_date
    """
    return execute_query(query, (organization_id,))

def update_report_status(report_id, status):
    """Update the status of an assigned report."""
    query = """
    UPDATE assigned_reports
    SET status = %s, updated_at = NOW()
    WHERE id = %s
    """
    return execute_query(query, (status, report_id), fetch=False)

def submit_report_data(assigned_report_id, data):
    """Submit data for an assigned report."""
    query = """
    INSERT INTO report_submissions (assigned_report_id, data, submitted_at)
    VALUES (%s, %s, NOW())
    RETURNING id
    """
    result = execute_query(query, (assigned_report_id, data), fetch=True)
    
    if result is not None:
        # Update the status of the assigned report
        update_report_status(assigned_report_id, 'completed')
        return True
    return False

def get_report_submission(assigned_report_id):
    """Get the submission data for an assigned report."""
    query = """
    SELECT rs.id, rs.data, rs.submitted_at
    FROM report_submissions rs
    WHERE rs.assigned_report_id = %s
    ORDER BY rs.submitted_at DESC
    LIMIT 1
    """
    result = execute_query(query, (assigned_report_id,))
    if result is not None and not result.empty:
        return result.iloc[0].to_dict()
    return None

# Dashboard Statistics Functions
def get_total_reports():
    """Get total reports statistics."""
    query_templates = "SELECT COUNT(*) as templates FROM report_templates"
    query_assigned = "SELECT COUNT(*) as assigned FROM assigned_reports"
    
    templates_result = execute_query(query_templates)
    assigned_result = execute_query(query_assigned)
    
    return {
        'templates': templates_result.iloc[0]['templates'] if not templates_result.empty else 0,
        'assigned': assigned_result.iloc[0]['assigned'] if not assigned_result.empty else 0
    }

def get_reports_by_status(status):
    """Get count of reports by status."""
    query = "SELECT COUNT(*) as count FROM assigned_reports WHERE status = %s"
    result = execute_query(query, (status,))
    return result.iloc[0]['count'] if not result.empty else 0

def get_total_users():
    """Get total number of users."""
    query = "SELECT COUNT(*) as count FROM users"
    result = execute_query(query)
    return result.iloc[0]['count'] if not result.empty else 0

def get_report_status_data():
    """Get report status data for charts."""
    query = """
    SELECT status, COUNT(*) as count
    FROM assigned_reports
    GROUP BY status
    """
    return execute_query(query)

def get_report_by_organization():
    """Get report counts by organization."""
    query = """
    SELECT o.name as organization, ar.status, COUNT(*) as count
    FROM assigned_reports ar
    JOIN organizations o ON ar.organization_id = o.id
    GROUP BY o.name, ar.status
    ORDER BY count DESC
    """
    return execute_query(query)

def get_recent_activity():
    """Get recent activity for the dashboard."""
    query = """
    SELECT o.name as organization, rt.name as report, ar.status, ar.updated_at as activity_date
    FROM assigned_reports ar
    JOIN organizations o ON ar.organization_id = o.id
    JOIN report_templates rt ON ar.template_id = rt.id
    ORDER BY ar.updated_at DESC
    LIMIT 10
    """
    return execute_query(query)

# Department Dashboard Functions
def get_department_reports(department_id):
    """Get count of reports for a department."""
    query = """
    SELECT COUNT(*) as count
    FROM assigned_reports ar
    JOIN report_templates rt ON ar.template_id = rt.id
    WHERE rt.department_id = %s
    """
    result = execute_query(query, (department_id,))
    return result.iloc[0]['count'] if not result.empty else 0

def get_department_reports_by_status(department_id, status):
    """Get count of department reports by status."""
    query = """
    SELECT COUNT(*) as count
    FROM assigned_reports ar
    JOIN report_templates rt ON ar.template_id = rt.id
    WHERE rt.department_id = %s AND ar.status = %s
    """
    result = execute_query(query, (department_id, status))
    return result.iloc[0]['count'] if not result.empty else 0

def get_department_report_status(department_id):
    """Get report status data for a department."""
    query = """
    SELECT ar.status, COUNT(*) as count
    FROM assigned_reports ar
    JOIN report_templates rt ON ar.template_id = rt.id
    WHERE rt.department_id = %s
    GROUP BY ar.status
    """
    return execute_query(query, (department_id,))

def get_department_recent_submissions(department_id):
    """Get recent submissions for a department."""
    query = """
    SELECT o.name as organization, rt.name as report, rs.submitted_at
    FROM report_submissions rs
    JOIN assigned_reports ar ON rs.assigned_report_id = ar.id
    JOIN organizations o ON ar.organization_id = o.id
    JOIN report_templates rt ON ar.template_id = rt.id
    WHERE rt.department_id = %s
    ORDER BY rs.submitted_at DESC
    LIMIT 10
    """
    return execute_query(query, (department_id,))

# Unit Dashboard Functions
def get_unit_assigned_reports(unit_id):
    """Get count of reports assigned to a unit."""
    query = """
    SELECT COUNT(*) as count
    FROM assigned_reports
    WHERE organization_id = %s
    """
    result = execute_query(query, (unit_id,))
    return result.iloc[0]['count'] if not result.empty else 0

def get_unit_reports_by_status(unit_id, status):
    """Get count of unit reports by status."""
    query = """
    SELECT COUNT(*) as count
    FROM assigned_reports
    WHERE organization_id = %s AND status = %s
    """
    result = execute_query(query, (unit_id, status))
    return result.iloc[0]['count'] if not result.empty else 0

def get_unit_upcoming_reports(unit_id):
    """Get upcoming reports for a unit."""
    query = """
    SELECT ar.id, rt.name as report_name, ar.due_date, ar.status
    FROM assigned_reports ar
    JOIN report_templates rt ON ar.template_id = rt.id
    WHERE ar.organization_id = %s AND ar.due_date >= CURRENT_DATE
    ORDER BY ar.due_date ASC
    LIMIT 5
    """
    return execute_query(query, (unit_id,))

def get_unit_action_needed_reports(unit_id):
    """Get reports that need action from a unit."""
    query = """
    SELECT ar.id, rt.name as report_name, rt.description, ar.due_date, ar.status
    FROM assigned_reports ar
    JOIN report_templates rt ON ar.template_id = rt.id
    WHERE ar.organization_id = %s AND ar.status = 'pending'
    ORDER BY 
        CASE WHEN ar.due_date < CURRENT_DATE THEN 0 ELSE 1 END,
        ar.due_date ASC
    """
    return execute_query(query, (unit_id,))
