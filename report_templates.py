import streamlit as st
import pandas as pd
import json
import database as db

def manage_report_templates():
    """Manage report templates."""
    st.title("📋 Quản lý mẫu báo cáo")
    
    # Create tabs for managing templates and configuring sheets
    tab1, tab2 = st.tabs(["Danh sách mẫu báo cáo", "Tạo mẫu báo cáo"])
    
    with tab1:
        list_report_templates()
    
    with tab2:
        create_report_template()

def list_report_templates():
    """Display a list of all report templates with edit and delete options."""
    st.subheader("Danh sách mẫu báo cáo")
    
    # Get all report templates
    templates = db.get_report_templates()
    
    if templates is None or templates.empty:
        st.info("Chưa có mẫu báo cáo nào.")
        return
    
    # Display templates in a table
    for _, template in templates.iterrows():
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.write(f"**{template['name']}**")
                st.write(f"Phòng ban: {template['department']}")
                
            with col2:
                if st.button("Xem", key=f"view_{template['id']}"):
                    # Store template ID in session state and show view dialog
                    st.session_state.viewing_template = template.to_dict()
                    st.session_state.show_view_dialog = True
            
            with col3:
                if st.button("Sửa", key=f"edit_{template['id']}"):
                    # Store template ID in session state and show edit dialog
                    st.session_state.editing_template = template.to_dict()
                    st.session_state.show_edit_dialog = True
            
            with col4:
                if st.button("Xóa", key=f"delete_{template['id']}"):
                    # Store template ID in session state and show delete dialog
                    st.session_state.deleting_template_id = template['id']
                    st.session_state.deleting_template_name = template['name']
                    st.session_state.show_delete_dialog = True
            
            st.divider()
    
    # Handle view dialog
    if st.session_state.get('show_view_dialog', False) and st.session_state.get('viewing_template'):
        template = st.session_state.viewing_template
        
        with st.expander("Chi tiết mẫu báo cáo", expanded=True):
            st.write(f"**Tên mẫu báo cáo:** {template['name']}")
            st.write(f"**Mô tả:** {template['description']}")
            st.write(f"**Phòng ban:** {template['department']}")
            
            # Parse and display fields
            fields = json.loads(template['fields'])
            st.write("**Các trường dữ liệu:**")
            
            for field in fields:
                st.write(f"- {field['label']} ({field['id']})")
            
            # Get sheet structure if available
            sheet_structure = db.get_report_template_sheet_structure(template['id'])
            if sheet_structure:
                sheet_data = json.loads(sheet_structure)
                st.write("**Cấu trúc Excel:**")
                
                for sheet_name, sheet_config in sheet_data.items():
                    st.write(f"- Sheet: {sheet_name}")
                    st.write(f"  - Các trường: {', '.join([field['label'] for field in sheet_config['fields']])}")
            
            if st.button("Đóng", key="close_view"):
                st.session_state.show_view_dialog = False
                st.session_state.viewing_template = None
                st.rerun()
    
    # Handle edit dialog
    if st.session_state.get('show_edit_dialog', False) and st.session_state.get('editing_template'):
        edit_report_template(st.session_state.editing_template)
    
    # Handle delete dialog
    if st.session_state.get('show_delete_dialog', False):
        with st.expander("Xác nhận xóa", expanded=True):
            st.warning(f"Bạn có chắc chắn muốn xóa mẫu báo cáo '{st.session_state.deleting_template_name}'?")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Xác nhận", key="confirm_delete"):
                    # Delete the template
                    success = db.delete_report_template(st.session_state.deleting_template_id)
                    if success:
                        st.success("Đã xóa mẫu báo cáo.")
                        st.session_state.show_delete_dialog = False
                        st.session_state.deleting_template_id = None
                        st.session_state.deleting_template_name = None
                        st.rerun()
                    else:
                        st.error("Không thể xóa mẫu báo cáo.")
            
            with col2:
                if st.button("Hủy", key="cancel_delete"):
                    st.session_state.show_delete_dialog = False
                    st.session_state.deleting_template_id = None
                    st.session_state.deleting_template_name = None
                    st.rerun()

