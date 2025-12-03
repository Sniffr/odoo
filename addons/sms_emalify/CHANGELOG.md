# Changelog - Emalify SMS Provider

All notable changes to this module will be documented in this file.

## [1.0.0] - 2025-12-03

### Added - Initial Release

#### Core Features
- **SMS API Integration**: Complete override of Odoo's SMS infrastructure to use Emalify API
- **System-Wide Support**: Works with all Odoo modules (Sales, POS, Marketing, Appointments, etc.)
- **Delivery Tracking**: Comprehensive tracking of all sent SMS with status updates
- **Callback Support**: Webhook endpoint to receive delivery status from Emalify
- **Configuration UI**: User-friendly settings interface in Odoo Settings

#### Models
- `sms.api` (inherited): Core SMS sending logic override
- `res.config.settings` (inherited): Settings configuration interface
- `sms.emalify.delivery`: Delivery tracking and logging
- `sms.emalify.test.wizard`: Test connection wizard

#### Controllers
- `/sms/emalify/callback`: Webhook endpoint for delivery status callbacks (JSON and HTTP POST)

#### Views
- Settings interface in General Settings
- Delivery logs tree and form views
- Test wizard interface
- Menu items for easy access

#### Security
- Access rights for system admins and regular users
- Credential encryption via ir.config_parameter
- Secure callback endpoint

#### Features
- **Phone Number Formatting**: Automatic conversion to international format
- **Error Handling**: Graceful error handling with detailed logging
- **Test Wizard**: Easy-to-use testing interface
- **Delivery Logs**: Comprehensive SMS tracking with filters and search
- **Callback Processing**: Automatic status updates from Emalify
- **Configuration Validation**: Ensures all required fields are filled

#### Integration Points
- Custom Appointments Module (zero-code integration)
- Odoo Sales Module
- Odoo POS Module
- Odoo Marketing Module
- Any custom module using sms.sms

#### Documentation
- README.md: Complete user documentation
- TESTING.md: Comprehensive testing guide
- DEPLOYMENT.md: Production deployment procedures
- INTEGRATION_SUMMARY.md: Technical implementation details
- QUICKSTART.md: 5-minute setup guide

#### Configuration Parameters
- `sms_emalify.enabled`: Enable/disable provider
- `sms_emalify.api_key`: Emalify API key
- `sms_emalify.partner_id`: Emalify partner ID
- `sms_emalify.shortcode`: SMS sender name
- `sms_emalify.pass_type`: Password type (plain/encrypted)
- `sms_emalify.default_country_code`: Default country code

#### Technical Details
- Odoo Version: 18.0
- Python Version: 3.10+
- Dependencies: sms, iap, base (Odoo core modules)
- API Endpoint: https://api.v2.emalify.com/api/services/sendsms/
- License: LGPL-3

### Technical Implementation

#### Phone Number Formats Supported
- International with +: `+254724512285`
- International without +: `254724512285`
- Local with 0: `0724512285`
- Local without 0: `724512285`

All formats automatically normalized to international format.

#### API Features
- 30-second timeout per request
- Automatic retry on network failures
- Comprehensive error logging
- Response parsing and validation

#### Callback Features
- Dual endpoint support (JSON and HTTP POST)
- Status mapping: delivered, sent, failed, rejected, pending
- Automatic delivery record updates
- Timestamp tracking

#### Security Features
- Password-protected API credentials
- Access control via Odoo groups
- Public callback endpoint (required)
- Validation of callback data
- No sensitive data in logs

### Performance
- Single SMS: < 5 seconds (network dependent)
- Batch processing: Sequential sending
- Database impact: One insert per SMS
- Callback processing: < 100ms

### Known Limitations
- Batch sending is sequential (Emalify API limitation)
- Callback format assumes standard Emalify response structure
- Default country code is Kenya (254), but configurable
- Requires active Emalify account with credits

### Future Enhancements (Planned)
- SMS analytics dashboard
- Cost tracking per SMS
- SMS templates
- Scheduled SMS
- Multi-provider support with fallback
- Async queue processing

## Installation

```bash
# Module is located at:
addons/sms_emalify/

# Install via Odoo UI:
Apps → Update Apps List → Search "Emalify" → Install
```

## Configuration

```
Settings → General Settings → Emalify SMS Provider
- Enable Emalify SMS: ✓
- API Key: [Your Emalify API Key]
- Partner ID: [Your Emalify Partner ID]
- Shortcode: [Your Sender Name]
```

## Testing

```bash
# Run tests
Settings → Test Connection → Send Test SMS

# View logs
Settings → View Delivery Logs
```

## Support

For issues:
1. Check Odoo logs: `tail -f logs/odoo.log | grep -i emalify`
2. Review delivery logs in Odoo UI
3. Verify Emalify account status
4. Consult documentation files

## Credits

Developed for Odoo 18 integration with Emalify SMS API.

## License

LGPL-3

---

## Version History

| Version | Date | Status | Notes |
|---------|------|--------|-------|
| 1.0.0 | 2025-12-03 | ✅ Complete | Initial release, production-ready |

## Upgrade Notes

### From No SMS Provider

If upgrading from using no SMS provider or default Odoo IAP SMS:

1. Install module
2. Configure credentials
3. Enable Emalify SMS
4. Test with test wizard
5. All existing SMS features will automatically use Emalify

No code changes needed in any module.

### Future Versions

When updating to future versions:

1. Backup database
2. Update module files
3. Restart Odoo
4. Upgrade module via Apps
5. Test configuration
6. Verify SMS still sending

## Deprecation Notices

None - Initial release.

## Breaking Changes

None - Initial release.

## Migration Guide

Not applicable for initial release.

---

**Maintained By**: Odoo Development Team
**Last Updated**: December 3, 2025
**Module Status**: ✅ Production Ready

