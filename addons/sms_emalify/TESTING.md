# Testing Guide for Emalify SMS Provider

This document provides comprehensive testing procedures for the Emalify SMS Provider module.

## Pre-Testing Checklist

Before testing, ensure you have:
- [ ] Valid Emalify API credentials (API Key, Partner ID, Shortcode)
- [ ] Active Emalify account with sufficient credits
- [ ] Test phone number that can receive SMS
- [ ] Odoo 18 instance with the module installed

## Installation Testing

### 1. Module Installation

```bash
# Restart Odoo
./odoo-bin -c config/odoo.conf

# Or with Docker
docker-compose restart
```

1. Go to **Apps** in Odoo
2. Click **Update Apps List**
3. Search for "Emalify"
4. Click **Install** on "SMS Provider: Emalify"
5. ✓ Verify installation completes without errors

### 2. Verify Module Structure

Check that the following menu items appear:
- Settings → General Settings → Emalify SMS Provider section
- Settings → Technical → Emalify SMS Logs (for system admins)

## Configuration Testing

### 1. Basic Configuration

1. Navigate to **Settings → General Settings**
2. Scroll to **Emalify SMS Provider** section
3. Enable the provider by checking **Enable Emalify SMS**
4. Fill in credentials:
   ```
   API Key: [Your Emalify API Key]
   Partner ID: [Your Emalify Partner ID]
   Shortcode: [Your Sender Name]
   Password Type: Plain
   Default Country Code: 254
   ```
5. Click **Save**
6. ✓ Verify no errors occur

### 2. Test Connection

1. In the same Settings page, click **Test Connection** button
2. In the wizard that opens:
   - Enter a test phone number (e.g., your own)
   - Modify test message if desired
   - Click **Send Test SMS**
3. ✓ Verify success message appears
4. ✓ Check your phone for the test SMS
5. ✓ Click **View Delivery Logs** to see the log entry

### 3. Configuration Validation

Test invalid configurations:

**Test Case 1: Missing API Key**
1. Clear the API Key field
2. Try to send test SMS
3. ✓ Should show error about incomplete credentials

**Test Case 2: Invalid Phone Number**
1. Enter invalid phone (e.g., "123")
2. Try to send test SMS
3. ✓ Should show validation error

## Integration Testing

### 1. Appointments Module Integration

**Test Case: Appointment Confirmation SMS**

1. Navigate to **Appointments → Appointments**
2. Create a new appointment:
   - Customer: Select or create a customer with a valid phone number
   - Service: Select any service
   - Date/Time: Select future date/time
   - Staff: Select a staff member
3. Confirm the appointment
4. ✓ Check that SMS is sent automatically
5. ✓ Verify SMS delivery in **Emalify SMS Logs**
6. ✓ Customer should receive SMS confirmation

**Test Case: Appointment Reminder**

1. Create appointment for tomorrow (within 24 hours)
2. Wait for cron job or manually trigger:
   ```python
   # In Odoo shell
   self.env['custom.appointment'].send_appointment_reminders()
   ```
3. ✓ Check that reminder SMS is sent
4. ✓ Verify in delivery logs

**Test Case: Appointment Cancellation**

1. Open an existing appointment
2. Click **Cancel** button
3. ✓ Verify cancellation SMS is sent
4. ✓ Check delivery logs

### 2. Manual SMS Testing

**From Contact Record**

1. Open **Contacts**
2. Select a contact with a valid phone number
3. Click **SMS** button (if available) or use the SMS composer
4. Send a test SMS
5. ✓ Verify SMS is sent via Emalify
6. ✓ Check delivery logs

**From Sales Module** (if installed)

1. Create a quotation
2. Send it via SMS (if configured)
3. ✓ Verify delivery through Emalify

### 3. Programmatic Testing

Create a test method in a custom module or via Odoo shell:

```python
# Test single SMS
sms = self.env['sms.sms'].create({
    'number': '+254724512285',
    'body': 'Test SMS from Odoo via Emalify',
})
sms.send()

# Check result
delivery = self.env['sms.emalify.delivery'].search([
    ('phone_number', '=', '254724512285')
], limit=1, order='create_date desc')
print(f"Status: {delivery.status}")
print(f"Message ID: {delivery.emalify_message_id}")
```

## Callback Testing

### 1. Configure Callback URL

1. Copy callback URL from Settings: `https://yourdomain.com/sms/emalify/callback`
2. Add it to your Emalify dashboard

### 2. Test Callback Reception

**Manual Callback Test (using curl)**

```bash
# JSON callback
curl -X POST https://yourdomain.com/sms/emalify/callback \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": "test123",
    "status": "delivered",
    "mobile": "254724512285",
    "delivered_at": "2024-01-01 12:00:00"
  }'

# Should return: {"success": true, "message": "Status updated"}
```

**Verify Callback Processing**

1. Check Odoo logs for callback processing messages
2. Check delivery log record gets updated with status
3. ✓ Status should change to "delivered"

### 3. End-to-End Callback Test

1. Send actual SMS via test wizard
2. Wait for Emalify to send callback (usually within seconds)
3. ✓ Check delivery log updates automatically
4. ✓ Verify `delivered_date` is populated

## Phone Number Format Testing

Test various phone number formats:

