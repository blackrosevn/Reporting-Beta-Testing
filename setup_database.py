import os
import psycopg2
import psycopg2.extras
import json
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import random
from datetime import datetime, timedelta
import streamlit as st
import urllib.parse

# Parse database URL from environment variables
database_url = os.getenv('DATABASE_URL')
parsed_url = urllib.parse.urlparse(database_url)
db_params = {
    'dbname': parsed_url.path[1:],
    'user': parsed_url.username,
    'password': parsed_url.password,
    'host': parsed_url.hostname,
    'port': parsed_url.port
}

def create_tables():
    """Create the necessary tables for the application."""
    # SQL for creating tables
    create_tables_sql = """
    -- Organizations table
    CREATE TABLE IF NOT EXISTS organizations (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        type VARCHAR(50) NOT NULL,  -- 'unit', 'department', 'holding', etc.
        parent_id INT,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (parent_id) REFERENCES organizations(id) ON DELETE CASCADE
    );

    -- Users table
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(100) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        role VARCHAR(50) NOT NULL,  -- 'admin', 'department', 'unit'
        organization_id INT,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE SET NULL
    );

    -- Report Templates table
    CREATE TABLE IF NOT EXISTS report_templates (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        fields TEXT NOT NULL,  -- JSON string of field names
        department_id INT,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (department_id) REFERENCES organizations(id) ON DELETE SET NULL
    );

    -- Assigned Reports table
    CREATE TABLE IF NOT EXISTS assigned_reports (
        id SERIAL PRIMARY KEY,
        template_id INT NOT NULL,
        organization_id INT NOT NULL,
        due_date DATE NOT NULL,
        status VARCHAR(50) NOT NULL,  -- 'pending', 'completed', 'overdue'
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (template_id) REFERENCES report_templates(id) ON DELETE CASCADE,
        FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
    );

    -- Report Submissions table
    CREATE TABLE IF NOT EXISTS report_submissions (
        id SERIAL PRIMARY KEY,
        assigned_report_id INT NOT NULL,
        data TEXT NOT NULL,  -- JSON string of field values
        submitted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (assigned_report_id) REFERENCES assigned_reports(id) ON DELETE CASCADE
    );
    """
    
    # Connect to the database and create tables
    conn = None
    try:
        conn = psycopg2.connect(**db_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute(create_tables_sql)
        print("Tables created successfully")
        
        cursor.close()
        return True
    except Exception as e:
        print(f"Error creating tables: {e}")
        return False
    finally:
        if conn is not None:
            conn.close()

def create_sample_data():
    """Create sample organizations, users, report templates, and assigned reports."""
    conn = None
    try:
        conn = psycopg2.connect(**db_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Insert sample organizations
        sample_organizations_sql = """
        -- Holding company
        INSERT INTO organizations (name, type, parent_id)
        VALUES ('Vinatex', 'holding', NULL);

        -- Departments
        INSERT INTO organizations (name, type, parent_id)
        SELECT 'Ban Tài chính - Kế toán', 'department', id FROM organizations WHERE name = 'Vinatex';
        INSERT INTO organizations (name, type, parent_id)
        SELECT 'Ban Nhân sự', 'department', id FROM organizations WHERE name = 'Vinatex';
        INSERT INTO organizations (name, type, parent_id)
        SELECT 'Ban Sợi', 'department', id FROM organizations WHERE name = 'Vinatex';
        INSERT INTO organizations (name, type, parent_id)
        SELECT 'Ban May', 'department', id FROM organizations WHERE name = 'Vinatex';
        INSERT INTO organizations (name, type, parent_id)
        SELECT 'Ban Đầu tư', 'department', id FROM organizations WHERE name = 'Vinatex';

        -- Member units
        INSERT INTO organizations (name, type, parent_id)
        SELECT 'Tổng Công ty CP May Hưng Yên', 'unit', id FROM organizations WHERE name = 'Vinatex';
        INSERT INTO organizations (name, type, parent_id)
        SELECT 'Tổng Công ty CP Dệt May Hòa Thọ', 'unit', id FROM organizations WHERE name = 'Vinatex';
        INSERT INTO organizations (name, type, parent_id)
        SELECT 'Tổng Công ty May 10 - CTCP', 'unit', id FROM organizations WHERE name = 'Vinatex';
        INSERT INTO organizations (name, type, parent_id)
        SELECT 'Tổng Công ty CP May Đáp Cầu', 'unit', id FROM organizations WHERE name = 'Vinatex';
        INSERT INTO organizations (name, type, parent_id)
        SELECT 'Tổng Công ty CP Dệt May Nam Định', 'unit', id FROM organizations WHERE name = 'Vinatex';
        """
        cursor.execute(sample_organizations_sql)
        
        # Insert sample users
        sample_users_sql = """
        -- Admin user
        INSERT INTO users (username, password, role, organization_id)
        SELECT 'admin', 'admin123', 'admin', id FROM organizations WHERE name = 'Vinatex';

        -- Department users
        INSERT INTO users (username, password, role, organization_id)
        SELECT 'finance', 'finance123', 'department', id FROM organizations WHERE name = 'Ban Tài chính - Kế toán';
        INSERT INTO users (username, password, role, organization_id)
        SELECT 'hr', 'hr123', 'department', id FROM organizations WHERE name = 'Ban Nhân sự';
        INSERT INTO users (username, password, role, organization_id)
        SELECT 'yarn', 'yarn123', 'department', id FROM organizations WHERE name = 'Ban Sợi';
        INSERT INTO users (username, password, role, organization_id)
        SELECT 'garment', 'garment123', 'department', id FROM organizations WHERE name = 'Ban May';

        -- Unit users
        INSERT INTO users (username, password, role, organization_id)
        SELECT 'hungyen', 'hungyen123', 'unit', id FROM organizations WHERE name = 'Tổng Công ty CP May Hưng Yên';
        INSERT INTO users (username, password, role, organization_id)
        SELECT 'hoatho', 'hoatho123', 'unit', id FROM organizations WHERE name = 'Tổng Công ty CP Dệt May Hòa Thọ';
        INSERT INTO users (username, password, role, organization_id)
        SELECT 'may10', 'may10123', 'unit', id FROM organizations WHERE name = 'Tổng Công ty May 10 - CTCP';
        INSERT INTO users (username, password, role, organization_id)
        SELECT 'dapcau', 'dapcau123', 'unit', id FROM organizations WHERE name = 'Tổng Công ty CP May Đáp Cầu';
        INSERT INTO users (username, password, role, organization_id)
        SELECT 'namdinh', 'namdinh123', 'unit', id FROM organizations WHERE name = 'Tổng Công ty CP Dệt May Nam Định';
        """
        cursor.execute(sample_users_sql)
        
        # Create sample report templates
        create_sample_report_templates(cursor)
        
        # Create sample assigned reports
        create_sample_assigned_reports(cursor)
        
        # Create accounts file
        create_accounts_file()
        
        # Create organizations file
        create_organizations_file()
        
        # Create reports file
        create_reports_file()
        
        cursor.close()
        return True
    except Exception as e:
        print(f"Error creating sample data: {e}")
        return False
    finally:
        if conn is not None:
            conn.close()

def create_sample_report_templates(cursor):
    """Create sample report templates with fields."""
    # Get department IDs
    cursor.execute("SELECT id, name FROM organizations WHERE type = 'department'")
    departments = {row[1]: row[0] for row in cursor.fetchall()}
    
    # Financial report template
    financial_fields = json.dumps([
        "Revenue (VND)",
        "Expenses (VND)",
        "Profit (VND)",
        "Accounts Receivable (VND)",
        "Accounts Payable (VND)",
        "Cash Flow (VND)"
    ])
    cursor.execute(
        "INSERT INTO report_templates (name, description, fields, department_id) VALUES (%s, %s, %s, %s)",
        ("Báo cáo tài chính", "Báo cáo tài chính hàng quý của đơn vị", financial_fields, departments["Ban Tài chính - Kế toán"])
    )
    
    # HR report template
    hr_fields = json.dumps([
        "Total Employees",
        "New Hires",
        "Terminations",
        "Turnover Rate (%)",
        "Training Hours",
        "Labor Cost (VND)"
    ])
    cursor.execute(
        "INSERT INTO report_templates (name, description, fields, department_id) VALUES (%s, %s, %s, %s)",
        ("Báo cáo Nhân sự", "Báo cáo tình hình nhân sự định kỳ", hr_fields, departments["Ban Nhân sự"])
    )
    
    # Yarn production report template
    yarn_fields = json.dumps([
        "Production Volume (kg)",
        "Production Capacity (%)",
        "Raw Material Cost (VND/kg)",
        "Energy Consumption (kWh)",
        "Quality Metrics (%)",
        "Inventory Level (kg)"
    ])
    cursor.execute(
        "INSERT INTO report_templates (name, description, fields, department_id) VALUES (%s, %s, %s, %s)",
        ("Báo cáo tình hình SXKD Ban Sợi", "Báo cáo sản xuất kinh doanh ngành sợi", yarn_fields, departments["Ban Sợi"])
    )
    
    # Garment production report template
    garment_fields = json.dumps([
        "Production Volume (pieces)",
        "Production Capacity (%)",
        "Material Cost (VND/piece)",
        "Labor Productivity (pieces/person)",
        "Quality Metrics (%)",
        "Inventory Level (pieces)"
    ])
    cursor.execute(
        "INSERT INTO report_templates (name, description, fields, department_id) VALUES (%s, %s, %s, %s)",
        ("Báo cáo tình hình SXKD Ban May", "Báo cáo sản xuất kinh doanh ngành may", garment_fields, departments["Ban May"])
    )
    
    # Production report template
    production_fields = json.dumps([
        "Production Plan Completion (%)",
        "Production Volume",
        "Production Value (VND)",
        "Defect Rate (%)",
        "Operating Hours",
        "Downtime Hours"
    ])
    cursor.execute(
        "INSERT INTO report_templates (name, description, fields, department_id) VALUES (%s, %s, %s, %s)",
        ("Báo cáo sản xuất", "Báo cáo tình hình sản xuất chung", production_fields, departments["Ban Đầu tư"])
    )

def create_sample_assigned_reports(cursor):
    """Create sample assigned reports for units."""
    # Get template IDs
    cursor.execute("SELECT id, name FROM report_templates")
    templates = {row[1]: row[0] for row in cursor.fetchall()}
    
    # Get unit IDs
    cursor.execute("SELECT id, name FROM organizations WHERE type = 'unit'")
    units = {row[1]: row[0] for row in cursor.fetchall()}
    
    # Current date for reference
    current_date = datetime.now().date()
    
    # Create sample assignments with different due dates and statuses
    sample_assignments = [
        # Financial reports
        (templates["Báo cáo tài chính"], units["Tổng Công ty CP May Hưng Yên"], 
         current_date + timedelta(days=15), "pending"),
        (templates["Báo cáo tài chính"], units["Tổng Công ty CP Dệt May Hòa Thọ"], 
         current_date + timedelta(days=15), "pending"),
        (templates["Báo cáo tài chính"], units["Tổng Công ty May 10 - CTCP"], 
         current_date - timedelta(days=5), "completed"),
        
        # HR reports
        (templates["Báo cáo Nhân sự"], units["Tổng Công ty CP May Hưng Yên"], 
         current_date + timedelta(days=10), "pending"),
        (templates["Báo cáo Nhân sự"], units["Tổng Công ty CP Dệt May Nam Định"], 
         current_date - timedelta(days=2), "completed"),
        
        # Yarn reports
        (templates["Báo cáo tình hình SXKD Ban Sợi"], units["Tổng Công ty CP Dệt May Hòa Thọ"], 
         current_date + timedelta(days=7), "pending"),
        (templates["Báo cáo tình hình SXKD Ban Sợi"], units["Tổng Công ty CP Dệt May Nam Định"], 
         current_date + timedelta(days=7), "pending"),
        
        # Garment reports
        (templates["Báo cáo tình hình SXKD Ban May"], units["Tổng Công ty CP May Hưng Yên"], 
         current_date - timedelta(days=3), "completed"),
        (templates["Báo cáo tình hình SXKD Ban May"], units["Tổng Công ty May 10 - CTCP"], 
         current_date + timedelta(days=5), "pending"),
        (templates["Báo cáo tình hình SXKD Ban May"], units["Tổng Công ty CP May Đáp Cầu"], 
         current_date - timedelta(days=10), "completed"),
        
        # Production reports
        (templates["Báo cáo sản xuất"], units["Tổng Công ty CP May Hưng Yên"], 
         current_date + timedelta(days=20), "pending"),
        (templates["Báo cáo sản xuất"], units["Tổng Công ty CP Dệt May Hòa Thọ"], 
         current_date - timedelta(days=1), "completed"),
        (templates["Báo cáo sản xuất"], units["Tổng Công ty May 10 - CTCP"], 
         current_date + timedelta(days=20), "pending"),
        (templates["Báo cáo sản xuất"], units["Tổng Công ty CP May Đáp Cầu"], 
         current_date + timedelta(days=20), "pending"),
        (templates["Báo cáo sản xuất"], units["Tổng Công ty CP Dệt May Nam Định"], 
         current_date - timedelta(days=15), "completed"),
    ]
    
    # Insert assignments
    for template_id, unit_id, due_date, status in sample_assignments:
        cursor.execute(
            "INSERT INTO assigned_reports (template_id, organization_id, due_date, status) VALUES (%s, %s, %s, %s) RETURNING id",
            (template_id, unit_id, due_date, status)
        )
        
        # If status is completed, create a submission
        if status == "completed":
            assigned_report_id = cursor.fetchone()[0]
            
            # Get template fields
            cursor.execute("SELECT fields FROM report_templates WHERE id = %s", (template_id,))
            fields = json.loads(cursor.fetchone()[0])
            
            # Create sample data for submission
            sample_data = {}
            for field in fields:
                if "VND" in field:
                    sample_data[field] = f"{random.randint(100000, 10000000):,} VND"
                elif "%" in field:
                    sample_data[field] = f"{random.uniform(70, 99):.2f}%"
                elif any(keyword in field for keyword in ["Volume", "Level", "Inventory"]):
                    sample_data[field] = f"{random.randint(1000, 50000):,}"
                elif "Hours" in field:
                    sample_data[field] = f"{random.randint(100, 2000):,}"
                elif "Employees" in field or "Hires" in field or "Terminations" in field:
                    sample_data[field] = f"{random.randint(50, 500):,}"
                else:
                    sample_data[field] = f"{random.uniform(10, 100):.2f}"
            
            # Insert submission
            cursor.execute(
                "INSERT INTO report_submissions (assigned_report_id, data) VALUES (%s, %s)",
                (assigned_report_id, json.dumps(sample_data))
            )
        else:
            cursor.fetchone()  # Consume the returned ID

def create_accounts_file():
    """Create accounts.txt file with login credentials."""
    with open("accounts.txt", "w") as f:
        f.write("Vinatex Report Portal - Account Information\n")
        f.write("=========================================\n\n")
        
        f.write("Admin Access:\n")
        f.write("Username: admin\n")
        f.write("Password: admin123\n\n")
        
        f.write("Department Access:\n")
        f.write("1. Finance Department\n")
        f.write("   Username: finance\n")
        f.write("   Password: finance123\n\n")
        
        f.write("2. HR Department\n")
        f.write("   Username: hr\n")
        f.write("   Password: hr123\n\n")
        
        f.write("3. Yarn Department\n")
        f.write("   Username: yarn\n")
        f.write("   Password: yarn123\n\n")
        
        f.write("4. Garment Department\n")
        f.write("   Username: garment\n")
        f.write("   Password: garment123\n\n")
        
        f.write("Member Units Access:\n")
        f.write("1. Tổng Công ty CP May Hưng Yên\n")
        f.write("   Username: hungyen\n")
        f.write("   Password: hungyen123\n\n")
        
        f.write("2. Tổng Công ty CP Dệt May Hòa Thọ\n")
        f.write("   Username: hoatho\n")
        f.write("   Password: hoatho123\n\n")
        
        f.write("3. Tổng Công ty May 10 - CTCP\n")
        f.write("   Username: may10\n")
        f.write("   Password: may10123\n\n")
        
        f.write("4. Tổng Công ty CP May Đáp Cầu\n")
        f.write("   Username: dapcau\n")
        f.write("   Password: dapcau123\n\n")
        
        f.write("5. Tổng Công ty CP Dệt May Nam Định\n")
        f.write("   Username: namdinh\n")
        f.write("   Password: namdinh123\n\n")
        
        f.write("Database Credentials:\n")
        f.write(f"Database URL: {database_url}\n")

def create_organizations_file():
    """Create Organizations.txt file with organization information."""
    with open("Organizations.txt", "w") as f:
        f.write("Vinatex Report Portal - Organizations Information\n")
        f.write("=============================================\n\n")
        
        f.write("Holding Company:\n")
        f.write("- Vinatex (Tập đoàn Dệt May Việt Nam)\n\n")
        
        f.write("Functional Departments:\n")
        f.write("1. Ban Tài chính - Kế toán\n")
        f.write("2. Ban Nhân sự\n")
        f.write("3. Ban Sợi\n")
        f.write("4. Ban May\n")
        f.write("5. Ban Đầu tư\n\n")
        
        f.write("Member Units:\n")
        f.write("1. Tổng Công ty CP May Hưng Yên\n")
        f.write("2. Tổng Công ty CP Dệt May Hòa Thọ\n")
        f.write("3. Tổng Công ty May 10 - CTCP\n")
        f.write("4. Tổng Công ty CP May Đáp Cầu\n")
        f.write("5. Tổng Công ty CP Dệt May Nam Định\n")

def create_reports_file():
    """Create reports.txt file with report template information."""
    with open("reports.txt", "w") as f:
        f.write("Vinatex Report Portal - Report Templates\n")
        f.write("=====================================\n\n")
        
        f.write("1. Báo cáo tài chính\n")
        f.write("   Department: Ban Tài chính - Kế toán\n")
        f.write("   Description: Báo cáo tài chính hàng quý của đơn vị\n")
        f.write("   Fields:\n")
        f.write("     - Revenue (VND)\n")
        f.write("     - Expenses (VND)\n")
        f.write("     - Profit (VND)\n")
        f.write("     - Accounts Receivable (VND)\n")
        f.write("     - Accounts Payable (VND)\n")
        f.write("     - Cash Flow (VND)\n\n")
        
        f.write("2. Báo cáo Nhân sự\n")
        f.write("   Department: Ban Nhân sự\n")
        f.write("   Description: Báo cáo tình hình nhân sự định kỳ\n")
        f.write("   Fields:\n")
        f.write("     - Total Employees\n")
        f.write("     - New Hires\n")
        f.write("     - Terminations\n")
        f.write("     - Turnover Rate (%)\n")
        f.write("     - Training Hours\n")
        f.write("     - Labor Cost (VND)\n\n")
        
        f.write("3. Báo cáo tình hình SXKD Ban Sợi\n")
        f.write("   Department: Ban Sợi\n")
        f.write("   Description: Báo cáo sản xuất kinh doanh ngành sợi\n")
        f.write("   Fields:\n")
        f.write("     - Production Volume (kg)\n")
        f.write("     - Production Capacity (%)\n")
        f.write("     - Raw Material Cost (VND/kg)\n")
        f.write("     - Energy Consumption (kWh)\n")
        f.write("     - Quality Metrics (%)\n")
        f.write("     - Inventory Level (kg)\n\n")
        
        f.write("4. Báo cáo tình hình SXKD Ban May\n")
        f.write("   Department: Ban May\n")
        f.write("   Description: Báo cáo sản xuất kinh doanh ngành may\n")
        f.write("   Fields:\n")
        f.write("     - Production Volume (pieces)\n")
        f.write("     - Production Capacity (%)\n")
        f.write("     - Material Cost (VND/piece)\n")
        f.write("     - Labor Productivity (pieces/person)\n")
        f.write("     - Quality Metrics (%)\n")
        f.write("     - Inventory Level (pieces)\n\n")
        
        f.write("5. Báo cáo sản xuất\n")
        f.write("   Department: Ban Đầu tư\n")
        f.write("   Description: Báo cáo tình hình sản xuất chung\n")
        f.write("   Fields:\n")
        f.write("     - Production Plan Completion (%)\n")
        f.write("     - Production Volume\n")
        f.write("     - Production Value (VND)\n")
        f.write("     - Defect Rate (%)\n")
        f.write("     - Operating Hours\n")
        f.write("     - Downtime Hours\n")

def check_tables_exist():
    """Check if the required tables exist in the database."""
    conn = None
    try:
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        # Check if users table exists and has data
        cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'users'
        )
        """)
        users_table_exists = cursor.fetchone()[0]
        
        if users_table_exists:
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            return user_count > 0
        
        return False
    except Exception as e:
        print(f"Error checking tables: {e}")
        return False
    finally:
        if conn is not None:
            conn.close()

def initialize_database():
    """Initialize the database with tables and sample data."""
    # Check if tables already exist with data
    if check_tables_exist():
        st.write("Database already initialized.")
        return True
    
    # Create tables
    if not create_tables():
        st.error("Failed to create tables")
        return False
    
    # Create sample data
    if not create_sample_data():
        st.error("Failed to create sample data")
        return False
    
    st.success("Database initialized successfully!")
    return True

if __name__ == "__main__":
    initialize_database()