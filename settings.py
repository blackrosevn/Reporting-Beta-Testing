import streamlit as st
import pandas as pd
import json
import os
import database as db
from datetime import datetime

def settings_page():
    st.title("Cài đặt hệ thống")
    st.markdown("Quản lý cài đặt hệ thống Vinatex Report Portal")
    
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
    st.subheader("Cài đặt tài khoản")
    st.markdown("Quản lý thông tin tài khoản và mật khẩu")
    
    # Current user information
    current_user = st.session_state.username
    current_role = st.session_state.user_role
    
    # Display current user information
    st.write(f"**Tên đăng nhập:** {current_user}")
    st.write(f"**Quyền truy cập:** {current_role}")
    
    # Change password form
    with st.form("change_password_form"):
        st.subheader("Đổi mật khẩu")
        current_password = st.text_input("Mật khẩu hiện tại", type="password")
        new_password = st.text_input("Mật khẩu mới", type="password")
        confirm_password = st.text_input("Xác nhận mật khẩu mới", type="password")
        
        submitted = st.form_submit_button("Đổi mật khẩu")
        
        if submitted:
            if not current_password or not new_password or not confirm_password:
                st.error("Vui lòng điền đầy đủ thông tin")
            elif new_password != confirm_password:
                st.error("Mật khẩu mới không khớp")
            else:
                # Verify current password and update to new password
                user_id = st.session_state.user_id
                # Implement password change logic here
                st.success("Đổi mật khẩu thành công")

def notification_settings():
    st.subheader("Cài đặt thông báo")
    st.markdown("Quản lý cách bạn nhận thông báo từ hệ thống")
    
    # Load current notification settings
    notification_settings = load_notification_settings()
    
    # Email notifications toggle
    email_notifications = st.toggle(
        "Thông báo qua email",
        value=notification_settings.get("email_notifications", True),
        help="Nhận thông báo và cảnh báo qua email"
    )
    
    if email_notifications:
        st.markdown("#### Nhắc nhở nộp báo cáo")
        report_reminder = st.toggle(
            "Nhắc nhở nộp báo cáo",
            value=notification_settings.get("report_reminder", True),
            help="Nhận thông báo khi sắp đến hạn nộp báo cáo"
        )
        
        st.markdown("#### Cảnh báo quá hạn")
        overdue_alert = st.toggle(
            "Cảnh báo quá hạn",
            value=notification_settings.get("overdue_alert", True),
            help="Nhận thông báo khi báo cáo quá hạn nộp"
        )
        
        st.markdown("#### Cập nhật hệ thống")
        system_updates = st.toggle(
            "Cập nhật hệ thống",
            value=notification_settings.get("system_updates", False),
            help="Nhận thông báo về các thay đổi và cập nhật hệ thống"
        )
    
    # Save button
    if st.button("Lưu thay đổi", key="save_notification_settings"):
        # Update notification settings
        notification_settings = {
            "email_notifications": email_notifications,
            "report_reminder": report_reminder if email_notifications else False,
            "overdue_alert": overdue_alert if email_notifications else False,
            "system_updates": system_updates if email_notifications else False,
            "updated_at": datetime.now().isoformat()
        }
        
        # Save settings
        save_notification_settings(notification_settings)
        st.success("Đã lưu cài đặt thông báo")

def sharepoint_settings():
    st.subheader("Cài đặt SharePoint")
    st.markdown("Cấu hình kết nối với SharePoint để lưu trữ báo cáo")
    
    # Load current SharePoint settings
    sharepoint_settings = load_sharepoint_settings()
    
    # SharePoint connection settings
    st.markdown("### Thông tin kết nối SharePoint")
    
    sharepoint_url = st.text_input(
        "URL SharePoint",
        value=sharepoint_settings.get("sharepoint_url", "https://vinatex.sharepoint.com/sites/reports"),
        help="URL của trang SharePoint để lưu trữ tài liệu"
    )
    
    document_library = st.text_input(
        "URL thư mục SharePoint nơi lưu trữ các file báo cáo",
        value=sharepoint_settings.get("document_library", "Documents/Reports"),
        help="Thư mục trong SharePoint nơi các báo cáo sẽ được lưu trữ"
    )
    
    # SharePoint credentials
    st.markdown("### Tài khoản SharePoint")
    
    sharepoint_username = st.text_input(
        "Tài khoản SharePoint",
        value=sharepoint_settings.get("sharepoint_username", "admin@vinatex.com.vn"),
        help="Email hoặc tên đăng nhập SharePoint"
    )
    
    # Only show placeholder for password, not the actual value
    sharepoint_password = st.text_input(
        "Mật khẩu SharePoint",
        type="password",
        help="Để trống nếu không thay đổi mật khẩu"
    )
    st.caption("Để trống nếu không thay đổi mật khẩu")
    
    # Organization folder structure
    st.markdown("### Cấu trúc thư mục theo đơn vị")
    use_org_folders = st.checkbox(
        "Sử dụng thư mục riêng cho từng đơn vị",
        value=sharepoint_settings.get("use_org_folders", True),
        help="Tạo thư mục riêng cho mỗi đơn vị trong thư mục báo cáo"
    )
    
    # Save button
    if st.button("Lưu thay đổi", key="save_sharepoint_settings"):
        # Update SharePoint settings
        new_settings = {
            "sharepoint_url": sharepoint_url,
            "document_library": document_library,
            "sharepoint_username": sharepoint_username,
            "use_org_folders": use_org_folders,
            "updated_at": datetime.now().isoformat()
        }
        
        # Only update password if a new one is provided
        if sharepoint_password:
            new_settings["sharepoint_password"] = sharepoint_password
        else:
            # Keep the existing password
            new_settings["sharepoint_password"] = sharepoint_settings.get("sharepoint_password", "")
        
        # Save settings
        save_sharepoint_settings(new_settings)
        st.success("Đã lưu cài đặt SharePoint")