```python
# Test phone formatting
sms_api = self.env['sms.api']

test_numbers = [
    '+254724512285',    # International with +
    '254724512285',     # International without +
    '0724512285',       # Local format
    '724512285',        # Without leading 0
]

for number in test_numbers:
    formatted = sms_api._emalify_format_phone_number(number)
    print(f"{number} → {formatted}")
    # All should output: 254724512285
```

✓ All formats should normalize to `254724512285`

## Error Handling Testing

### 1. Network Failure Simulation

**Test Case: Emalify API Unavailable**

1. Temporarily modify API URL in code to invalid URL
2. Try to send SMS
3. ✓ Should log error and mark SMS as failed
4. ✓ Delivery log should show error message

### 2. Invalid Credentials

**Test Case: Wrong API Key**

1. Change API Key to invalid value
2. Try to send SMS
3. ✓ Should fail gracefully with clear error message
4. ✓ Should not crash Odoo

### 3. Rate Limiting

**Test Case: Bulk SMS**

```python
# Send 100 SMS rapidly
for i in range(100):
    self.env['sms.sms'].create({
        'number': '+254724512285',
        'body': f'Test message {i}',
    })
```

✓ All should be processed without errors
✓ Check Emalify doesn't rate-limit

## Performance Testing

### 1. Batch SMS Performance

```python
import time

# Test batch of 50 SMS
start_time = time.time()

for i in range(50):
    self.env['sms.sms'].create({
        'number': '+254724512285',
        'body': f'Performance test {i}',
    })

elapsed = time.time() - start_time
print(f"50 SMS sent in {elapsed:.2f} seconds")
print(f"Average: {elapsed/50:.2f} seconds per SMS")
```

✓ Should complete in reasonable time (< 5 seconds per SMS)

## Security Testing

### 1. Access Rights

**Test Case: Regular User Access**

1. Log in as regular user (not system admin)
2. Try to access Settings → Emalify SMS
3. ✓ Should not be able to modify credentials
4. ✓ Can view own delivery logs

**Test Case: Portal User Access**

1. Log in as portal user
2. Try to access delivery logs directly
3. ✓ Should be denied access

### 2. Callback Security

**Test Case: Invalid Callback**

```bash
# Try to send malicious callback
curl -X POST https://yourdomain.com/sms/emalify/callback \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": "nonexistent123",
    "status": "delivered"
  }'
```

✓ Should return error but not crash
✓ Should log warning about unknown message_id

## Load Testing

### 1. Concurrent SMS

```python
# Simulate multiple users sending SMS simultaneously
import threading

def send_sms_batch(thread_id):
    for i in range(10):
        self.env['sms.sms'].create({
            'number': '+254724512285',
            'body': f'Load test from thread {thread_id}, msg {i}',
        })

threads = []
for i in range(5):
    t = threading.Thread(target=send_sms_batch, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()
```

✓ All SMS should be sent successfully
✓ No database locks or errors

## Monitoring & Logging

### 1. Check Odoo Logs

```bash
# Monitor logs in real-time
tail -f logs/odoo.log | grep -i emalify
```

Look for:
- ✓ "SMS sent successfully" messages
- ✓ "Received Emalify callback" messages
- ✗ Any ERROR level messages

### 2. Check Delivery Logs

1. Go to **Settings → Technical → Emalify SMS Logs**
2. Review recent entries
3. ✓ Verify statuses are updating correctly
4. ✓ Check for any failed messages

## Production Readiness Checklist

Before deploying to production:

- [ ] All tests pass successfully
- [ ] Callbacks are properly configured and working
- [ ] Emalify account has sufficient credits
- [ ] Monitoring is set up
- [ ] Backup credentials are stored securely
- [ ] Documentation is provided to team
- [ ] Fallback plan is defined (if Emalify fails)

## Troubleshooting Common Issues

### Issue: SMS not sending

**Debug Steps:**
1. Check Odoo logs: `tail -f logs/odoo.log | grep -i sms`
2. Verify Emalify is enabled in Settings
3. Test connection with test wizard
4. Check Emalify account credits
5. Verify phone number format

### Issue: Callbacks not working

**Debug Steps:**
1. Verify callback URL is accessible from internet
2. Check firewall rules
3. Test callback manually with curl
4. Check Odoo logs for callback errors
5. Verify Emalify dashboard callback configuration

### Issue: Wrong phone number format

**Debug Steps:**
1. Check default country code setting
2. Test phone number formatting manually
3. Verify customer phone numbers are correct
4. Check Odoo logs for formatting errors

## Success Criteria

The integration is successful when:

✓ Test SMS sends and delivers successfully
✓ Appointments module automatically sends SMS
✓ Delivery status updates via callbacks
✓ All logs are clean (no errors)
✓ Phone numbers format correctly
✓ Performance is acceptable (< 5s per SMS)
✓ Security access rights work correctly

## Next Steps

After successful testing:

1. **Document Configuration**: Keep credentials secure
2. **Train Users**: Show how to monitor delivery logs
3. **Set Up Monitoring**: Configure alerts for failures
4. **Plan Maintenance**: Schedule regular checks
5. **Monitor Usage**: Track SMS volume and costs

## Support

For issues during testing:
- Check Odoo logs first
- Review delivery logs in Odoo
- Contact Emalify support for API issues
- Check this documentation for troubleshooting

