import streamlit as st
import pandas as pd
import json
import database as db

def settings_page():
    """Display the settings page with multiple tabs."""
    st.title("Cài đặt hệ thống")
    st.write("Quản lý cài đặt hệ thống Vinatex Report Portal")
    
    # Create tabs for different settings categories
    tab1, tab2, tab3, tab4 = st.tabs(["Tài khoản", "Thông báo", "SharePoint", "Email"])
    
    with tab1:
        account_settings()
    with tab2:
        notification_settings()
    with tab3:
        sharepoint_settings()
    with tab4:
        email_settings()

def account_settings():
    """Manage user account settings."""
    st.subheader("Cài đặt tài khoản")
    
    # Change password form
    with st.form("change_password_form"):
        st.write("Thay đổi mật khẩu")
        
        current_password = st.text_input("Mật khẩu hiện tại", type="password")
        new_password = st.text_input("Mật khẩu mới", type="password")
        confirm_password = st.text_input("Xác nhận mật khẩu mới", type="password")
        
        submitted = st.form_submit_button("Cập nhật mật khẩu")
        
        if submitted:
            if not current_password or not new_password or not confirm_password:
                st.error("Vui lòng điền đầy đủ thông tin")
            elif new_password != confirm_password:
                st.error("Mật khẩu mới không khớp")
            else:
                # Validate current password
                user_data = db.validate_user(st.session_state.username, current_password)
                if user_data:
                    # Update password
                    result = db.execute_query(
                        "UPDATE users SET password = %s WHERE id = %s",
                        (new_password, st.session_state.user_id),
                        fetch=False
                    )
                    if result:
                        st.success("Mật khẩu đã được cập nhật thành công")
                    else:
                        st.error("Không thể cập nhật mật khẩu")
                else:
                    st.error("Mật khẩu hiện tại không đúng")

def notification_settings():
    """Configure notification settings."""
    st.subheader("Cài đặt thông báo")
    st.write("Quản lý cách bạn nhận thông báo từ hệ thống")
    
    # Load current settings
    settings = load_notification_settings()
    
    # Toggle switches for different notification types
    email_notifications = st.toggle(
        "Thông báo qua email",
        value=settings.get("email_notifications", True),
        help="Nhận thông báo và cảnh báo qua email"
    )
    
    st.markdown("---")
    st.subheader("Tùy chọn thông báo")
    
    # Show email notification options if enabled
    if email_notifications:
        report_reminder = st.toggle(
            "Nhắc nhở nộp báo cáo",
            value=settings.get("report_reminder", True),
            help="Nhận thông báo khi báo cáo sắp đến hạn nộp"
        )
        
        overdue_alert = st.toggle(
            "Cảnh báo quá hạn",
            value=settings.get("overdue_alert", True),
            help="Nhận thông báo khi báo cáo quá hạn nộp"
        )
        
        system_updates = st.toggle(
            "Cập nhật hệ thống",
            value=settings.get("system_updates", False),
            help="Nhận thông báo về các thay đổi và cập nhật hệ thống"
        )
    else:
        report_reminder = False
        overdue_alert = False
        system_updates = False
    
    # Save button
    if st.button("Lưu thay đổi", key="save_notifications"):
        # Compile settings
        new_settings = {
            "email_notifications": email_notifications,
            "report_reminder": report_reminder,
            "overdue_alert": overdue_alert,
            "system_updates": system_updates
        }
        
        # Save to database
        if save_notification_settings(new_settings):
            st.success("Đã lưu cài đặt thông báo thành công")
        else:
            st.error("Không thể lưu cài đặt thông báo")

def sharepoint_settings():
    """Configure SharePoint integration settings."""
    st.subheader("Cài đặt SharePoint")
    st.write("Cấu hình kết nối với SharePoint để lưu trữ báo cáo")
    
    # Load current settings
    settings = load_sharepoint_settings()
    
    # SharePoint configuration form
    with st.form("sharepoint_settings_form"):
        # SharePoint connection info
        st.write("Thông tin kết nối SharePoint")
        
        sharepoint_url = st.text_input(
            "URL SharePoint",
            value=settings.get("sharepoint_url", "https://vinatex.sharepoint.com/sites/reports"),
            help="URL thư mục SharePoint nơi lưu trữ các file báo cáo"
        )
        
        # SharePoint authentication
        st.write("Tài khoản SharePoint")
        
        sharepoint_username = st.text_input(
            "Tài khoản SharePoint",
            value=settings.get("sharepoint_username", "admin@vinatex.com.vn")
        )
        
        sharepoint_password = st.text_input(
            "Mật khẩu SharePoint",
            type="password",
            help="Để trống nếu không thay đổi mật khẩu"
        )
        
        # File organization
        st.write("Cấu trúc thư mục")
        
        document_library = st.text_input(
            "Đường dẫn thư mục SharePoint nơi lưu trữ các file báo cáo",
            value=settings.get("document_library", "Documents/Reports")
        )
        
        use_org_folders = st.checkbox(
            "Tạo thư mục riêng cho mỗi đơn vị",
            value=settings.get("use_org_folders", True),
            help="Tạo thư mục riêng cho mỗi đơn vị trong thư mục Reports"
        )
        
        # Submit button
        submitted = st.form_submit_button("Lưu thay đổi")
        
        if submitted:
            # Compile settings
            new_settings = {
                "sharepoint_url": sharepoint_url,
                "sharepoint_username": sharepoint_username,
                "document_library": document_library,
                "use_org_folders": use_org_folders
            }
            
            # Add password only if provided
            if sharepoint_password:
                new_settings["sharepoint_password"] = sharepoint_password
            elif "sharepoint_password" in settings:
                new_settings["sharepoint_password"] = settings["sharepoint_password"]
            
            # Save to database
            if save_sharepoint_settings(new_settings):
                st.success("Đã lưu cài đặt SharePoint thành công")
            else:
                st.error("Không thể lưu cài đặt SharePoint")