def create_report_template():
    """Form to create a new report template."""
    st.subheader("Tạo mẫu báo cáo mới")
    
    with st.form("create_template_form"):
        # Get departments for dropdown
        departments = db.get_organization_departments()
        
        if departments is None or departments.empty:
            st.error("Không thể tải danh sách phòng ban.")
            return
        
        department_options = departments['name'].tolist()
        department_ids = departments['id'].tolist()
        
        # Form fields
        name = st.text_input("Tên mẫu báo cáo", key="create_name")
        description = st.text_area("Mô tả", key="create_description")
        department = st.selectbox("Phòng ban quản lý", department_options, key="create_department")
        
        # Dynamic fields management
        st.subheader("Các trường dữ liệu")
        
        if 'fields' not in st.session_state:
            st.session_state.fields = []
        
        for i, field in enumerate(st.session_state.fields):
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                field['label'] = st.text_input(f"Tên trường {i+1}", value=field['label'], key=f"field_label_{i}")
            
            with col2:
                field['type'] = st.selectbox(
                    f"Loại dữ liệu {i+1}", 
                    ["text", "number", "date"], 
                    index=["text", "number", "date"].index(field['type']),
                    key=f"field_type_{i}"
                )
            
            with col3:
                if st.button("Xóa", key=f"remove_field_{i}"):
                    st.session_state.fields.pop(i)
                    st.rerun()
        
        if st.button("Thêm trường", key="add_field"):
            # Generate a unique ID for the field
            field_id = f"field_{len(st.session_state.fields) + 1}"
            st.session_state.fields.append({
                'id': field_id,
                'label': f"Trường {len(st.session_state.fields) + 1}",
                'type': "text"
            })
            st.rerun()
        
        submitted = st.form_submit_button("Tạo mẫu báo cáo")
        
        if submitted:
            if not name:
                st.error("Vui lòng nhập tên mẫu báo cáo.")
            elif not st.session_state.fields:
                st.error("Vui lòng thêm ít nhất một trường dữ liệu.")
            else:
                # Get department ID from selection
                department_idx = department_options.index(department)
                department_id = department_ids[department_idx]
                
                # Convert fields to JSON
                fields_json = json.dumps(st.session_state.fields)
                
                # Save template to database
                success = db.add_report_template(name, description, fields_json, department_id)
                
                if success:
                    # Get the template ID of the newly created template
                    templates = db.get_report_templates()
                    new_template = templates[templates['name'] == name].iloc[0]
                    template_id = new_template['id']
                    
                    # Create an empty sheet structure and save it
                    sheet_structure = {
                        "Báo cáo": {
                            "fields": st.session_state.fields
                        }
                    }
                    db.update_report_template_sheet_structure(template_id, json.dumps(sheet_structure))
                    
                    st.success("Đã tạo mẫu báo cáo thành công.")
                    st.session_state.fields = []
                    
                    # Offer to configure Excel structure
                    st.info("Bạn có thể thiết lập cấu trúc Excel cho mẫu báo cáo này.")
                    if st.button("Thiết lập cấu trúc Excel"):
                        st.session_state.configuring_template_id = template_id
                        st.session_state.configuring_template = new_template.to_dict()
                        st.session_state.show_excel_config = True
                        st.rerun()
                else:
                    st.error("Không thể tạo mẫu báo cáo. Vui lòng thử lại sau.")

