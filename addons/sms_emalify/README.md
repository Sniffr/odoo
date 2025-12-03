# Emalify SMS Provider for Odoo 18

This module integrates Emalify SMS API with Odoo's SMS infrastructure, enabling cost-effective SMS messaging across all Odoo features.

## Features

- **System-Wide Integration**: Works with Sales, POS, Marketing, Appointments, and all custom modules
- **Delivery Status Tracking**: Monitor SMS delivery with callback support
- **Easy Configuration**: Simple setup through Odoo Settings interface
- **Test Wizard**: Verify your configuration before going live
- **Comprehensive Logging**: Detailed delivery logs for troubleshooting
- **Phone Number Formatting**: Automatic international format handling

## Installation

1. Copy the `sms_emalify` folder to your Odoo addons directory
2. Update the apps list in Odoo (Apps → Update Apps List)
3. Install the "SMS Provider: Emalify" module

## Configuration

### 1. Get Emalify Credentials

- Sign up or log in to your [Emalify account](https://emalify.com)
- Navigate to your API settings
- Copy your:
  - API Key
  - Partner ID
  - Shortcode (Sender Name)

### 2. Configure in Odoo

1. Go to **Settings → General Settings**
2. Scroll to the **Emalify SMS Provider** section
3. Fill in your credentials:
   - **Enable Emalify SMS**: Check this box
   - **API Key**: Your Emalify API key
   - **Partner ID**: Your Emalify partner ID
   - **Shortcode**: Your sender name/shortcode
   - **Password Type**: Usually "Plain"
   - **Default Country Code**: Your country code (e.g., 254 for Kenya)
4. Click **Save**
5. Click **Test Connection** to verify your setup

### 3. Configure Callbacks (Optional)

To receive delivery status updates:

1. In Odoo Settings, copy the **Callback URL** shown
2. Log in to your Emalify dashboard
3. Navigate to API Settings → Webhooks/Callbacks
4. Add the callback URL from Odoo
5. Save the configuration

## Usage

### Sending SMS

Once configured, Emalify will automatically handle all SMS in Odoo:

#### From Appointments Module
The existing appointment SMS notifications will automatically use Emalify:
- Booking confirmations
- Appointment reminders
- Cancellation notifications

#### From Marketing
Create SMS campaigns in Marketing → SMS Marketing

#### From Sales/CRM
Send SMS to contacts directly from their records

#### From POS
Configure SMS receipt sending

#### Programmatically
```python
# In your custom module
self.env['sms.sms'].create({
    'number': '+254724512285',
    'body': 'Your message here',
})
```

### Monitoring Deliveries

View SMS delivery logs:
1. Go to **Settings → Technical → Emalify SMS Logs** (System admin)
2. Or click **View Delivery Logs** in Settings → Emalify SMS section

Filter by:
- Status (Pending, Sent, Delivered, Failed)
- Date range
- Phone number

## Phone Number Format

The module accepts phone numbers in various formats and automatically converts them:

- `+254724512285` → `254724512285`
- `0724512285` → `254724512285` (adds default country code)
- `254724512285` → `254724512285` (already formatted)

## Troubleshooting

### SMS Not Sending

1. **Check Configuration**:
   - Verify all credentials are correct
   - Ensure "Enable Emalify SMS" is checked
   - Click "Test Connection" to verify

2. **Check Logs**:
   - View Delivery Logs for error messages
   - Check Odoo server logs for detailed errors

3. **Common Issues**:
   - Insufficient credit in Emalify account
   - Invalid phone number format
   - Incorrect API credentials
   - Network connectivity issues

### Delivery Status Not Updating

1. Verify callback URL is configured in Emalify dashboard
2. Ensure callback URL is accessible from the internet
3. Check firewall settings

## API Reference

### Configuration Parameters

System parameters (accessible via Settings):
- `sms_emalify.enabled`: Enable/disable the provider
- `sms_emalify.api_key`: Emalify API key
- `sms_emalify.partner_id`: Emalify partner ID
- `sms_emalify.shortcode`: SMS sender name
- `sms_emalify.pass_type`: Password type (plain/encrypted)
- `sms_emalify.default_country_code`: Default country code

### Models

#### sms.emalify.delivery
Tracks SMS delivery status with fields:
- `phone_number`: Recipient number
- `message_content`: SMS text
- `status`: Current status (pending/sent/delivered/failed)
- `emalify_message_id`: Emalify's message identifier
- `sent_date`: When SMS was sent
- `delivered_date`: When SMS was delivered
- `error_message`: Error details if failed

### Controllers

#### /sms/emalify/callback
Webhook endpoint for Emalify callbacks (both JSON and HTTP POST supported)

## Security

- API credentials are stored encrypted in Odoo
- Only system administrators can modify settings
- All users can view their own SMS delivery logs
- Callback endpoint validates requests

## Support

For issues related to:
- **Odoo Module**: Check Odoo logs and delivery logs
- **Emalify API**: Contact Emalify support
- **Phone Numbers**: Verify format and validity

## License

LGPL-3

## Credits

Developed for Odoo 18 integration with Emalify SMS API.

