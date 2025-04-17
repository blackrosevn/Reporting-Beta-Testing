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
import settings
import report_templates

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

# Function definitions for dashboard displays
def display_dashboard():
    st.title("Tổng quan báo cáo")
    
    # Display different dashboards based on user role
    if st.session_state.user_role == "admin":
        admin_dashboard()
    elif st.session_state.user_role == "department":
        department_dashboard()
    elif st.session_state.user_role == "unit":
        unit_dashboard()

def admin_dashboard():
    # Create columns for metrics
    col1, col2, col3, col4 = st.columns(4)
    
    # Fetch statistics from database
    total_reports = db.get_total_reports()
    pending_reports = db.get_reports_by_status("pending")
    completed_reports = db.get_reports_by_status("completed")
    overdue_reports = db.get_reports_by_status("overdue")
    
    # Display metrics with icons
    with col1:
        st.markdown("### Tổng số báo cáo")
        st.markdown(f"<div style='text-align: center; font-size: 48px;'>📄 {total_reports['assigned']}</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("### Báo cáo đã nộp")
        st.markdown(f"<div style='text-align: center; color: #28a745; font-size: 48px;'>✓ {completed_reports}</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("### Báo cáo nộp muộn")
        st.markdown(f"<div style='text-align: center; color: #ffc107; font-size: 48px;'>⚠️ {0}</div>", unsafe_allow_html=True)
    
    with col4:
        st.markdown("### Báo cáo quá hạn")
        st.markdown(f"<div style='text-align: center; color: #dc3545; font-size: 48px;'>⚠️ {overdue_reports}</div>", unsafe_allow_html=True)
    
    # Progress chart section
    st.markdown("## Tiến độ nộp báo cáo theo đơn vị")
    
    # Create sample data for the progress chart
    org_data = db.get_report_by_organization()
    if org_data is not None and not org_data.empty:
        # Convert to the format needed for dual-axis chart
        chart_data = []
        for org_name in org_data['organization'].unique():
            org_df = org_data[org_data['organization'] == org_name]
            total = org_df['count'].sum()
            completed = org_df[org_df['status'] == 'completed']['count'].sum() if 'completed' in org_df['status'].values else 0
            completion_rate = (completed / total * 100) if total > 0 else 0
            chart_data.append({
                'organization': org_name,
                'Đã nộp': completed,
                'Chưa nộp': total - completed,
                'Tỉ lệ hoàn thành': completion_rate
            })
        
        chart_df = pd.DataFrame(chart_data)
        
        # Create a combined chart
        fig = px.bar(
            chart_df,
            x='organization',
            y=['Đã nộp', 'Chưa nộp'],
            barmode='stack',
            color_discrete_map={
                'Đã nộp': '#0066b2',
                'Chưa nộp': '#e0e0e0'
            },
            labels={'value': 'Số báo cáo', 'organization': 'Đơn vị', 'variable': 'Trạng thái'}
        )
        
        # Add line chart for completion rate
        completion_rate = px.line(
            chart_df,
            x='organization',
            y='Tỉ lệ hoàn thành',
            color_discrete_sequence=['#28a745']
        ).data[0]
        
        fig.add_trace(completion_rate)
        
        # Configure y-axes
        fig.update_layout(
            yaxis=dict(title='Số báo cáo'),
            yaxis2=dict(title='Tỉ lệ hoàn thành (%)', overlaying='y', side='right', range=[0, 100]),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )
        
        # Display the chart
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Không có dữ liệu báo cáo theo đơn vị")
    
    # Recent activity
    st.markdown("## Hoạt động gần đây")
    recent_activity = db.get_recent_activity()
    if recent_activity is not None and not recent_activity.empty:
        st.dataframe(recent_activity, use_container_width=True)
    else:
        st.info("Chưa có hoạt động nào")
    
    # Reports by due date
    st.markdown("## Quản lý báo cáo theo hạn nộp")
    
    # Create tabs for different report statuses
    tab1, tab2 = st.tabs(["Báo cáo sắp đến hạn", "Báo cáo đã hết hạn"])
    
    with tab1:
        # Display upcoming reports
        upcoming_reports = db.get_assigned_reports()
        if upcoming_reports is not None and not upcoming_reports.empty:
            upcoming_df = upcoming_reports[upcoming_reports['status'] == 'pending']
            if not upcoming_df.empty:
                # Format the dataframe for display
                upcoming_df = upcoming_df[['report_name', 'organization', 'due_date', 'status']]
                upcoming_df.columns = ['Tên báo cáo', 'Đơn vị', 'Ngày hết hạn', 'Trạng thái']
                upcoming_df['Trạng thái'] = upcoming_df['Trạng thái'].map({
                    'pending': 'Chưa nộp',
                    'completed': 'Đã nộp',
                    'overdue': 'Quá hạn'
                })
                st.dataframe(upcoming_df, use_container_width=True)
            else:
                st.info("Không có báo cáo sắp đến hạn")
        else:
            st.info("Không có dữ liệu báo cáo")
    
    with tab2:
        # Display overdue reports
        overdue_reports = db.get_assigned_reports()
        if overdue_reports is not None and not overdue_reports.empty:
            overdue_df = overdue_reports[overdue_reports['status'] == 'overdue']
            if not overdue_df.empty:
                # Format the dataframe for display
                overdue_df = overdue_df[['report_name', 'organization', 'due_date', 'status']]
                overdue_df.columns = ['Tên báo cáo', 'Đơn vị', 'Ngày hết hạn', 'Trạng thái']
                overdue_df['Trạng thái'] = 'Quá hạn'
                st.dataframe(overdue_df, use_container_width=True)
            else:
                st.info("Không có báo cáo quá hạn")
        else:
            st.info("Không có dữ liệu báo cáo")

def department_dashboard():
    st.subheader("Tổng quan phòng ban")
    
    # Create columns for metrics
    col1, col2, col3 = st.columns(3)
    
    # Fetch statistics from database for this department
    dept_id = st.session_state.user_org_id
    dept_reports = db.get_department_reports(dept_id)
    pending_reports = db.get_department_reports_by_status(dept_id, "pending")
    completed_reports = db.get_department_reports_by_status(dept_id, "completed")
    
    # Display metrics
    with col1:
        st.markdown("### Tổng số báo cáo")
        st.markdown(f"<div style='text-align: center; font-size: 48px;'>📄 {dept_reports}</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("### Báo cáo đã nộp")
        st.markdown(f"<div style='text-align: center; color: #28a745; font-size: 48px;'>✓ {completed_reports}</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("### Báo cáo chưa nộp")
        st.markdown(f"<div style='text-align: center; color: #ffc107; font-size: 48px;'>⚠️ {pending_reports}</div>", unsafe_allow_html=True)
    
    # Report submission status chart
    st.markdown("## Trạng thái nộp báo cáo")
    status_data = db.get_department_report_status(dept_id)
    if status_data is not None and not status_data.empty:
        fig = px.pie(
            status_data, 
            values='count', 
            names='status', 
            color='status',
            color_discrete_map={
                'completed': '#28a745',
                'pending': '#ffc107',
                'overdue': '#dc3545'
            },
            labels={
                'status': 'Trạng thái',
                'count': 'Số lượng'
            }
        )
        
        # Map status names to Vietnamese
        fig.update_traces(
            labels=['Đã nộp' if label == 'completed' else 'Chưa nộp' if label == 'pending' else 'Quá hạn' for label in fig.data[0].labels]
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Không có dữ liệu trạng thái báo cáo")
    
    # Recent submissions
    st.markdown("## Nộp báo cáo gần đây")
    recent_submissions = db.get_department_recent_submissions(dept_id)
    if recent_submissions is not None and not recent_submissions.empty:
        # Rename columns to Vietnamese
        recent_submissions.columns = ['Đơn vị', 'Báo cáo', 'Thời gian nộp']
        st.dataframe(recent_submissions, use_container_width=True)
    else:
        st.info("Không có báo cáo được nộp gần đây")

def unit_dashboard():
    st.subheader("Tổng quan báo cáo của đơn vị")
    
    # Create columns for metrics
    col1, col2, col3 = st.columns(3)
    
    # Fetch statistics from database for this unit
    unit_id = st.session_state.user_org_id
    assigned_reports = db.get_unit_assigned_reports(unit_id)
    completed_reports = db.get_unit_reports_by_status(unit_id, "completed")
    pending_reports = db.get_unit_reports_by_status(unit_id, "pending")
    
    # Display metrics
    with col1:
        st.markdown("### Tổng số báo cáo")
        st.markdown(f"<div style='text-align: center; font-size: 48px;'>📄 {assigned_reports}</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("### Báo cáo đã nộp")
        st.markdown(f"<div style='text-align: center; color: #28a745; font-size: 48px;'>✓ {completed_reports}</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("### Báo cáo chưa nộp")
        st.markdown(f"<div style='text-align: center; color: #ffc107; font-size: 48px;'>⚠️ {pending_reports}</div>", unsafe_allow_html=True)
    
    # Report due dates
    st.markdown("## Báo cáo sắp đến hạn")
    upcoming_reports = db.get_unit_upcoming_reports(unit_id)
    if upcoming_reports is not None and not upcoming_reports.empty:
        # Rename columns to Vietnamese
        upcoming_reports.columns = ['ID', 'Tên báo cáo', 'Hạn nộp', 'Trạng thái']
        # Map status to Vietnamese
        upcoming_reports['Trạng thái'] = upcoming_reports['Trạng thái'].map({
            'pending': 'Chưa nộp',
            'completed': 'Đã nộp',
            'overdue': 'Quá hạn'
        })
        # Remove ID column for display
        upcoming_reports_display = upcoming_reports.drop(columns=['ID'])
        st.dataframe(upcoming_reports_display, use_container_width=True)
    else:
        st.info("Không có báo cáo sắp đến hạn")
    
    # Action needed reports
    st.markdown("## Báo cáo cần xử lý")
    action_needed = db.get_unit_action_needed_reports(unit_id)
    if action_needed is not None and not action_needed.empty:
        for _, report in action_needed.iterrows():
            with st.expander(f"{report['report_name']} - Hạn nộp: {report['due_date']}"):
                st.write(f"**Mô tả:** {report['description']}")
                st.write(f"**Trạng thái:** {'Chưa nộp' if report['status'] == 'pending' else 'Quá hạn' if report['status'] == 'overdue' else 'Đã nộp'}")
                
                # Add submission button
                if st.button(f"Nộp báo cáo", key=f"submit_{report['id']}"):
                    st.session_state.current_report = report['id']
                    st.session_state.current_report_name = report['report_name']
                    st.rerun()
    else:
        st.info("Không có báo cáo cần xử lý")

# Authentication
if not st.session_state.authenticated:
    auth.login_page()
else:
    # Main application
    st.sidebar.title("Vinatex Report Portal")
    
    # Sidebar menu with icons
    st.sidebar.markdown("---")
    menu_options = {
        "Tổng quan": "📊",
        "Quản lý mẫu báo cáo": "📝", 
        "Đơn vị và thành viên": "🏢",
        "Bản chức năng": "📈",
        "Quản lý người dùng": "👥",
        "Cài đặt": "⚙️"
    }
    
    # Create the menu with icons
    menu_items = []
    for option, icon in menu_options.items():
        menu_items.append(f"{icon} {option}")
    
    selected_menu = st.sidebar.radio("", menu_items)
    
    # Extract the actual option name without the icon
    selected_option = selected_menu.split(" ", 1)[1]
    
    # Map selected option to pages
    page_mapping = {
        "Tổng quan": "Dashboard",
        "Quản lý mẫu báo cáo": "Report Templates",
        "Đơn vị và thành viên": "Organizations",
        "Bản chức năng": "Assign Reports",
        "Quản lý người dùng": "Users",
        "Cài đặt": "Settings"
    }
    
    page = page_mapping.get(selected_option, "Dashboard")
    
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
    elif page == "Settings":
        st.warning("Chức năng cài đặt đang được phát triển")
    else:
        st.warning("Trang không tìm thấy")
    
    # Add user information at the bottom of the sidebar
    st.sidebar.markdown("---")
    st.sidebar.write(f"Admin Vinatex")
    st.sidebar.write(f"Quyền truy cập: {st.session_state.user_role}")
    
    # Logout button
    if st.sidebar.button("Đăng xuất"):
        auth.logout()
        st.rerun()

if __name__ == "__main__":
    # Ensure database connection is established
    db.initialize_connection()
    
    # Initialize database if needed
    import setup_database
    setup_database.initialize_database()