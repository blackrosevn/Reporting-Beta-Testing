import json
import os
import pandas as pd
from io import BytesIO
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
import streamlit as st
import database as db

def create_excel_from_template(template_id, data):
    """
    Create an Excel file with multiple sheets based on the template's sheet structure.
    
    Args:
        template_id: The ID of the report template
        data: JSON data of field values
        
    Returns:
        BytesIO object containing the Excel file
    """
    # Get the template sheet structure
    sheet_structure = db.get_report_template_sheet_structure(template_id)
    if not sheet_structure:
        # Fallback to the old single-sheet structure
        template = db.get_report_template(template_id)
        if not template:
            raise ValueError("Mẫu báo cáo không tồn tại")
        
        fields = json.loads(template['fields'])
        sheet_structure = {
            "Báo cáo": {
                "fields": fields
            }
        }
    else:
        sheet_structure = json.loads(sheet_structure)
    
    # Create a new Excel workbook
    wb = openpyxl.Workbook()
    
    # Remove the default sheet
    default_sheet = wb.active
    wb.remove(default_sheet)
    
    # Define styles
    header_font = Font(bold=True, size=12)
    header_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    border = Border(
        left=Side(style='thin'), 
        right=Side(style='thin'), 
        top=Side(style='thin'), 
        bottom=Side(style='thin')
    )
    
    # Process each sheet in the structure
    for sheet_name, sheet_config in sheet_structure.items():
        # Create a new sheet
        ws = wb.create_sheet(title=sheet_name)
        
        # Add headers
        headers = ['STT'] + [field['label'] for field in sheet_config['fields']]
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        
        # Auto-adjust column widths based on header length
        for col_idx, header in enumerate(headers, 1):
            col_letter = get_column_letter(col_idx)
            column_width = len(header) * 1.5  # Adjust multiplier as needed
            ws.column_dimensions[col_letter].width = max(10, min(50, column_width))
        
        # Add data rows
        row_idx = 2
        for idx, item in enumerate(data.get(sheet_name, []), 1):
            ws.cell(row=row_idx, column=1, value=idx).border = border  # STT column
            
            for col_idx, field in enumerate(sheet_config['fields'], 2):
                field_id = field['id']
                value = item.get(field_id, '')
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                cell.border = border
                
                # Apply specific formatting based on field type if needed
                if field.get('type') == 'number':
                    cell.number_format = '#,##0.00'
                elif field.get('type') == 'date':
                    cell.number_format = 'DD/MM/YYYY'
                
            row_idx += 1
    
    # Save to BytesIO
    excel_bytes = BytesIO()
    wb.save(excel_bytes)
    excel_bytes.seek(0)
    
    return excel_bytes

def parse_excel_submission(uploaded_file, template_id):
    """
    Parse an uploaded Excel file that was created from a template.
    
    Args:
        uploaded_file: The uploaded Excel file
        template_id: The ID of the report template
        
    Returns:
        Dictionary of field values
    """
    # Get the template sheet structure
    sheet_structure = db.get_report_template_sheet_structure(template_id)
    if not sheet_structure:
        # Fallback to the old single-sheet structure
        template = db.get_report_template(template_id)
        if not template:
            raise ValueError("Mẫu báo cáo không tồn tại")
        
        fields = json.loads(template['fields'])
        sheet_structure = {
            "Báo cáo": {
                "fields": fields
            }
        }
    else:
        sheet_structure = json.loads(sheet_structure)
    
    # Load the Excel workbook
    wb = openpyxl.load_workbook(uploaded_file)
    
    # Initialize the result dictionary
    result = {}
    
    # Process each sheet in the structure
    for sheet_name, sheet_config in sheet_structure.items():
        if sheet_name not in wb.sheetnames:
            st.warning(f"Sheet '{sheet_name}' không tồn tại trong file Excel.")
            continue
        
        ws = wb[sheet_name]
        
        # Skip the header row and get data
        data_rows = list(ws.iter_rows(min_row=2, values_only=True))
        
        # Initialize sheet data
        sheet_data = []
        
        # Get field IDs from the structure
        field_ids = [field['id'] for field in sheet_config['fields']]
        
        # Process each data row
        for row in data_rows:
            if all(cell is None or cell == '' for cell in row[1:]):  # Skip empty rows (excluding STT column)
                continue
                
            row_data = {}
            for idx, field_id in enumerate(field_ids):
                # Excel data starts at column 2 (after STT column)
                cell_value = row[idx+1] if idx+1 < len(row) else None
                row_data[field_id] = str(cell_value) if cell_value is not None else ''
            
            sheet_data.append(row_data)
        
        result[sheet_name] = sheet_data
    
    return result

