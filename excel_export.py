import pandas as pd
import json
import os
from io import BytesIO
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
import streamlit as st
import database as db
import excel_utils

def create_report_excel(template_id, assigned_report_id, submission_data):
    """
    Create an Excel file for a report submission with multiple sheets based on template configuration.
    
    Args:
        template_id: ID of the report template
        assigned_report_id: ID of the assigned report
        submission_data: JSON string of submitted data
        
    Returns:
        BytesIO object containing the Excel file
    """
    # If submission_data is a string, parse it as JSON
    if isinstance(submission_data, str):
        data = json.loads(submission_data)
    else:
        data = submission_data
    
    # Create the Excel file based on the template sheet structure
    excel_file = excel_utils.create_excel_from_template(template_id, data)
    
    return excel_file

def save_excel_to_sharepoint(excel_bytes, template_name, organization_name, assigned_report_id):
    """
    Save Excel file to SharePoint (mock implementation)
    
    Args:
        excel_bytes: BytesIO object containing the Excel file
        template_name: Name of the report template
        organization_name: Name of the organization
        assigned_report_id: ID of the assigned report
        
    Returns:
        URL to the saved file in SharePoint
    """
    # Get SharePoint settings
    settings = load_sharepoint_settings()
    
    # Generate SharePoint URL using the excel_utils function
    sharepoint_url = excel_utils.save_to_sharepoint(excel_bytes, template_name, organization_name)
    
    # Update the report submission with the SharePoint URL
    db.execute_query(
        "UPDATE report_submissions SET sharepoint_url = %s WHERE assigned_report_id = %s",
        (sharepoint_url, assigned_report_id),
        fetch=False
    )
    
    return sharepoint_url

def load_sharepoint_settings():
    """Load SharePoint settings from the database"""
    settings_data = db.get_settings("sharepoint")
    
    if settings_data:
        return json.loads(settings_data)
    else:
        # Default settings if none are saved
        return {
            "sharepoint_url": "https://vinatex.sharepoint.com/sites/reports",
            "document_library": "Documents/Reports",
            "use_org_folders": True
        }

def export_report_to_excel(assigned_report_id):
    """
    Export a report to Excel and save to SharePoint
    
    Args:
        assigned_report_id: ID of the assigned report
        
    Returns:
        URL to the saved file in SharePoint
    """
    # Get the report details and submission
    report_query = """
    SELECT ar.id, rt.id as template_id, rt.name as template_name, 
           o.name as organization_name, rs.data as submission_data
    FROM assigned_reports ar
    JOIN report_templates rt ON ar.template_id = rt.id
    JOIN organizations o ON ar.organization_id = o.id
    LEFT JOIN report_submissions rs ON rs.assigned_report_id = ar.id
    WHERE ar.id = %s
    ORDER BY rs.submitted_at DESC
    LIMIT 1
    """
    result = db.execute_query(report_query, (assigned_report_id,))
    
    if result is None or result.empty:
        raise ValueError("Không tìm thấy báo cáo")
    
    report = result.iloc[0]
    
    # Create Excel file
    excel_bytes = create_report_excel(
        report['template_id'], 
        assigned_report_id, 
        report['submission_data']
    )
    
    # Save to SharePoint
    sharepoint_url = save_excel_to_sharepoint(
        excel_bytes,
        report['template_name'],
        report['organization_name'],
        assigned_report_id
    )
    
    return sharepoint_url

def download_report_excel(assigned_report_id):
    """
    Generate Excel file for download
    
    Args:
        assigned_report_id: ID of the assigned report
        
    Returns:
        BytesIO object containing the Excel file and filename
    """
    # Get the report details and submission
    report_query = """
    SELECT ar.id, rt.id as template_id, rt.name as template_name, 
           o.name as organization_name, rs.data as submission_data
    FROM assigned_reports ar
    JOIN report_templates rt ON ar.template_id = rt.id
    JOIN organizations o ON ar.organization_id = o.id
    LEFT JOIN report_submissions rs ON rs.assigned_report_id = ar.id
    WHERE ar.id = %s
    ORDER BY rs.submitted_at DESC
    LIMIT 1
    """
    result = db.execute_query(report_query, (assigned_report_id,))
    
    if result is None or result.empty:
        raise ValueError("Không tìm thấy báo cáo")
    
    report = result.iloc[0]
    
    # Create Excel file
    excel_bytes = create_report_excel(
        report['template_id'], 
        assigned_report_id, 
        report['submission_data']
    )
    
    # Generate filename
    filename = f"{report['template_name']}_{report['organization_name']}.xlsx"
    filename = filename.replace(" ", "_")
    
    return excel_bytes, filename