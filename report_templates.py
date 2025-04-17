import streamlit as st
import pandas as pd
import json
import os
import database as db
from datetime import datetime
import excel_handler

def manage_report_templates():
    st.title("Quản lý mẫu báo cáo")
    
    # Create tabs for template management
    tab1, tab2 = st.tabs(["Danh sách mẫu báo cáo", "Tạo mẫu báo cáo mới"])
    
    with tab1:
        list_report_templates()
    
    with tab2:
        create_report_template()

def list_report_templates():
    """Display a list of all report templates with edit and delete options."""
    st.subheader("Danh sách mẫu báo cáo hiện có")
    
    # Get all report templates from database
    templates = db.get_report_templates()
    
    if templates is None or templates.empty:
        st.info("Chưa có mẫu báo cáo nào. Hãy tạo mẫu báo cáo mới.")
        return
    
    # Display each template as an expandable card
    for _, template in templates.iterrows():
        with st.expander(f"{template['name']} - {template['department']}"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Mô tả:** {template['description']}")
                st.write("**Các trường dữ liệu:**")
                
                # Display fields with bullet points
                fields = json.loads(template['fields'])
                for field in fields:
                    st.write(f"• {field}")
                
                # Display sheet structure if available
                sheet_structure = db.get_report_template_sheet_structure(template['id'])
                if sheet_structure:
                    st.write("**Cấu trúc sheet Excel:**")
                    sheets = json.loads(sheet_structure)
                    for sheet_name, sheet_fields in sheets.items():
                        st.write(f"• Sheet '{sheet_name}': {', '.join(sheet_fields)}")
                else:
                    st.write("**Cấu trúc sheet Excel:** Chưa được cấu hình")
            
            with col2:
                # Edit button
                if st.button("Chỉnh sửa", key=f"edit_{template['id']}"):
                    st.session_state.editing_template = template
                    st.rerun()
                
                # Configure Excel sheets button
                if st.button("Cấu hình Excel", key=f"excel_{template['id']}"):
                    st.session_state.configuring_excel = template
                    st.rerun()
                
                # Delete button
                if st.button("Xóa", key=f"delete_{template['id']}"):
                    if db.delete_report_template(template['id']):
                        st.success("Xóa mẫu báo cáo thành công!")
                        st.rerun()
                    else:
                        st.error("Không thể xóa mẫu báo cáo.")
    
    # If a template is selected for editing, show the edit form
    if 'editing_template' in st.session_state:
        edit_report_template(st.session_state.editing_template)
    
    # If a template is selected for Excel configuration, show the config form
    if 'configuring_excel' in st.session_state:
        configure_excel_sheets(st.session_state.configuring_excel)

def create_report_template():
    """Form to create a new report template."""
    st.subheader("Tạo mẫu báo cáo mới")
    
    # Get list of departments for dropdown
    departments = db.get_organization_departments()
    if departments is None or departments.empty:
        st.error("Không thể tải danh sách phòng ban. Vui lòng thử lại sau.")
        return
    
    department_options = {row['name']: row['id'] for _, row in departments.iterrows()}
    
    # Create the form
    with st.form("new_template_form"):
        template_name = st.text_input("Tên mẫu báo cáo", placeholder="Nhập tên mẫu báo cáo")
        description = st.text_area("Mô tả", placeholder="Mô tả chi tiết về mẫu báo cáo")
        
        # Department selection
        department = st.selectbox("Phòng ban quản lý", options=list(department_options.keys()))
        
        # Fields section
        st.subheader("Các trường dữ liệu trong báo cáo")
        st.write("Nhập mỗi trường dữ liệu trên một dòng")
        
        fields_text = st.text_area("Trường dữ liệu", height=200, placeholder="Ví dụ:\nDoanh thu (VND)\nChi phí (VND)\nLợi nhuận (VND)")
        
        # Submit button
        submitted = st.form_submit_button("Tạo mẫu báo cáo")
        
        if submitted:
            if not template_name or not description or not fields_text:
                st.error("Vui lòng điền đầy đủ thông tin cho mẫu báo cáo.")
                return
            
            # Process fields
            fields = [field.strip() for field in fields_text.strip().split('\n') if field.strip()]
            
            if len(fields) == 0:
                st.error("Vui lòng nhập ít nhất một trường dữ liệu.")
                return
            
            # Save to database
            department_id = department_options[department]
            if db.add_report_template(template_name, description, json.dumps(fields), department_id):
                st.success("Đã tạo mẫu báo cáo thành công!")
                # Create a default Excel sheet structure
                template_id = db.execute_query(
                    "SELECT id FROM report_templates WHERE name = %s ORDER BY created_at DESC LIMIT 1",
                    (template_name,)
                )
                if template_id is not None and not template_id.empty:
                    template_id = template_id.iloc[0]['id']
                    # Create a default sheet structure with all fields in one sheet
                    sheet_structure = {"Sheet1": fields}
                    db.update_report_template_sheet_structure(template_id, json.dumps(sheet_structure))
            else:
                st.error("Không thể tạo mẫu báo cáo. Vui lòng thử lại.")

def edit_report_template(template):
    """Form to edit an existing report template."""
    st.subheader(f"Chỉnh sửa mẫu báo cáo: {template['name']}")
    
    # Get list of departments for dropdown
    departments = db.get_organization_departments()
    if departments is None or departments.empty:
        st.error("Không thể tải danh sách phòng ban. Vui lòng thử lại sau.")
        return
    
    department_options = {row['name']: row['id'] for _, row in departments.iterrows()}
    
    # Find current department name
    current_dept_id = template['department_id']
    current_dept_name = next((name for name, id in department_options.items() if id == current_dept_id), list(department_options.keys())[0])
    
    # Parse existing fields
    current_fields = json.loads(template['fields'])
    fields_text = '\n'.join(current_fields)
    
    # Create the form
    with st.form("edit_template_form"):
        template_name = st.text_input("Tên mẫu báo cáo", value=template['name'])
        description = st.text_area("Mô tả", value=template['description'])
        
        # Department selection
        department = st.selectbox("Phòng ban quản lý", options=list(department_options.keys()), index=list(department_options.keys()).index(current_dept_name))
        
        # Fields section
        st.subheader("Các trường dữ liệu trong báo cáo")
        st.write("Nhập mỗi trường dữ liệu trên một dòng")
        
        new_fields_text = st.text_area("Trường dữ liệu", height=200, value=fields_text)
        
        # Cancel button and submit button in columns
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Hủy"):
                del st.session_state.editing_template
                st.rerun()
        
        with col2:
            submitted = st.form_submit_button("Cập nhật")
        
        if submitted:
            if not template_name or not description or not new_fields_text:
                st.error("Vui lòng điền đầy đủ thông tin cho mẫu báo cáo.")
                return
            
            # Process fields
            new_fields = [field.strip() for field in new_fields_text.strip().split('\n') if field.strip()]
            
            if len(new_fields) == 0:
                st.error("Vui lòng nhập ít nhất một trường dữ liệu.")
                return
            
            # Save to database
            department_id = department_options[department]
            if db.update_report_template(template['id'], template_name, description, json.dumps(new_fields), department_id):
                st.success("Đã cập nhật mẫu báo cáo thành công!")
                del st.session_state.editing_template
                st.rerun()
            else:
                st.error("Không thể cập nhật mẫu báo cáo. Vui lòng thử lại.")

def configure_excel_sheets(template):
    """Configure Excel sheet structure for a report template."""
    st.subheader(f"Cấu hình cấu trúc Excel cho: {template['name']}")
    
    # Parse fields from template
    fields = json.loads(template['fields'])
    
    # Get current sheet structure or create a default one
    current_structure = db.get_report_template_sheet_structure(template['id'])
    if current_structure:
        sheets = json.loads(current_structure)
    else:
        # Default structure with all fields in Sheet1
        sheets = {"Sheet1": fields}
    
    # Display the current structure
    st.write("**Cấu trúc hiện tại:**")
    for sheet_name, sheet_fields in sheets.items():
        st.write(f"• Sheet '{sheet_name}': {', '.join(sheet_fields)}")
    
    st.markdown("---")
    st.write("**Cấu hình lại cấu trúc Excel:**")
    st.write("Mỗi báo cáo có thể được chia thành nhiều sheet, mỗi sheet chứa các trường dữ liệu khác nhau.")
    
    # Count the number of sheets in the current structure
    num_sheets = len(sheets)
    
    # Let user add or remove sheets
    new_num_sheets = st.number_input("Số lượng sheet", min_value=1, value=num_sheets, step=1)
    
    # If number of sheets has changed, adjust the structure
    if new_num_sheets != num_sheets:
        if new_num_sheets > num_sheets:
            # Add new sheets
            for i in range(num_sheets + 1, new_num_sheets + 1):
                sheets[f"Sheet{i}"] = []
        else:
            # Remove excess sheets (starting from the highest number)
            sheet_names = sorted(list(sheets.keys()))
            for i in range(num_sheets - new_num_sheets):
                if sheet_names:
                    del sheets[sheet_names.pop()]
    
    # Create form for configuring each sheet
    with st.form("sheet_config_form"):
        new_structure = {}
        
        for i, (sheet_name, sheet_fields) in enumerate(sheets.items()):
            st.subheader(f"Sheet {i+1}")
            
            new_sheet_name = st.text_input(f"Tên sheet {i+1}", value=sheet_name, key=f"sheet_name_{i}")
            
            # Multiselect for fields
            selected_fields = st.multiselect(
                f"Các trường dữ liệu cho sheet {i+1}",
                options=fields,
                default=sheet_fields,
                key=f"sheet_fields_{i}"
            )
            
            new_structure[new_sheet_name] = selected_fields
        
        # Cancel and submit buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Hủy"):
                del st.session_state.configuring_excel
                st.rerun()
        
        with col2:
            submitted = st.form_submit_button("Lưu cấu hình")
        
        if submitted:
            # Validate that each field is included in at least one sheet
            all_assigned_fields = []
            for sheet_fields in new_structure.values():
                all_assigned_fields.extend(sheet_fields)
            
            missing_fields = set(fields) - set(all_assigned_fields)
            if missing_fields:
                st.error(f"Các trường sau chưa được đưa vào bất kỳ sheet nào: {', '.join(missing_fields)}")
                return
            
            # Save the new structure
            if db.update_report_template_sheet_structure(template['id'], json.dumps(new_structure)):
                st.success("Đã cập nhật cấu trúc Excel thành công!")
                del st.session_state.configuring_excel
                st.rerun()
            else:
                st.error("Không thể cập nhật cấu trúc Excel. Vui lòng thử lại.")