# Quick Start Guide - Emalify SMS Provider

Get up and running with Emalify SMS in 5 minutes!

## Prerequisites

- Emalify API credentials (API Key, Partner ID, Shortcode)
- Odoo 18 instance running
- Admin access to Odoo

## Installation (2 minutes)

### Step 1: Install Module

1. Go to **Apps** in Odoo
2. Click **Update Apps List** (may need debug mode: add `?debug=1` to URL)
3. Search for "Emalify"
4. Click **Install**

### Step 2: Configure Credentials

1. Go to **Settings → General Settings**
2. Scroll to **Emalify SMS Provider**
3. Fill in:
   ```
   ✓ Enable Emalify SMS
   API Key: [paste your API key]
   Partner ID: [paste your partner ID]
   Shortcode: [paste your shortcode]
   Password Type: Plain
   Country Code: 254 (or yours)
   ```
4. Click **Save**

### Step 3: Test It

1. Click **Test Connection** button
2. Enter your phone number (e.g., `+254724512285`)
3. Click **Send Test SMS**
4. ✓ Check your phone!

## That's It! 🎉

Your SMS integration is now live. All Odoo SMS features will use Emalify automatically.

## Where SMS Will Be Sent From

✅ **Appointments**: Confirmations, reminders, cancellations  
✅ **Sales**: Customer notifications  
✅ **POS**: Receipt notifications  
✅ **Marketing**: SMS campaigns  
✅ **Any module**: That uses Odoo's SMS feature

## Monitor Your SMS

View logs: **Settings → Technical → Emalify SMS Logs**

Or click **View Delivery Logs** in Settings.

## Troubleshooting

### Not sending?
- Check "Enable Emalify SMS" is ✓
- Verify credentials with Test Connection
- Check Emalify account credits

### Need callbacks?
1. Copy callback URL from Settings
2. Add to Emalify dashboard
3. Done!

## Next Steps

- Read [README.md](README.md) for detailed docs
- See [TESTING.md](TESTING.md) for comprehensive testing
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment

## Quick Reference

| Action | Location |
|--------|----------|
| Configure | Settings → General Settings → Emalify SMS |
| Test | Settings → Test Connection button |
| View Logs | Settings → View Delivery Logs |
| Send from Code | `self.env['sms.sms'].create({'number': '...', 'body': '...'})` |

## Support

- Check logs: `tail -f logs/odoo.log | grep -i emalify`
- Check delivery logs in Odoo UI
- Verify Emalify account status
- Review documentation files

---

**Need Help?** Check the comprehensive guides:
- [README.md](README.md) - Full documentation
- [TESTING.md](TESTING.md) - Testing procedures
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment guide
- [INTEGRATION_SUMMARY.md](INTEGRATION_SUMMARY.md) - Technical details

