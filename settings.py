import streamlit as st
import pandas as pd
import json
import database as db

def settings_page():
    """Display the settings page with multiple tabs."""
    st.title("⚙️ Cài đặt hệ thống")
    
    # Create tabs for different settings categories
    tab1, tab2, tab3 = st.tabs(["Tài khoản", "Thông báo", "SharePoint"])
    
    with tab1:
        account_settings()
    
    with tab2:
        notification_settings()
    
    with tab3:
        sharepoint_settings()

def account_settings():
    """Manage user account settings."""
    st.header("Cài đặt tài khoản")
    
    # Current user info
    if "user" in st.session_state:
        user = st.session_state.user
        st.subheader("Thông tin tài khoản")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Tên đăng nhập:** {user['username']}")
        with col2:
            st.write(f"**Vai trò:** {user['role']}")
        
        # Change password form
        st.subheader("Đổi mật khẩu")
        with st.form("change_password_form"):
            current_password = st.text_input("Mật khẩu hiện tại", type="password")
            new_password = st.text_input("Mật khẩu mới", type="password")
            confirm_password = st.text_input("Xác nhận mật khẩu mới", type="password")
            
            submitted = st.form_submit_button("Cập nhật mật khẩu")
            
            if submitted:
                if not current_password or not new_password or not confirm_password:
                    st.error("Vui lòng điền đầy đủ thông tin.")
                elif new_password != confirm_password:
                    st.error("Mật khẩu mới không khớp.")
                else:
                    # Verify current password
                    verified_user = db.validate_user(user['username'], current_password)
                    if verified_user:
                        # Update password
                        success = db.update_user(
                            user['id'], 
                            user['username'], 
                            new_password, 
                            user['role'], 
                            user['organization_id']
                        )
                        if success:
                            st.success("Đã cập nhật mật khẩu thành công.")
                        else:
                            st.error("Không thể cập nhật mật khẩu. Vui lòng thử lại sau.")
                    else:
                        st.error("Mật khẩu hiện tại không đúng.")

def notification_settings():
    """Configure notification settings."""
    st.header("Cài đặt thông báo")
    
    # Load current settings
    settings = load_notification_settings()
    
    st.subheader("Thông báo email")
    
    with st.form("notification_settings_form"):
        settings['enable_email_notifications'] = st.toggle(
            "Bật thông báo email", 
            value=settings['enable_email_notifications']
        )
        
        st.write("**Gửi thông báo cho các sự kiện:**")
        
        col1, col2 = st.columns(2)
        with col1:
            settings['notify_on_report_assignment'] = st.checkbox(
                "Khi được giao báo cáo mới", 
                value=settings['notify_on_report_assignment']
            )
            settings['notify_on_report_due'] = st.checkbox(
                "Trước hạn nộp báo cáo", 
                value=settings['notify_on_report_due']
            )
        
        with col2:
            settings['notify_on_report_submission'] = st.checkbox(
                "Khi báo cáo được nộp", 
                value=settings['notify_on_report_submission']
            )
            settings['notify_on_status_change'] = st.checkbox(
                "Khi trạng thái báo cáo thay đổi", 
                value=settings['notify_on_status_change']
            )
        
        st.write("**Nhắc nhở:**")
        settings['reminder_days'] = st.number_input(
            "Số ngày trước hạn để gửi nhắc nhở", 
            min_value=1, 
            max_value=14, 
            value=settings['reminder_days']
        )
        
        submitted = st.form_submit_button("Lưu cài đặt")
        
        if submitted:
            save_notification_settings(settings)
            st.success("Đã lưu cài đặt thông báo.")