def edit_report_template(template):
    """Form to edit an existing report template."""
    st.subheader(f"Chỉnh sửa mẫu báo cáo: {template['name']}")
    
    # Get departments for dropdown
    departments = db.get_organization_departments()
    
    if departments is None or departments.empty:
        st.error("Không thể tải danh sách phòng ban.")
        return
    
    department_options = departments['name'].tolist()
    department_ids = departments['id'].tolist()
    
    # Get current department
    current_dept_id = template['department_id']
    current_dept_idx = 0
    
    for i, dept_id in enumerate(department_ids):
        if dept_id == current_dept_id:
            current_dept_idx = i
            break
    
    # Parse fields from JSON
    fields = json.loads(template['fields'])
    
    # Initialize session state for editing fields if not exists
    if 'editing_fields' not in st.session_state:
        st.session_state.editing_fields = fields
    
    with st.form("edit_template_form"):
        name = st.text_input("Tên mẫu báo cáo", value=template['name'], key="edit_name")
        description = st.text_area("Mô tả", value=template['description'], key="edit_description")
        department = st.selectbox(
            "Phòng ban quản lý", 
            department_options, 
            index=current_dept_idx,
            key="edit_department"
        )
        
        # Dynamic fields management
        st.subheader("Các trường dữ liệu")
        
        for i, field in enumerate(st.session_state.editing_fields):
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                field['label'] = st.text_input(f"Tên trường {i+1}", value=field['label'], key=f"edit_field_label_{i}")
            
            with col2:
                field_type = field.get('type', 'text')
                field['type'] = st.selectbox(
                    f"Loại dữ liệu {i+1}", 
                    ["text", "number", "date"], 
                    index=["text", "number", "date"].index(field_type) if field_type in ["text", "number", "date"] else 0,
                    key=f"edit_field_type_{i}"
                )
            
            with col3:
                if st.button("Xóa", key=f"edit_remove_field_{i}"):
                    st.session_state.editing_fields.pop(i)
                    st.rerun()
        
        if st.button("Thêm trường", key="edit_add_field"):
            # Generate a unique ID for the field
            field_id = f"field_{len(st.session_state.editing_fields) + 1}"
            st.session_state.editing_fields.append({
                'id': field_id,
                'label': f"Trường {len(st.session_state.editing_fields) + 1}",
                'type': "text"
            })
            st.rerun()
        
        col1, col2 = st.columns(2)
        
        with col1:
            submitted = st.form_submit_button("Cập nhật mẫu báo cáo")
        
        with col2:
            configure_excel = st.form_submit_button("Thiết lập cấu trúc Excel")
        
        if submitted:
            if not name:
                st.error("Vui lòng nhập tên mẫu báo cáo.")
            elif not st.session_state.editing_fields:
                st.error("Vui lòng thêm ít nhất một trường dữ liệu.")
            else:
                # Get department ID from selection
                department_idx = department_options.index(department)
                department_id = department_ids[department_idx]
                
                # Convert fields to JSON
                fields_json = json.dumps(st.session_state.editing_fields)
                
                # Update template in database
                success = db.update_report_template(template['id'], name, description, fields_json, department_id)
                
                if success:
                    st.success("Đã cập nhật mẫu báo cáo thành công.")
                    
                    # Update sheet structure if it exists
                    sheet_structure = db.get_report_template_sheet_structure(template['id'])
                    if sheet_structure:
                        sheet_data = json.loads(sheet_structure)
                        
                        # Update fields in all sheets
                        for sheet_name in sheet_data:
                            sheet_data[sheet_name]['fields'] = st.session_state.editing_fields
                        
                        db.update_report_template_sheet_structure(template['id'], json.dumps(sheet_data))
                    else:
                        # Create default sheet structure
                        sheet_structure = {
                            "Báo cáo": {
                                "fields": st.session_state.editing_fields
                            }
                        }
                        db.update_report_template_sheet_structure(template['id'], json.dumps(sheet_structure))
                    
                    # Close the edit dialog
                    st.session_state.show_edit_dialog = False
                    st.session_state.editing_template = None
                    st.session_state.editing_fields = None
                    st.rerun()
                else:
                    st.error("Không thể cập nhật mẫu báo cáo. Vui lòng thử lại sau.")
        
        elif configure_excel:
            # Save current changes first
            if name and st.session_state.editing_fields:
                # Get department ID from selection
                department_idx = department_options.index(department)
                department_id = department_ids[department_idx]
                
                # Convert fields to JSON
                fields_json = json.dumps(st.session_state.editing_fields)
                
                # Update template in database
                success = db.update_report_template(template['id'], name, description, fields_json, department_id)
                
                if success:
                    st.success("Đã cập nhật mẫu báo cáo thành công.")
                    
                    # Go to Excel configuration
                    st.session_state.configuring_template_id = template['id']
                    st.session_state.configuring_template = template
                    st.session_state.configuring_fields = st.session_state.editing_fields
                    st.session_state.show_excel_config = True
                    st.rerun()
                else:
                    st.error("Không thể cập nhật mẫu báo cáo. Vui lòng thử lại sau.")
            else:
                st.error("Vui lòng điền đầy đủ thông tin trước khi thiết lập cấu trúc Excel.")
    
    # Close button outside the form
    if st.button("Đóng", key="edit_close"):
        st.session_state.show_edit_dialog = False
        st.session_state.editing_template = None
        st.session_state.editing_fields = None
        st.rerun()

