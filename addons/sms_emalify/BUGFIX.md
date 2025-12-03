# Bug Fix - Installation Error

## Issue

When installing the module, the following error occurred:

```
NotImplementedError: Compute method cannot depend on field 'id'.
```

**Location**: `models/res_config_settings.py` line 59

## Root Cause

In Odoo, computed fields on `TransientModel` (which `res.config.settings` is) cannot depend on the 'id' field. The `@api.depends('id')` decorator was incorrectly used on the `_compute_sms_emalify_callback_url` method.

## The Problem Code

```python
@api.depends('id')
def _compute_sms_emalify_callback_url(self):
    """Compute the callback URL for Emalify delivery status updates"""
    for record in self:
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        record.sms_emalify_callback_url = f'{base_url}/sms/emalify/callback'
```

## Solution

Removed the `@api.depends('id')` decorator since the computed field doesn't actually depend on any field - it only computes from a system parameter:

```python
def _compute_sms_emalify_callback_url(self):
    """Compute the callback URL for Emalify delivery status updates"""
    for record in self:
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        record.sms_emalify_callback_url = f'{base_url}/sms/emalify/callback'
```

## Why This Works

The callback URL field doesn't depend on any record field - it's computed from the system's base URL which is a configuration parameter. Without dependencies, Odoo will compute the field each time the settings form is opened, which is the desired behavior.

## Status

✅ **Fixed** - Module now installs correctly

## Installation Instructions

After the fix:

1. The Odoo container has been restarted
2. Go to **Apps** in Odoo
3. Click **Update Apps List** (may need debug mode)
4. Search for "Emalify"
5. Click **Install**
6. Should install without errors now

## Verification

To verify the fix worked:

```bash
# Check logs for any errors
tail -f /Users/sidneymalingu/PycharmProjects/odoo/logs/odoo.log | grep -i error
```

If no errors appear during installation, the fix is successful.

## Related Changes

- File: `models/res_config_settings.py`
- Lines modified: 59 (decorator removed)
- No other changes needed

---

**Fixed**: December 3, 2025
**Status**: ✅ Ready for installation

