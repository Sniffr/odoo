# Complete Guide to Self-Hosted Odoo Setup with Multi-Tenancy and Module Management

## Table of Contents
1. [Introduction](#introduction)
2. [Server Requirements](#server-requirements)
3. [Installation Methods](#installation-methods)
4. [Docker Setup (Recommended)](#docker-setup-recommended)
5. [Manual Installation](#manual-installation)
6. [Multi-Tenancy Configuration](#multi-tenancy-configuration)
7. [Module Management](#module-management)
8. [Security Configuration](#security-configuration)
9. [Performance Optimization](#performance-optimization)
10. [Backup and Maintenance](#backup-and-maintenance)
11. [Troubleshooting](#troubleshooting)

## Introduction

Odoo is a comprehensive open-source ERP (Enterprise Resource Planning) platform that offers a wide range of business applications. This guide covers the best practices for setting up Odoo self-hosted with multi-tenancy support and module management.

### Key Benefits of Self-Hosted Odoo:
- Complete control over your data and infrastructure
- Cost-effective for multiple clients/tenants
- Customizable and scalable
- Enhanced security and compliance
- No vendor lock-in

## Server Requirements

### Minimum Requirements
- **CPU**: 2 vCPUs (4+ recommended for production)
- **RAM**: 4 GB (8+ GB recommended)
- **Storage**: 50 GB SSD (100+ GB recommended)
- **OS**: Ubuntu 20.04/22.04/24.04 LTS, CentOS 7/8, or Debian 10/11

### Recommended Production Setup
- **CPU**: 8+ vCPUs
- **RAM**: 16+ GB
- **Storage**: 200+ GB SSD with RAID configuration
- **Network**: High-speed internet with static IP
- **Backup**: Automated backup solution

### Software Dependencies
- Python 3.8+ (3.10+ recommended)
- PostgreSQL 12+ (15+ recommended)
- Nginx (reverse proxy)
- Redis (optional, for performance)
- Docker & Docker Compose (for containerized setup)

## Installation Methods

### Method 1: Docker Setup (Recommended)

Docker provides the most reliable and maintainable setup for Odoo with multi-tenancy support.

#### Prerequisites
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin -y
```

#### Docker Compose Configuration

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: postgres
      POSTGRES_USER: odoo
      POSTGRES_PASSWORD: odoo_password
      PGDATA: /var/lib/postgresql/data/pgdata
    volumes:
      - odoo-db-data:/var/lib/postgresql/data/pgdata
    ports:
      - "5432:5432"
    restart: unless-stopped

  odoo:
    image: odoo:18.0
    depends_on:
      - db
    ports:
      - "8069:8069"
      - "8072:8072"
    environment:
      - HOST=db
      - USER=odoo
      - PASSWORD=odoo_password
    volumes:
      - odoo-web-data:/var/lib/odoo
      - ./config:/etc/odoo
      - ./addons:/mnt/extra-addons
      - ./logs:/var/log/odoo
    restart: unless-stopped
    command: ["odoo", "--config=/etc/odoo/odoo.conf"]

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/conf.d:/etc/nginx/conf.d
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - odoo
    restart: unless-stopped

volumes:
  odoo-web-data:
  odoo-db-data:
```

#### Odoo Configuration File

Create `config/odoo.conf`:

```ini
[options]
; Database settings
db_host = db
db_port = 5432
db_user = odoo
db_password = odoo_password
db_name = False
db_template = template0

; Server settings
http_port = 8069
longpolling_port = 8072
workers = 4
max_cron_threads = 2

; Multi-tenancy settings
dbfilter = ^%d$
list_db = True
proxy_mode = True

; Logging
log_level = info
log_handler = :INFO
logfile = /var/log/odoo/odoo.log

; Performance
limit_memory_hard = 2684354560
limit_memory_soft = 2147483648
limit_request = 8192
limit_time_cpu = 600
limit_time_real = 1200

; Security
admin_passwd = admin_password_here
```

#### Nginx Configuration

Create `nginx/conf.d/odoo.conf`:

```nginx
upstream odoo {
    server odoo:8069;
}

upstream odoochat {
    server odoo:8072;
}

server {
    listen 80;
    server_name your-domain.com *.your-domain.com;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Proxy settings
    proxy_read_timeout 720s;
    proxy_connect_timeout 720s;
    proxy_send_timeout 720s;
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Real-IP $remote_addr;
    
    # Gzip compression
    gzip on;
    gzip_types text/css text/less text/plain text/xml application/xml application/json application/javascript;
    
    # Main location
    location / {
        proxy_redirect off;
        proxy_pass http://odoo;
    }
    
    # Long polling
    location /longpolling {
        proxy_pass http://odoochat;
    }
    
    # Static files
    location ~* /web/static/ {
        proxy_cache_valid 200 90m;
        proxy_buffering on;
        expires 864000;
        proxy_pass http://odoo;
    }
}
```

### Method 2: Manual Installation

#### Step 1: Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3 python3-pip python3-dev python3-venv python3-wheel \
    build-essential wget git libfreetype-dev libxml2-dev libzip-dev \
    libldap2-dev libsasl2-dev python3-setuptools node-less libjpeg-dev \
    zlib1g-dev libpq-dev libxslt1-dev libldap2-dev libtiff-dev \
    libjpeg8-dev libopenjp2-7-dev liblcms2-dev libwebp-dev \
    libharfbuzz-dev libfribidi-dev libxcb1-dev -y

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Create PostgreSQL user
sudo su - postgres -c "createuser -s odoo"
```

#### Step 2: Install Wkhtmltopdf

```bash
# Download and install wkhtmltopdf
wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/wkhtmltox_0.12.6.1-3.jammy_amd64.deb
sudo dpkg -i wkhtmltox_0.12.6.1-3.jammy_amd64.deb
sudo apt --fix-broken install
```

#### Step 3: Install Odoo

```bash
# Create system user
sudo useradd -m -d /opt/odoo -U -r -s /bin/bash odoo

# Download Odoo
cd /opt
sudo git clone https://www.github.com/odoo/odoo --depth 1 --branch 18.0 odoo

# Set permissions
sudo chown -R odoo:odoo /opt/odoo

# Create virtual environment
sudo su - odoo
cd /opt/odoo
python3 -m venv odoo-venv
source odoo-venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

#### Step 4: Create Odoo Configuration

```bash
sudo mkdir /etc/odoo
sudo touch /etc/odoo/odoo.conf
sudo chown odoo:odoo /etc/odoo/odoo.conf
```

Add configuration to `/etc/odoo/odoo.conf`:

```ini
[options]
; Database settings
db_host = False
db_port = False
db_user = odoo
db_password = False
db_name = False
db_template = template0

; Server settings
http_port = 8069
longpolling_port = 8072
workers = 4
max_cron_threads = 2

; Multi-tenancy settings
dbfilter = ^%d$
list_db = True
proxy_mode = True

; Paths
addons_path = /opt/odoo/addons,/opt/odoo/odoo/addons
data_dir = /var/lib/odoo

; Logging
log_level = info
log_handler = :INFO
logfile = /var/log/odoo/odoo.log

; Performance
limit_memory_hard = 2684354560
limit_memory_soft = 2147483648
limit_request = 8192
limit_time_cpu = 600
limit_time_real = 1200

; Security
admin_passwd = admin_password_here
```

#### Step 5: Create Systemd Service

Create `/etc/systemd/system/odoo.service`:

```ini
[Unit]
Description=Odoo
After=postgresql.service

[Service]
Type=simple
SyslogIdentifier=odoo
PermissionsStartOnly=true
User=odoo
Group=odoo
ExecStart=/opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo-bin -c /etc/odoo/odoo.conf
StandardOutput=journal+console

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable odoo
sudo systemctl start odoo
```

## Multi-Tenancy Configuration

### Database Filter Configuration

Multi-tenancy in Odoo is achieved through database filtering. Each tenant gets their own database, and Odoo routes requests based on the domain.

#### Domain-Based Routing

```ini
# In odoo.conf
dbfilter = ^%d$  # Uses subdomain as database name
# Examples:
# client1.yourdomain.com -> client1 database
# client2.yourdomain.com -> client2 database
```

#### Alternative Filtering Options

```ini
# Filter by database name pattern
dbfilter = ^mycompany.*$

# Filter by specific subdomain
dbfilter = ^[a-zA-Z0-9-]+\.yourdomain\.com$

# Show all databases (development only)
dbfilter = .*
```

### Creating Tenant Databases

#### Method 1: Through Odoo Interface

1. Access the database manager at `http://your-domain.com/web/database/manager`
2. Click "Create Database"
3. Enter database name (should match subdomain)
4. Set master password
5. Configure language and country

#### Method 2: Command Line

```bash
# Create database via command line
sudo su - postgres
createdb -O odoo client1_db
createdb -O odoo client2_db
exit

# Initialize database with Odoo
sudo su - odoo
cd /opt/odoo
./odoo-bin -d client1_db -i base --stop-after-init
./odoo-bin -d client2_db -i base --stop-after-init
```

### DNS Configuration

Configure your DNS to point subdomains to your server:

```
# A records
yourdomain.com          A    YOUR_SERVER_IP
*.yourdomain.com        A    YOUR_SERVER_IP

# Or CNAME records
client1.yourdomain.com  CNAME yourdomain.com
client2.yourdomain.com  CNAME yourdomain.com
```

### Nginx Multi-Tenant Configuration

Update your Nginx configuration to handle multiple tenants:

```nginx
# Main server block
server {
    listen 80;
    server_name yourdomain.com *.yourdomain.com;
    
    # Proxy to Odoo
    location / {
        proxy_pass http://odoo:8069;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# SSL configuration (after obtaining certificates)
server {
    listen 443 ssl http2;
    server_name yourdomain.com *.yourdomain.com;
    
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    location / {
        proxy_pass http://odoo:8069;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Module Management

### Installing Official Modules

#### Through Odoo Interface

1. Go to Apps menu
2. Search for desired module
3. Click "Install" or "Upgrade"
4. Wait for installation to complete

#### Command Line Installation

```bash
# Install specific module
sudo su - odoo
cd /opt/odoo
./odoo-bin -d database_name -i module_name --stop-after-init

# Install multiple modules
./odoo-bin -d database_name -i module1,module2,module3 --stop-after-init

# Update modules
./odoo-bin -d database_name -u module_name --stop-after-init
```

### Installing Custom Modules

#### Method 1: Addons Directory

1. Place module in `/opt/odoo/addons/` or `/mnt/extra-addons/` (Docker)
2. Update addons list: Apps → Update Apps List
3. Install from Apps menu

#### Method 2: Odoo CLI

```bash
# Install from specific path
./odoo-bin -d database_name -i custom_module --addons-path=/path/to/modules --stop-after-init
```

### Creating Custom Modules

#### Module Structure

```
my_custom_module/
├── __manifest__.py
├── __init__.py
├── models/
│   ├── __init__.py
│   └── my_model.py
├── views/
│   └── my_model_views.xml
├── security/
│   └── ir.model.access.csv
└── static/
    └── description/
        └── icon.png
```

#### Manifest File (`__manifest__.py`)

```python
{
    'name': 'My Custom Module',
    'version': '1.0.0',
    'category': 'Custom',
    'summary': 'Custom functionality for Odoo',
    'description': """
        Detailed description of the module functionality
    """,
    'author': 'Your Name',
    'website': 'https://yourwebsite.com',
    'depends': ['base', 'sale', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/my_model_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
    'module_type': 'official',  # Important for custom modules
}
```

#### Model Definition (`models/my_model.py`)

```python
from odoo import models, fields, api

class MyModel(models.Model):
    _name = 'my.model'
    _description = 'My Custom Model'
    _order = 'name'
    
    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    partner_id = fields.Many2one('res.partner', string='Partner')
    amount = fields.Float(string='Amount', digits=(16, 2))
    date = fields.Date(string='Date', default=fields.Date.today)
    
    @api.model
    def create(self, vals):
        # Custom logic before creation
        return super(MyModel, self).create(vals)
    
    def write(self, vals):
        # Custom logic before update
        return super(MyModel, self).write(vals)
```

#### View Definition (`views/my_model_views.xml`)

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_my_model_tree" model="ir.ui.view">
        <field name="name">my.model.tree</field>
        <field name="model">my.model</field>
        <field name="arch" type="xml">
            <tree string="My Models">
                <field name="name"/>
                <field name="partner_id"/>
                <field name="amount"/>
                <field name="date"/>
            </tree>
        </field>
    </record>

    <record id="view_my_model_form" model="ir.ui.view">
        <field name="name">my.model.form</field>
        <field name="model">my.model</field>
        <field name="arch" type="xml">
            <form string="My Model">
                <sheet>
                    <group>
                        <group>
                            <field name="name"/>
                            <field name="partner_id"/>
                        </group>
                        <group>
                            <field name="amount"/>
                            <field name="date"/>
                        </group>
                    </group>
                    <group>
                        <field name="description"/>
                    </group>
                </sheet>
            </form>
        </field>
    </record>

    <menuitem id="menu_my_model_root" name="My Module" sequence="10"/>
    <menuitem id="menu_my_model" name="My Models" parent="menu_my_model_root" action="action_my_model" sequence="10"/>

    <record id="action_my_model" model="ir.actions.act_window">
        <field name="name">My Models</field>
        <field name="res_model">my.model</field>
        <field name="view_mode">tree,form</field>
    </record>
</odoo>
```

#### Security Rules (`security/ir.model.access.csv`)

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_my_model_user,my.model.user,model_my_model,base.group_user,1,1,1,1
access_my_model_manager,my.model.manager,model_my_model,base.group_system,1,1,1,1
```

### Module Development Best Practices

1. **Version Control**: Use Git for module development
2. **Testing**: Write unit tests for your modules
3. **Documentation**: Document your code and create user guides
4. **Dependencies**: Clearly define module dependencies
5. **Data Migration**: Handle data migration between versions
6. **Security**: Implement proper access controls
7. **Performance**: Optimize database queries and views

### Module Installation Troubleshooting

#### Common Issues and Solutions

1. **Module not appearing in Apps list**:
   - Check if module is in correct addons path
   - Verify `__manifest__.py` syntax
   - Update Apps List

2. **Installation errors**:
   - Check dependencies are installed
   - Verify database permissions
   - Check log files for detailed errors

3. **Custom module download error**:
   - Add `'module_type': 'official'` to manifest
   - Use list view instead of kanban view
   - Install via command line

## Security Configuration

### SSL/TLS Setup

#### Using Let's Encrypt (Free)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com -d *.yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### Manual SSL Certificate

```bash
# Place certificates in nginx directory
sudo mkdir -p /etc/nginx/ssl
sudo cp your-certificate.crt /etc/nginx/ssl/
sudo cp your-private-key.key /etc/nginx/ssl/
```

### Firewall Configuration

```bash
# Install UFW
sudo apt install ufw -y

# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Database Security

```bash
# Secure PostgreSQL
sudo -u postgres psql
ALTER USER odoo PASSWORD 'strong_password';
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO odoo;
GRANT CREATE ON SCHEMA public TO odoo;
\q
```

### Odoo Security Settings

```ini
# In odoo.conf
admin_passwd = very_strong_admin_password
proxy_mode = True
dbfilter = ^%d$  # Restrict database access by domain
```

## Performance Optimization

### Database Optimization

```sql
-- PostgreSQL configuration optimizations
-- In /etc/postgresql/15/main/postgresql.conf

shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
```

### Odoo Performance Settings

```ini
# In odoo.conf
workers = 4  # Number of worker processes
max_cron_threads = 2  # Cron job threads
limit_memory_hard = 2684354560  # 2.5GB
limit_memory_soft = 2147483648  # 2GB
limit_request = 8192
limit_time_cpu = 600
limit_time_real = 1200
```

### Redis Caching (Optional)

```yaml
# Add to docker-compose.yml
redis:
  image: redis:alpine
  ports:
    - "6379:6379"
  volumes:
    - redis-data:/data
  restart: unless-stopped

volumes:
  redis-data:
```

```ini
# In odoo.conf
enable_redis = True
redis_host = redis
redis_port = 6379
redis_dbindex = 0
```

### Nginx Caching

```nginx
# Add to nginx configuration
location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    proxy_pass http://odoo:8069;
}
```

## Backup and Maintenance

### Automated Backup Script

Create `/opt/backup_odoo.sh`:

```bash
#!/bin/bash

# Configuration
BACKUP_DIR="/opt/backups"
ODOO_DB="your_database"
ODOO_USER="odoo"
DB_HOST="localhost"
DB_PORT="5432"
RETENTION_DAYS=30

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
pg_dump -h $DB_HOST -p $DB_PORT -U $ODOO_USER $ODOO_DB > $BACKUP_DIR/odoo_$(date +%Y%m%d_%H%M%S).sql

# File system backup
tar -czf $BACKUP_DIR/odoo_files_$(date +%Y%m%d_%H%M%S).tar.gz /var/lib/odoo

# Cleanup old backups
find $BACKUP_DIR -name "*.sql" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $(date)"
```

Make executable and schedule:

```bash
chmod +x /opt/backup_odoo.sh

# Add to crontab
crontab -e
# Add: 0 2 * * * /opt/backup_odoo.sh
```

### Database Maintenance

```bash
# Regular database maintenance
sudo su - postgres
psql -d your_database -c "VACUUM ANALYZE;"
psql -d your_database -c "REINDEX DATABASE your_database;"
```

### Log Rotation

Create `/etc/logrotate.d/odoo`:

```
/var/log/odoo/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 odoo odoo
    postrotate
        systemctl reload odoo
    endscript
}
```

## Troubleshooting

### Common Issues

#### 1. Odoo Won't Start

```bash
# Check service status
sudo systemctl status odoo

# Check logs
sudo journalctl -u odoo -f
tail -f /var/log/odoo/odoo.log

# Check configuration
sudo -u odoo /opt/odoo/odoo-bin -c /etc/odoo/odoo.conf --test-enable
```

#### 2. Database Connection Issues

```bash
# Test PostgreSQL connection
sudo -u postgres psql -c "SELECT version();"

# Check Odoo database access
sudo -u odoo psql -h localhost -U odoo -d postgres -c "SELECT current_database();"
```

#### 3. Module Installation Errors

```bash
# Check module syntax
python3 -m py_compile /path/to/module/__manifest__.py

# Install with debug mode
./odoo-bin -d database_name -i module_name --log-level=debug
```

#### 4. Performance Issues

```bash
# Monitor system resources
htop
iotop
free -h
df -h

# Check Odoo processes
ps aux | grep odoo
```

### Log Analysis

```bash
# Odoo logs
tail -f /var/log/odoo/odoo.log

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# PostgreSQL logs
tail -f /var/log/postgresql/postgresql-15-main.log
```

### Health Checks

Create a health check script `/opt/health_check.sh`:

```bash
#!/bin/bash

# Check Odoo service
if ! systemctl is-active --quiet odoo; then
    echo "ERROR: Odoo service is not running"
    exit 1
fi

# Check database connection
if ! sudo -u odoo psql -h localhost -U odoo -d postgres -c "SELECT 1;" > /dev/null 2>&1; then
    echo "ERROR: Database connection failed"
    exit 1
fi

# Check web interface
if ! curl -f http://localhost:8069/web/health > /dev/null 2>&1; then
    echo "ERROR: Web interface not responding"
    exit 1
fi

echo "All checks passed"
```

## Conclusion

This comprehensive guide covers the essential aspects of setting up a self-hosted Odoo instance with multi-tenancy support and module management. The Docker approach is recommended for production environments due to its reliability and ease of maintenance.

### Key Takeaways:

1. **Use Docker** for production deployments
2. **Implement proper security** measures from the start
3. **Configure multi-tenancy** using database filtering
4. **Set up automated backups** and monitoring
5. **Follow module development** best practices
6. **Monitor performance** and optimize regularly

### Next Steps:

1. Choose your installation method (Docker recommended)
2. Set up your server with proper requirements
3. Configure multi-tenancy for your clients
4. Install and customize modules as needed
5. Implement security and backup procedures
6. Monitor and maintain your system

For additional support and advanced configurations, refer to the official Odoo documentation and community forums.
