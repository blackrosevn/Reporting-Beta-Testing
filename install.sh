#!/bin/bash

# Vinatex Report Portal Installation Script
# For Ubuntu 22.04/24.04

echo "Vinatex Report Portal Installation"
echo "=================================="
echo

# Check if script is run as root
if [ "$(id -u)" -ne 0 ]; then
   echo "This script must be run as root" 
   exit 1
fi

# Update package lists
echo "Updating package lists..."
apt-get update

# Install PostgreSQL
echo "Installing PostgreSQL..."
apt-get install -y postgresql postgresql-contrib

# Install Python and pip
echo "Installing Python and pip..."
apt-get install -y python3 python3-pip python3-venv

# Create a directory for the application
echo "Creating application directory..."
mkdir -p /opt/vinatex-reports
cd /opt/vinatex-reports

# Copy application files to the directory
echo "Copying application files..."
cp -r $PWD/* /opt/vinatex-reports/

# Create a Python virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install required Python packages
echo "Installing Python packages..."
pip install streamlit pandas plotly psycopg2-binary openpyxl python-dotenv

# Configure PostgreSQL
echo "Configuring PostgreSQL..."
# Create database user
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'root123';"
sudo -u postgres psql -c "CREATE USER root WITH PASSWORD 'root123' SUPERUSER;"
sudo -u postgres psql -c "CREATE DATABASE vinatex_reports;"

# Initialize the database
echo "Initializing database..."
export PGUSER=root
export PGPASSWORD=root123
export PGHOST=localhost
export PGPORT=5432
export PGDATABASE=vinatex_reports

# Run database initialization script
python3 init_db.py

# Create a systemd service for the application
echo "Creating systemd service..."
cat > /etc/systemd/system/vinatex-reports.service << EOF
[Unit]
Description=Vinatex Report Portal
After=network.target postgresql.service

[Service]
User=gsm
WorkingDirectory=/opt/vinatex-reports
ExecStart=/opt/vinatex-reports/venv/bin/streamlit run app.py --server.port 5000
Restart=always
RestartSec=5
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=vinatex-reports

[Install]
WantedBy=multi-user.target
EOF

# Create gsm user if it doesn't exist
if ! id "gsm" &>/dev/null; then
    echo "Creating gsm user..."
    useradd -m -s /bin/bash gsm
    echo "gsm:gsm" | chpasswd
fi

# Set permissions
echo "Setting permissions..."
chown -R gsm:gsm /opt/vinatex-reports

# Enable and start the service
echo "Starting the service..."
systemctl daemon-reload
systemctl enable vinatex-reports.service
systemctl start vinatex-reports.service

# Display information
echo
echo "Vinatex Report Portal has been installed successfully!"
echo "The application is running at: http://localhost:5000"
echo
echo "Login credentials have been saved to: /opt/vinatex-reports/accounts.txt"
echo "Organization information: /opt/vinatex-reports/Organizations.txt"
echo "Report templates: /opt/vinatex-reports/reports.txt"
echo
echo "Database credentials:"
echo "  User: gsm"
echo "  Password: gsm"
echo "  Database: vinatex_reports"
echo
echo "System user:"
echo "  Username: gsm"
echo "  Password: gsm"
echo
echo "Installation complete!"
