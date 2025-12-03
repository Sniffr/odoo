# Deployment Guide for Emalify SMS Provider

This guide walks you through deploying the Emalify SMS Provider module to your Odoo 18 instance.

## Prerequisites

- Odoo 18 server (running or ready to deploy)
- Emalify account with API credentials
- Access to Odoo addons directory
- System administrator access to Odoo

## Deployment Steps

### Step 1: Prepare Module Files

The module is already in your addons directory:
```
addons/sms_emalify/
├── __init__.py
├── __manifest__.py
├── README.md
├── TESTING.md
├── DEPLOYMENT.md
├── controllers/
│   ├── __init__.py
│   └── main.py
├── data/
│   └── sms_provider_data.xml
├── models/
│   ├── __init__.py
│   ├── res_config_settings.py
│   ├── sms_api.py
│   └── sms_emalify_delivery.py
├── security/
│   └── ir.model.access.csv
├── views/
│   ├── res_config_settings_views.xml
│   └── sms_emalify_delivery_views.xml
└── wizard/
    ├── __init__.py
    ├── sms_test_wizard.py
    └── sms_test_wizard_views.xml
```

### Step 2: Restart Odoo Server

#### For Standard Installation:
```bash
# Navigate to Odoo directory
cd /Users/sidneymalingu/.cursor/worktrees/odoo/pcf

# Restart Odoo with your config
./odoo-bin -c config/odoo.conf -u sms_emalify
```

#### For Docker Installation:
```bash
# Navigate to project directory
cd /Users/sidneymalingu/.cursor/worktrees/odoo/pcf

# Restart containers
docker-compose down
docker-compose up -d

# Or restart without downtime
docker-compose restart web
```

#### For Production with Docker:
```bash
docker-compose -f docker-compose.yml restart
```

### Step 3: Install Module in Odoo

1. Log in to Odoo as administrator
2. Navigate to **Apps**
3. Click **Update Apps List** (may require debug mode)
4. Search for "Emalify"
5. Click **Install** on "SMS Provider: Emalify"
6. Wait for installation to complete

### Step 4: Configure Emalify Credentials

1. Go to **Settings → General Settings**
2. Scroll to **Emalify SMS Provider** section
3. Configure the following:

```
Enable Emalify SMS: ✓ (checked)
API Key: [Your Emalify API Key - from Emalify dashboard]
Partner ID: [Your Emalify Partner ID]
Shortcode: [Your Sender Name/Shortcode]
Password Type: Plain
Default Country Code: 254 (or your country code)
```

4. Click **Save**

### Step 5: Test Configuration

1. In Settings, click **Test Connection**
2. Enter your phone number
3. Click **Send Test SMS**
4. Verify you receive the SMS
5. Check **View Delivery Logs** to confirm sending

### Step 6: Configure Callbacks (Recommended)

1. In Odoo Settings → Emalify SMS, copy the **Callback URL**
   ```
   Example: https://yourdomain.com/sms/emalify/callback
   ```