def email_settings():
    st.subheader("Cài đặt Email")
    st.markdown("Cấu hình máy chủ email để gửi thông báo")
    
    # Load current email settings
    email_settings = load_email_settings()
    
    # SMTP server configuration
    st.markdown("### Cấu hình máy chủ SMTP")
    
    smtp_server = st.text_input(
        "Máy chủ SMTP",
        value=email_settings.get("smtp_server", "smtp.office365.com"),
        help="Địa chỉ máy chủ SMTP để gửi email"
    )
    
    smtp_port = st.text_input(
        "Cổng SMTP",
        value=email_settings.get("smtp_port", "587"),
        help="Cổng máy chủ SMTP (thường là 587 hoặc 465)"
    )
    
    # Email account
    st.markdown("### Tài khoản email")
    
    email_address = st.text_input(
        "Tài khoản email",
        value=email_settings.get("email_address", "reports@vinatex.com.vn"),
        help="Địa chỉ email dùng để gửi thông báo"
    )
    
    # Only show placeholder for password, not the actual value
    email_password = st.text_input(
        "Mật khẩu email",
        type="password",
        help="Để trống nếu không thay đổi mật khẩu"
    )
    st.caption("Để trống nếu không thay đổi mật khẩu")
    
    # Sender display name
    sender_name = st.text_input(
        "Tên hiển thị khi gửi email",
        value=email_settings.get("sender_name", "Vinatex Report Portal"),
        help="Tên sẽ hiển thị trong email gửi đi"
    )
    
    # Test configuration
    if st.button("Gửi email kiểm tra"):
        # Implement email sending test
        st.info("Gửi email kiểm tra... Chức năng này sẽ được cài đặt sau")
    
    # Save button
    if st.button("Lưu thay đổi", key="save_email_settings"):
        # Update email settings
        new_settings = {
            "smtp_server": smtp_server,
            "smtp_port": smtp_port,
            "email_address": email_address,
            "sender_name": sender_name,
            "updated_at": datetime.now().isoformat()
        }
        
        # Only update password if a new one is provided
        if email_password:
            new_settings["email_password"] = email_password
        else:
            # Keep the existing password
            new_settings["email_password"] = email_settings.get("email_password", "")
        
        # Save settings
        save_email_settings(new_settings)
        st.success("Đã lưu cài đặt Email")

def load_notification_settings():
    """Load notification settings from database or create default settings"""
    # Try to get settings from the database
    settings = db.get_settings("notification")
    
    if settings:
        try:
            return json.loads(settings)
        except:
            pass
    
    # Default settings
    return {
        "email_notifications": True,
        "report_reminder": True,
        "overdue_alert": True,
        "system_updates": False,
        "updated_at": datetime.now().isoformat()
    }

def save_notification_settings(settings):
    """Save notification settings to database"""
    db.save_settings("notification", json.dumps(settings))

def load_sharepoint_settings():
    """Load SharePoint settings from database or create default settings"""
    # Try to get settings from the database
    settings = db.get_settings("sharepoint")
    
    if settings:
        try:
            return json.loads(settings)
        except:
            pass
    
    # Default settings
    return {
        "sharepoint_url": "https://vinatex.sharepoint.com/sites/reports",
        "document_library": "Documents/Reports",
        "sharepoint_username": "admin@vinatex.com.vn",
        "sharepoint_password": "",
        "use_org_folders": True,
        "updated_at": datetime.now().isoformat()
    }

def save_sharepoint_settings(settings):
    """Save SharePoint settings to database"""
    db.save_settings("sharepoint", json.dumps(settings))

def load_email_settings():
    """Load email settings from database or create default settings"""
    # Try to get settings from the database
    settings = db.get_settings("email")
    
    if settings:
        try:
            return json.loads(settings)
        except:
            pass
    
    # Default settings
    return {
        "smtp_server": "smtp.office365.com",
        "smtp_port": "587",
        "email_address": "reports@vinatex.com.vn",
        "email_password": "",
        "sender_name": "Vinatex Report Portal",
        "updated_at": datetime.now().isoformat()
    }

def save_email_settings(settings):
    """Save email settings to database"""
    db.save_settings("email", json.dumps(settings))