def configure_excel_sheets(template):
    """Configure Excel sheet structure for a report template."""
    st.subheader(f"Thiết lập cấu trúc Excel: {template['name']}")
    
    # Get fields from session state or from template
    if 'configuring_fields' in st.session_state:
        fields = st.session_state.configuring_fields
    else:
        fields = json.loads(template['fields'])
    
    # Get current sheet structure if it exists
    current_structure = db.get_report_template_sheet_structure(template['id'])
    
    if current_structure:
        sheet_structure = json.loads(current_structure)
    else:
        # Create default structure with a single sheet
        sheet_structure = {
            "Báo cáo": {
                "fields": fields
            }
        }
    
    # Initialize session state for sheet management
    if 'sheet_structure' not in st.session_state:
        st.session_state.sheet_structure = sheet_structure
    
    # Sheet management
    st.write("**Quản lý các sheet trong Excel:**")
    
    for sheet_name in list(st.session_state.sheet_structure.keys()):
        with st.expander(f"Sheet: {sheet_name}", expanded=True):
            # Allow changing sheet name
            new_name = st.text_input(f"Tên sheet", value=sheet_name, key=f"sheet_name_{sheet_name}")
            
            if new_name != sheet_name and new_name and new_name not in st.session_state.sheet_structure:
                # Rename the sheet
                st.session_state.sheet_structure[new_name] = st.session_state.sheet_structure[sheet_name]
                del st.session_state.sheet_structure[sheet_name]
                st.rerun()
            
            # Field management for this sheet
            st.write("**Các trường dữ liệu trong sheet:**")
            
            # Get field IDs already in this sheet
            sheet_field_ids = [field['id'] for field in st.session_state.sheet_structure[sheet_name]['fields']]
            
            # Create a list of all available fields for multiselect
            field_options = {field['id']: field['label'] for field in fields}
            
            # Show selected fields and allow reordering
            selected_fields = st.multiselect(
                "Chọn các trường dữ liệu",
                options=list(field_options.keys()),
                default=sheet_field_ids,
                format_func=lambda x: field_options[x],
                key=f"fields_{sheet_name}"
            )
            
            # Update the sheet's fields based on selection and ordering
            if selected_fields:
                # Create new field list preserving field details
                new_field_list = []
                for field_id in selected_fields:
                    for field in fields:
                        if field['id'] == field_id:
                            new_field_list.append(field)
                            break
                
                st.session_state.sheet_structure[sheet_name]['fields'] = new_field_list
            
            # Delete sheet button
            if len(st.session_state.sheet_structure) > 1:  # Don't allow deleting if it's the only sheet
                if st.button("Xóa sheet này", key=f"delete_sheet_{sheet_name}"):
                    del st.session_state.sheet_structure[sheet_name]
                    st.rerun()
    
    # Add new sheet button
    if st.button("Thêm sheet mới"):
        # Generate a unique sheet name
        base_name = "Sheet mới"
        sheet_name = base_name
        counter = 1
        
        while sheet_name in st.session_state.sheet_structure:
            sheet_name = f"{base_name} {counter}"
            counter += 1
        
        # Add new sheet with all fields
        st.session_state.sheet_structure[sheet_name] = {
            "fields": fields
        }
        
        st.rerun()
    
    # Save changes button
    if st.button("Lưu cấu trúc Excel"):
        # Save sheet structure to database
        success = db.update_report_template_sheet_structure(
            template['id'], 
            json.dumps(st.session_state.sheet_structure)
        )
        
        if success:
            st.success("Đã lưu cấu trúc Excel thành công.")
            # Clear session state
            st.session_state.show_excel_config = False
            st.session_state.configuring_template_id = None
            st.session_state.configuring_template = None
            st.session_state.configuring_fields = None
            st.session_state.sheet_structure = None
            st.rerun()
        else:
            st.error("Không thể lưu cấu trúc Excel. Vui lòng thử lại sau.")
    
    # Cancel button
    if st.button("Hủy"):
        # Clear session state without saving
        st.session_state.show_excel_config = False
        st.session_state.configuring_template_id = None
        st.session_state.configuring_template = None
        st.session_state.configuring_fields = None
        st.session_state.sheet_structure = None
        st.rerun()