def sharepoint_settings():
    """Configure SharePoint integration settings."""
    st.header("Cài đặt SharePoint")
    
    # Load current settings
    settings = load_sharepoint_settings()
    
    with st.form("sharepoint_settings_form"):
        settings['sharepoint_url'] = st.text_input(
            "URL SharePoint", 
            value=settings['sharepoint_url'],
            help="URL cơ sở của site SharePoint, ví dụ: https://vinatex.sharepoint.com/sites/reports"
        )
        
        settings['document_library'] = st.text_input(
            "Thư viện tài liệu", 
            value=settings['document_library'],
            help="Đường dẫn thư viện tài liệu, ví dụ: Documents/Reports"
        )
        
        settings['use_org_folders'] = st.checkbox(
            "Tạo thư mục riêng cho mỗi đơn vị", 
            value=settings['use_org_folders'],
            help="Tạo thư mục riêng cho mỗi đơn vị trong thư viện tài liệu"
        )
        
        # SharePoint credentials (in a real app, these would be securely stored)
        st.subheader("Thông tin xác thực (nếu cần)")
        
        settings['use_credentials'] = st.checkbox(
            "Sử dụng thông tin xác thực",
            value=settings.get('use_credentials', False)
        )
        
        if settings['use_credentials']:
            settings['username'] = st.text_input(
                "Tên đăng nhập SharePoint", 
                value=settings.get('username', '')
            )
            
            if 'password' not in settings:
                settings['password'] = ''
                
            new_password = st.text_input(
                "Mật khẩu SharePoint", 
                type="password", 
                help="Để trống nếu không muốn thay đổi mật khẩu hiện tại"
            )
            
            if new_password:
                settings['password'] = new_password
        
        submitted = st.form_submit_button("Lưu cài đặt")
        
        if submitted:
            save_sharepoint_settings(settings)
            st.success("Đã lưu cài đặt SharePoint.")

def email_settings():
    """Configure email server settings."""
    st.header("Cài đặt máy chủ email")
    
    # Load current settings
    settings = load_email_settings()
    
    with st.form("email_settings_form"):
        settings['smtp_server'] = st.text_input(
            "Máy chủ SMTP", 
            value=settings['smtp_server']
        )
        
        settings['smtp_port'] = st.number_input(
            "Cổng SMTP", 
            value=settings['smtp_port'],
            min_value=1,
            max_value=65535
        )
        
        settings['use_ssl'] = st.checkbox(
            "Sử dụng SSL", 
            value=settings['use_ssl']
        )
        
        settings['smtp_username'] = st.text_input(
            "Tên đăng nhập SMTP", 
            value=settings['smtp_username']
        )
        
        if 'smtp_password' not in settings:
            settings['smtp_password'] = ''
            
        new_password = st.text_input(
            "Mật khẩu SMTP", 
            type="password", 
            help="Để trống nếu không muốn thay đổi mật khẩu hiện tại"
        )
        
        if new_password:
            settings['smtp_password'] = new_password
        
        settings['from_email'] = st.text_input(
            "Địa chỉ email gửi", 
            value=settings['from_email']
        )
        
        settings['email_signature'] = st.text_area(
            "Chữ ký email", 
            value=settings['email_signature']
        )
        
        submitted = st.form_submit_button("Lưu cài đặt")
        
        if submitted:
            save_email_settings(settings)
            st.success("Đã lưu cài đặt email.")

def load_notification_settings():
    """Load notification settings from database or create default settings"""
    settings_data = db.get_settings("notifications")
    
    if settings_data:
        return json.loads(settings_data)
    else:
        # Default notification settings
        return {
            "enable_email_notifications": True,
            "notify_on_report_assignment": True,
            "notify_on_report_due": True,
            "notify_on_report_submission": True,
            "notify_on_status_change": False,
            "reminder_days": 3
        }

def save_notification_settings(settings):
    """Save notification settings to database"""
    settings_data = json.dumps(settings)
    db.save_settings("notifications", settings_data)

def load_sharepoint_settings():
    """Load SharePoint settings from database or create default settings"""
    settings_data = db.get_settings("sharepoint")
    
    if settings_data:
        return json.loads(settings_data)
    else:
        # Default SharePoint settings
        return {
            "sharepoint_url": "https://vinatex.sharepoint.com/sites/reports",
            "document_library": "Documents/Reports",
            "use_org_folders": True,
            "use_credentials": False,
            "username": "",
            "password": ""
        }

def save_sharepoint_settings(settings):
    """Save SharePoint settings to database"""
    settings_data = json.dumps(settings)
    db.save_settings("sharepoint", settings_data)

def load_email_settings():
    """Load email settings from database or create default settings"""
    settings_data = db.get_settings("email")
    
    if settings_data:
        return json.loads(settings_data)
    else:
        # Default email settings
        return {
            "smtp_server": "smtp.vinatex.com.vn",
            "smtp_port": 587,
            "use_ssl": True,
            "smtp_username": "reports@vinatex.com.vn",
            "smtp_password": "",
            "from_email": "reports@vinatex.com.vn",
            "email_signature": "Hệ thống báo cáo Tập đoàn Dệt may Việt Nam\nVinatex Report Management System"
        }

def save_email_settings(settings):
    """Save email settings to database"""
    settings_data = json.dumps(settings)
    db.save_settings("email", settings_data)