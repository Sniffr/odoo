# Staff SMS Notifications - Feature Added

## Overview

Staff members now receive **SMS notifications** in addition to email notifications when new appointments are booked.

## What Was Added

### Staff SMS Message Format

When an appointment is confirmed, staff members receive an SMS like:

```
📅 New Appointment!
Customer: John Doe
Service: Classic Lash Extensions
Date: December 03, 2025
Time: 02:30 PM
Duration: 120 min
Customer Phone: +254700123456
Location: Lashes by Shazz - Downtown
Ref: APPT-3005
```

## When SMS is Sent to Staff

### Trigger
SMS is sent during the `_send_staff_notification()` method, which is called when:
- Appointment is confirmed (`action_confirm()`)
- Payment is completed
- Customer notification has been sent

### Requirements
For staff to receive SMS:
1. ✅ Staff member must have a **phone number** set in their profile
2. ✅ Appointment must be confirmed
3. ✅ `staff_notification_sent` flag must be False (not already sent)

## Staff Notifications Flow

```
Appointment Confirmed
        ↓
_send_staff_notification() called
        ↓
    ┌───────────────┐
    │  Email Path   │
    └───────────────┘
        ↓
    Has Email?
    Yes → Send email with calendar invite
    No  → Log warning
        ↓
    ┌───────────────┐
    │   SMS Path    │  ← NEW!
    └───────────────┘
        ↓
    Has Phone?
    Yes → Send SMS via Emalify
    No  → Skip (no error)
```

## Information Included in Staff SMS

### Customer Details
- **Customer Name**: Who booked the appointment
- **Customer Phone**: Contact number for the customer

### Appointment Details
- **Service**: What service is being provided
- **Date**: Full date (December 03, 2025)
- **Time**: 12-hour format (02:30 PM)
- **Duration**: Length in minutes

### Location & Reference
- **Location**: Branch name
- **Reference**: Appointment reference number (APPT-XXXX)

## Code Implementation

### Location
File: `addons/custom_appointments/models/appointment.py`
Method: `_send_staff_notification()` (lines 723-766)

### Code Added

```python
# Send SMS notification to staff member
if appointment.staff_member_id.phone:
    local_start = appointment._get_local_datetime(appointment.start)
    sms_message = (
        f"📅 New Appointment!\n"
        f"Customer: {appointment.customer_name}\n"
        f"Service: {appointment.service_id.name}\n"
        f"Date: {local_start.strftime('%B %d, %Y')}\n"
        f"Time: {local_start.strftime('%I:%M %p')}\n"
        f"Duration: {appointment.duration} min\n"
        f"Customer Phone: {appointment.customer_phone or 'Not provided'}\n"
        f"Location: {appointment.branch_id.name}\n"
        f"Ref: {appointment.name}"
    )
    _logger.info(f"Sending SMS notification to staff {appointment.staff_member_id.name} at {appointment.staff_member_id.phone}")
    self._send_sms_notification(appointment.staff_member_id.phone, sms_message)
```

## Complete Notification Matrix

| Notification Type | Customer | Staff |
|------------------|----------|-------|
| **Email** | ✅ Confirmation with calendar invite | ✅ New booking with calendar invite |
| **SMS** | ✅ Enhanced details with branch info | ✅ **NEW!** Booking details with customer info |

## Staff Member Setup

### Ensure Staff Has Phone Number

1. Go to **Appointments** → **Configuration** → **Staff Members**
2. Open staff member record
3. Enter **Phone** number (e.g., +254700123456)
4. Save

### Phone Number Format

The phone number will be automatically formatted by Emalify SMS provider:
- **Accepted formats**: 
  - International: +254700123456
  - Local: 0700123456
  - Without prefix: 700123456
- **Converted to**: 254700123456 (Kenya format)

## Testing

### Test Staff SMS Notification

1. Ensure staff member has phone number set
2. Create new appointment for that staff member
3. Complete payment
4. Confirm appointment
5. **Check staff phone** for SMS notification

### Expected Behavior

#### Success Scenario
```
✅ Staff has email → Email sent with calendar invite
✅ Staff has phone → SMS sent with appointment details
✅ Both notifications sent successfully
```

#### Partial Success
```
✅ Staff has email, no phone → Only email sent
❌ Staff has phone, no email → Only SMS sent (+ warning logged)
```

#### No Contact Info
```
⚠️ Staff has no email → Warning logged, no email sent
⚠️ Staff has no phone → No SMS sent (silent skip)
```

## Logging

### SMS Logs
```
INFO: Sending SMS notification to staff Sidney Malingu at +254700123456
INFO: Auto-sending 1 non-marketing SMS
INFO: SMS sent successfully to 254700123456 via Emalify
```

### Error Logs
If SMS fails:
```
WARNING: Failed to send SMS to +254700123456: [error details]
```

## Benefits

### For Staff Members
- ✅ Instant notification on mobile device
- ✅ Quick overview of new booking
- ✅ Customer contact info readily available
- ✅ No need to check email for basic info

### For Business
- ✅ Better staff responsiveness
- ✅ Reduced missed appointments
- ✅ Improved communication
- ✅ Professional operation

### For Customers
- ✅ Staff is immediately aware of booking
- ✅ Better preparation for appointment
- ✅ Faster confirmation/communication

## SMS Cost Considerations

### Per Appointment SMS Count
Each confirmed appointment now sends:
- **2 SMS** for customer (confirmation)
- **1 SMS** for staff (notification)
- **Total**: 3 SMS per appointment

### Enhanced Messages Use Multiple Segments
- Customer SMS: ~2-3 segments (200-250 chars)
- Staff SMS: ~2 segments (180-200 chars)

### Cost Example (if 1 SMS segment = KES 1)
- Customer confirmation: ~2.5 segments = KES 2.50
- Staff notification: ~2 segments = KES 2.00
- **Total per appointment**: ~KES 4.50

**Note**: Adjust based on your actual SMS pricing from Emalify.

## Configuration

### Enable/Disable Staff SMS

If you want to temporarily disable staff SMS notifications without removing phone numbers:

**Option 1**: Remove phone from staff profile
**Option 2**: Comment out the code block (requires developer)

### Customize Message

To change the staff SMS message format, edit:
```python
# File: addons/custom_appointments/models/appointment.py
# Method: _send_staff_notification()
# Lines: 756-766
```

Example shorter message:
```python
sms_message = (
    f"📅 New Booking!\n"
    f"{appointment.customer_name}\n"
    f"{appointment.service_id.name}\n"
    f"{local_start.strftime('%b %d at %I:%M %p')}\n"
    f"Ref: {appointment.name}"
)
```

## Comparison: Before vs After

### Before This Update
```
Appointment Confirmed
    ↓
Customer: Email ✓ + SMS ✓
Staff:    Email ✓ + SMS ✗
```

### After This Update
```
Appointment Confirmed
    ↓
Customer: Email ✓ + SMS ✓
Staff:    Email ✓ + SMS ✓  ← NEW!
```

## Deployment Status

✅ **DEPLOYED TO PRODUCTION**
- Code updated in `appointment.py`
- Odoo production container restarted
- Feature active immediately
- No database upgrade needed

## Next Appointment

The next time an appointment is confirmed, staff members will receive:
1. ✅ Email notification (existing)
2. ✅ SMS notification (NEW!)

---

**Staff will now stay informed via both email and SMS!** 📧📱