2. Log in to [Emalify Dashboard](https://emalify.com)
3. Navigate to API Settings or Webhooks
4. Add the callback URL from Odoo
5. Save the configuration

### Step 7: Verify Integration

Test with existing modules:

#### Test with Appointments Module:
1. Create a test appointment with a valid phone number
2. Confirm the appointment
3. Verify SMS is sent
4. Check delivery logs

#### Test Manual SMS:
1. Go to any contact with a phone number
2. Send SMS (if available in your Odoo setup)
3. Verify delivery

### Step 8: Monitor Initial Usage

During the first few hours:

1. **Monitor Logs**:
   ```bash
   # Real-time log monitoring
   tail -f logs/odoo.log | grep -i emalify
   ```

2. **Check Delivery Logs**:
   - Go to Settings → Technical → Emalify SMS Logs
   - Review all sent messages
   - Verify statuses are updating

3. **Check Emalify Dashboard**:
   - Verify SMS count matches
   - Check credit usage
   - Confirm callbacks are received

## Production Deployment Checklist

Before enabling in production:

- [ ] Module installed successfully
- [ ] Test SMS sent and received
- [ ] Callbacks configured and working
- [ ] Emalify account has sufficient credits
- [ ] Alert system configured for failures
- [ ] Team trained on monitoring delivery logs
- [ ] Backup plan documented
- [ ] Integration tested with all modules
- [ ] Performance acceptable under load

## Environment-Specific Configuration

### Development Environment

```python
# In config/odoo.conf or environment
[options]
log_level = debug
# This will show detailed SMS processing logs
```

### Staging Environment

1. Use test Emalify credentials if available
2. Send to test phone numbers only
3. Monitor closely for issues

### Production Environment

1. Use production Emalify credentials
2. Set up monitoring and alerts
3. Configure log rotation
4. Document escalation procedures

## Security Considerations

### Credentials Management

1. **Never commit credentials to git**:
   ```bash
   # Credentials are stored in Odoo database
   # Ensure database backups are encrypted
   ```

2. **Restrict access**:
   - Only system admins can modify settings
   - Regular users can only view logs

3. **Secure callback endpoint**:
   - Endpoint is public but logs suspicious activity
   - Consider adding IP whitelist if Emalify provides IPs

### SSL/HTTPS

Ensure your Odoo instance uses HTTPS:
```nginx
# nginx/conf.d/odoo.conf should have SSL configured
server {
    listen 443 ssl;
    server_name yourdomain.com;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    # ... rest of config
}
```

## Monitoring Setup

### 1. Log Monitoring

Set up log monitoring for errors:

```bash
# Create monitoring script
cat > /usr/local/bin/monitor-sms.sh << 'EOF'
#!/bin/bash
tail -f /path/to/odoo/logs/odoo.log | grep -i "emalify.*error" | while read line; do
    echo "[ALERT] $line" | mail -s "Emalify SMS Error" admin@yourdomain.com
done
EOF

chmod +x /usr/local/bin/monitor-sms.sh
```

### 2. Odoo Scheduled Actions

The module automatically logs all SMS. Optionally create a scheduled action to send daily reports:

1. Go to Settings → Technical → Automation → Scheduled Actions
2. Create new action:
   ```
   Name: Daily SMS Report
   Model: sms.emalify.delivery
   Execute every: 1 Days
   Python Code:
   
   # Count SMS by status today
   from datetime import datetime, timedelta
   today = datetime.now().date()
   domain = [('create_date', '>=', today)]
   
   total = env['sms.emalify.delivery'].search_count(domain)
   delivered = env['sms.emalify.delivery'].search_count(domain + [('status', '=', 'delivered')])
   failed = env['sms.emalify.delivery'].search_count(domain + [('status', '=', 'failed')])
   
   # Send email report
   env['mail.mail'].create({
       'subject': f'Daily SMS Report - {today}',
       'body_html': f'<p>Total: {total}<br>Delivered: {delivered}<br>Failed: {failed}</p>',
       'email_to': 'admin@yourdomain.com',
   }).send()
   ```

### 3. Emalify Dashboard

Regularly check Emalify dashboard for:
- Credit balance
- Delivery rates
- Any API issues

## Backup and Recovery

### Backup SMS Logs

SMS delivery logs are stored in Odoo database:

```bash
# Full database backup (includes SMS logs)
docker exec -t odoo_db pg_dump -U odoo odoo > backup_$(date +%Y%m%d).sql

# Or use Odoo's built-in backup
# Settings → Database Manager → Backup
```

### Recovery Procedures

If SMS stops working:

1. **Check Odoo logs** for errors
2. **Verify Emalify account** (credits, API status)
3. **Test with test wizard** to isolate issue
4. **Disable Emalify** temporarily if needed:
   ```python
   # Via Odoo shell
   env['ir.config_parameter'].set_param('sms_emalify.enabled', 'False')
   ```
5. **Re-enable after fixing** the issue

## Scaling Considerations

### High Volume SMS

If sending > 1000 SMS/day:

1. **Monitor API limits** with Emalify
2. **Consider queue system** for batch sending
3. **Optimize database** queries for logs

### Multiple Servers

For multi-server deployments:

1. All servers share same database (SMS logs centralized)
2. Callback URL can hit any server (load balanced)
3. Ensure consistent configuration across all servers

## Maintenance

### Weekly Tasks

- [ ] Review delivery logs for failures
- [ ] Check Emalify credit balance
- [ ] Monitor SMS volume trends

### Monthly Tasks

- [ ] Archive old SMS logs (> 90 days)
- [ ] Review and optimize if needed
- [ ] Check for module updates

### Quarterly Tasks

- [ ] Review SMS costs vs volume
- [ ] Update documentation if processes changed
- [ ] Test disaster recovery procedures

## Troubleshooting Deployment Issues

### Module Won't Install

**Error: Module not found**
```bash
# Ensure module is in addons path
ls -la addons/sms_emalify/

# Check addons_path in config
grep addons_path config/odoo.conf

# Restart with update
./odoo-bin -c config/odoo.conf -u sms_emalify --stop-after-init
```

**Error: Dependencies not met**
```bash
# Ensure sms and iap modules are installed
# These are Odoo core modules, should be present
```

### SMS Not Sending After Installation

1. **Check if Emalify is enabled**:
   - Settings → Emalify SMS → Enable checkbox

2. **Verify credentials**:
   - Use Test Connection wizard

3. **Check logs**:
   ```bash
   grep -i "emalify" logs/odoo.log | tail -20
   ```

### Callbacks Not Working

1. **Test callback manually**:
   ```bash
   curl -X POST https://yourdomain.com/sms/emalify/callback \
     -H "Content-Type: application/json" \
     -d '{"message_id":"test","status":"delivered","mobile":"254..."}'
   ```

2. **Check firewall**:
   - Ensure port 443/80 is open
   - Callback URL is accessible from internet

3. **Verify Emalify config**:
   - Callback URL is correctly configured in Emalify dashboard

## Rollback Procedure

If you need to rollback:

1. **Disable Emalify**:
   - Settings → Emalify SMS → Uncheck Enable

2. **Uninstall module** (if necessary):
   - Apps → Emalify SMS → Uninstall
   - Note: This will remove delivery logs

3. **Restore previous state**:
   ```bash
   # Restore database backup if needed
   docker exec -i odoo_db psql -U odoo odoo < backup_previous.sql
   ```

## Success Metrics

Track these metrics after deployment:

- **Delivery Rate**: Should be > 95%
- **Average Send Time**: < 5 seconds per SMS
- **Failed Messages**: < 5% of total
- **Callback Success Rate**: > 90%

## Support and Resources

- **Module Documentation**: See README.md
- **Testing Guide**: See TESTING.md
- **Emalify API Docs**: [Emalify Documentation](https://emalify.com/docs)
- **Odoo SMS Framework**: [Odoo Documentation](https://www.odoo.com/documentation/18.0/developer/reference/backend/sms.html)

## Post-Deployment

After successful deployment:

1. **Document your configuration** (without exposing credentials)
2. **Train your team** on monitoring delivery logs
3. **Set up alerts** for SMS failures
4. **Review weekly** for the first month
5. **Optimize** based on usage patterns

## Contact

For issues specific to:
- **Emalify API**: Contact Emalify support
- **Odoo Integration**: Check Odoo logs and this documentation
- **Module Bugs**: Review code and logs

---

**Deployment Date**: _________________  
**Deployed By**: _________________  
**Verified By**: _________________  
**Production Sign-off**: _________________

