# SMS Emalify Integration for Odoo 18

This module integrates the Emalify SMS API with Odoo's SMS functionality, allowing you to send SMS messages through Emalify instead of Odoo's default IAP service.

## Requirements

- Odoo 18.0
- An Emalify account with API credentials

## Installation

1. Copy the `sms_emalify` folder to your Odoo addons directory
2. Restart Odoo server
3. Go to Apps menu in Odoo
4. Click "Update Apps List" (requires developer mode)
5. Search for "SMS Emalify"
6. Click "Activate" to install the module

## Configuration

1. Go to **Settings > General Settings**
2. Scroll down to the **Contacts** section
3. Under **Send SMS**, select **Send via Emalify**
4. Enter your Emalify credentials:
   - **API Key**: Your Emalify API key (e.g., `e7f6653c80b0b5da94a8750254c72640`)
   - **Partner ID**: Your Emalify Partner ID (e.g., `221`)
   - **Shortcode**: Your Emalify Shortcode/Sender ID (e.g., `STDIOXTIX`)
   - **API Domain**: The Emalify API domain (default: `https://api.v2.emalify.com`)
5. Click **Save**

## Usage

Once configured, all Odoo SMS features will automatically use Emalify:

- Sending SMS from Contacts
- SMS Marketing campaigns
- SMS notifications and reminders
- Any other Odoo feature that uses SMS

## Emalify API Format

The module sends SMS using the following API format:

```json
{
    "apikey": "your-api-key",
    "partnerID": "your-partner-id",
    "mobile": "254XXXXXXXXX",
    "message": "Your message content",
    "shortcode": "YOUR_SHORTCODE",
    "pass_type": "plain"
}
```

## Troubleshooting

If SMS messages are not being sent:

1. Verify your Emalify credentials are correct
2. Check that the phone numbers are in the correct format (e.g., `254XXXXXXXXX` for Kenya)
3. Ensure your Emalify account has sufficient credits
4. Check Odoo server logs for any error messages

## License

LGPL-3
