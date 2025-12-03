# Marketing SMS Issue Fixed

## Problem

When sending SMS via Marketing module, the SMS was sent successfully but threw an error:

```
odoo.exceptions.MissingError: Record does not exist or has been deleted.
(Record: sms.sms(2067,), User: 1)
```

**Cause**: Our module was immediately sending and deleting SMS records in the `create()` method. However, Marketing SMS module needs the records to exist longer to:
1. Process short links
2. Update tracking information
3. Handle mass mailing features

## Solution

Modified the `create()` override to distinguish between:
- **Regular SMS** (from Appointments, manual sends) → Send immediately ✅
- **Marketing SMS** (has `mailing_id` field) → Don't auto-send, let marketing cron handle it ✅

### Code Changes

**File**: `models/sms_api.py`

#### Change 1: Smart Detection in create()

```python
# Only auto-send for non-marketing SMS (SMS without mailing_id)
# Marketing SMS will be sent via _send() method by the marketing cron
outgoing_sms = records.filtered(lambda s: s.state == 'outgoing' and not s.mailing_id)
if outgoing_sms:
    _logger.info(f'Auto-sending {len(outgoing_sms)} non-marketing SMS')
    outgoing_sms._send_emalify()
else:
    _logger.info(f'Skipping auto-send for {len(records)} SMS (marketing or not outgoing)')
```

#### Change 2: Don't Delete Marketing SMS

```python
# Handle unlink based on parameters (only for non-marketing SMS)
# Marketing SMS should be kept for tracking
if unlink_failed:
    to_unlink = self.filtered(lambda s: s.state == 'error' and not s.mailing_id)
    if to_unlink:
        to_unlink.unlink()
if unlink_sent:
    to_unlink = self.filtered(lambda s: s.state == 'sent' and not s.mailing_id)
    if to_unlink:
        to_unlink.unlink()
```

## How It Works Now

### Regular SMS (Appointments, Manual)
1. SMS created with `create()`
2. No `mailing_id` → Auto-send immediately ✅
3. Mark as sent
4. Delete record (clean up)

### Marketing SMS
1. SMS created by Marketing module with `mailing_id`
2. Has `mailing_id` → Skip auto-send ⏭️
3. Marketing cron calls `_send()` method
4. We send via Emalify ✅
5. Mark as sent
6. **Keep record** for Marketing tracking 📊

## Testing Results

### Before Fix
- ✅ SMS sent successfully
- ❌ Error: "Record does not exist"
- ❌ Marketing queue doesn't update

### After Fix
- ✅ SMS sent successfully
- ✅ No errors
- ✅ Marketing queue updates correctly
- ✅ Tracking information preserved

## Verification

Check logs after sending Marketing SMS:

```bash
tail -f logs/odoo.log | grep -i emalify
```

You should see:
```
INFO: Skipping auto-send for N SMS (marketing or not outgoing)
INFO: === _send_emalify called for N SMS records ===
INFO: ✓ SMS XXXX sent successfully to 254... via Emalify
INFO: Returning True from _send_emalify
```

**NO ERROR** about missing records!

## What Works Now

### ✅ Appointments SMS
- Confirmation → Sends immediately
- Reminders → Sends immediately  
- Cancellation → Sends immediately
- **No mailing_id** → Auto-sent instantly

### ✅ Marketing SMS
- Test SMS → Sent via marketing flow
- Mass campaigns → Sent via marketing cron
- **Has mailing_id** → Handled by marketing module
- **Records preserved** → Tracking works

### ✅ Manual SMS
- From contacts → Sends immediately
- From anywhere → Sends immediately
- **No mailing_id** → Auto-sent instantly

## Database Impact

Marketing SMS records are now kept in database for tracking:
- Can see delivery status
- Can track opens/clicks (if configured)
- Marketing reports work correctly

Regular SMS still auto-delete after sending (clean database).

## Summary

The fix ensures:
1. **Regular SMS** = Instant sending + auto-cleanup ⚡
2. **Marketing SMS** = Proper flow + tracking maintained 📊
3. **No more errors** = Clean execution ✅

---

**Status**: ✅ FIXED  
**Upgraded**: December 3, 2025, 09:32 UTC  
**Ready to Use**: Marketing SMS campaigns now work perfectly!