def email_settings():
    """Configure email server settings."""
    st.subheader("Cài đặt Email")
    st.write("Cấu hình máy chủ email để gửi thông báo")
    
    # Load current settings
    settings = load_email_settings()
    
    # Email server configuration form
    with st.form("email_settings_form"):
        st.write("Cấu hình máy chủ SMTP")
        
        smtp_server = st.text_input(
            "Máy chủ SMTP",
            value=settings.get("smtp_server", "smtp.office365.com")
        )
        
        smtp_port = st.text_input(
            "Cổng SMTP",
            value=settings.get("smtp_port", "587")
        )
        
        st.write("Tài khoản email")
        
        email_username = st.text_input(
            "Tài khoản email",
            value=settings.get("email_username", "reports@vinatex.com.vn")
        )
        
        email_password = st.text_input(
            "Mật khẩu email",
            type="password",
            help="Để trống nếu không thay đổi mật khẩu"
        )
        
        sender_name = st.text_input(
            "Tên hiển thị khi gửi email",
            value=settings.get("sender_name", "Vinatex Report Portal")
        )
        
        st.write("Kiểm tra cấu hình")
        
        test_email = st.text_input(
            "Gửi email kiểm tra",
            help="Gửi một email kiểm tra để xác nhận cấu hình đúng",
            placeholder="Nhập địa chỉ email để kiểm tra"
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            test_button = st.form_submit_button("Gửi kiểm tra")
        with col2:
            submitted = st.form_submit_button("Lưu thay đổi")
        
        if test_button and test_email:
            st.info("Chức năng gửi email kiểm tra đang được phát triển")
        
        if submitted:
            # Compile settings
            new_settings = {
                "smtp_server": smtp_server,
                "smtp_port": smtp_port,
                "email_username": email_username,
                "sender_name": sender_name
            }
            
            # Add password only if provided
            if email_password:
                new_settings["email_password"] = email_password
            elif "email_password" in settings:
                new_settings["email_password"] = settings["email_password"]
            
            # Save to database
            if save_email_settings(new_settings):
                st.success("Đã lưu cài đặt Email thành công")
            else:
                st.error("Không thể lưu cài đặt Email")

def load_notification_settings():
    """Load notification settings from database or create default settings"""
    settings_data = db.get_settings("notification")
    
    if settings_data:
        return json.loads(settings_data)
    else:
        # Default settings
        default_settings = {
            "email_notifications": True,
            "report_reminder": True,
            "overdue_alert": True,
            "system_updates": False
        }
        save_notification_settings(default_settings)
        return default_settings

def save_notification_settings(settings):
    """Save notification settings to database"""
    settings_json = json.dumps(settings)
    return db.save_settings("notification", settings_json)

def load_sharepoint_settings():
    """Load SharePoint settings from database or create default settings"""
    settings_data = db.get_settings("sharepoint")
    
    if settings_data:
        return json.loads(settings_data)
    else:
        # Default settings
        default_settings = {
            "sharepoint_url": "https://vinatex.sharepoint.com/sites/reports",
            "sharepoint_username": "admin@vinatex.com.vn",
            "sharepoint_password": "default_password",
            "document_library": "Documents/Reports",
            "use_org_folders": True
        }
        save_sharepoint_settings(default_settings)
        return default_settings

def save_sharepoint_settings(settings):
    """Save SharePoint settings to database"""
    settings_json = json.dumps(settings)
    return db.save_settings("sharepoint", settings_json)

def load_email_settings():
    """Load email settings from database or create default settings"""
    settings_data = db.get_settings("email")
    
    if settings_data:
        return json.loads(settings_data)
    else:
        # Default settings
        default_settings = {
            "smtp_server": "smtp.office365.com",
            "smtp_port": "587",
            "email_username": "reports@vinatex.com.vn",
            "email_password": "default_password",
            "sender_name": "Vinatex Report Portal"
        }
        save_email_settings(default_settings)
        return default_settings

def save_email_settings(settings):
    """Save email settings to database"""
    settings_json = json.dumps(settings)
    return db.save_settings("email", settings_json)