def create_excel_template(template_id):
    """
    Create an empty Excel template based on a report template.
    
    Args:
        template_id: The ID of the report template
        
    Returns:
        BytesIO object containing the Excel template
    """
    # Get the template sheet structure
    sheet_structure = db.get_report_template_sheet_structure(template_id)
    if not sheet_structure:
        # Fallback to the old single-sheet structure
        template = db.get_report_template(template_id)
        if not template:
            raise ValueError("Mẫu báo cáo không tồn tại")
        
        fields = json.loads(template['fields'])
        sheet_structure = {
            "Báo cáo": {
                "fields": fields
            }
        }
    else:
        sheet_structure = json.loads(sheet_structure)
    
    # Create a new Excel workbook
    wb = openpyxl.Workbook()
    
    # Remove the default sheet
    default_sheet = wb.active
    wb.remove(default_sheet)
    
    # Define styles
    header_font = Font(bold=True, size=12)
    header_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    border = Border(
        left=Side(style='thin'), 
        right=Side(style='thin'), 
        top=Side(style='thin'), 
        bottom=Side(style='thin')
    )
    
    # Process each sheet in the structure
    for sheet_name, sheet_config in sheet_structure.items():
        # Create a new sheet
        ws = wb.create_sheet(title=sheet_name)
        
        # Add headers
        headers = ['STT'] + [field['label'] for field in sheet_config['fields']]
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        
        # Auto-adjust column widths based on header length
        for col_idx, header in enumerate(headers, 1):
            col_letter = get_column_letter(col_idx)
            column_width = len(header) * 1.5  # Adjust multiplier as needed
            ws.column_dimensions[col_letter].width = max(10, min(50, column_width))
        
        # Add a few empty rows
        for row_idx in range(2, 12):
            ws.cell(row=row_idx, column=1, value=row_idx-1).border = border  # STT column
            
            for col_idx, _ in enumerate(sheet_config['fields'], 2):
                cell = ws.cell(row=row_idx, column=col_idx, value='')
                cell.border = border
    
    # Save to BytesIO
    excel_bytes = BytesIO()
    wb.save(excel_bytes)
    excel_bytes.seek(0)
    
    return excel_bytes

def save_to_sharepoint(excel_file, template_name, org_name):
    """
    Simulate saving to SharePoint - in a real application this would use
    SharePoint API to save the file to the configured location.
    
    Args:
        excel_file: The Excel file to save (BytesIO)
        template_name: The name of the report template
        org_name: The name of the organization
        
    Returns:
        String URL where the file would be saved
    """
    # Load SharePoint settings
    settings_data = db.get_settings("sharepoint")
    
    if settings_data:
        settings = json.loads(settings_data)
        base_url = settings.get("sharepoint_url", "https://vinatex.sharepoint.com/sites/reports")
        document_library = settings.get("document_library", "Documents/Reports")
        use_org_folders = settings.get("use_org_folders", True)
    else:
        # Default settings
        base_url = "https://vinatex.sharepoint.com/sites/reports"
        document_library = "Documents/Reports"
        use_org_folders = True
    
    # Format the filename
    filename = f"{template_name}_{org_name}.xlsx".replace(" ", "_")
    
    # Generate the SharePoint URL
    if use_org_folders:
        folder_path = f"{org_name}"
        sharepoint_url = f"{base_url}/{document_library}/{folder_path}/{filename}"
    else:
        sharepoint_url = f"{base_url}/{document_library}/{filename}"
    
    # In a real implementation, we would use SharePoint API to save the file
    # For now, we just return the URL where it would be saved
    
    return sharepoint_url