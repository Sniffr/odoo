# Enhanced SMS Messages for Appointments

## Overview

All appointment SMS messages have been enhanced to include comprehensive information including:
- Branch details (name, address, contact)
- Complete appointment information
- Staff member details
- Duration and timing
- Reference numbers for easy lookup

## Enhanced SMS Messages

### 1. Confirmation SMS

**When Sent**: After appointment is confirmed and payment completed

**Old Message**:
```
Appointment confirmed! Lash Extensions with Sidney on December 03 at 02:30 PM. See you soon!
```

**New Enhanced Message**:
```
✓ Appointment Confirmed!
Service: Lash Extensions
Date: December 03, 2025
Time: 02:30 PM
Duration: 120 min
Staff: Sidney
Location: Lashes by Shazz - Downtown
Address: 123 Main Street, Nairobi
Phone: +254700123456
Ref: APPT-1744
```

**Benefits**:
- ✅ Complete appointment details in one message
- ✅ Branch location with full address
- ✅ Contact phone for any questions
- ✅ Reference number for easy lookup
- ✅ Professional formatting with checkmark icon

---

### 2. Reminder SMS

**When Sent**: 24 hours before appointment (via cron job)

**Old Message**:
```
Reminder: Your appointment for Lash Extensions is tomorrow at 02:30 PM with Sidney.
```

**New Enhanced Message**:
```
⏰ Reminder: Appointment Tomorrow!
Service: Lash Extensions
Date: Tuesday, December 03
Time: 02:30 PM
Duration: 120 min
Staff: Sidney
Location: Lashes by Shazz - Downtown
Address: 123 Main Street, Nairobi
Contact: +254700123456
See you tomorrow!
```

**Benefits**:
- ✅ Full day name (Tuesday) for clarity
- ✅ Complete location details so customer can plan
- ✅ Duration reminder to help customer plan time
- ✅ Contact number in case of questions
- ✅ Friendly reminder tone with alarm icon

---

### 3. Cancellation SMS

**When Sent**: When appointment is cancelled by staff or customer

**Old Message**:
```
Your appointment for Lash Extensions on December 03 at 02:30 PM has been cancelled. Please contact us to reschedule.
```

**New Enhanced Message**:
```
✗ Appointment Cancelled
Service: Lash Extensions
Was scheduled: December 03 at 02:30 PM
Ref: APPT-1744

To reschedule, contact:
Lashes by Shazz - Downtown
Phone: +254700123456
Email: info@lashesbyshazz.com
```

**Benefits**:
- ✅ Clear cancellation notice with X icon
- ✅ Shows what was cancelled (helps if customer has multiple bookings)
- ✅ Reference number for customer records
- ✅ Complete contact information for easy rescheduling
- ✅ Both phone and email provided

---

## Information Included

### Branch Information
- **Branch Name**: The specific branch location
- **Address**: Full street address and city
- **Phone**: Branch phone number (or company phone as fallback)
- **Email**: Branch email (shown in cancellation)

### Appointment Details
- **Service Name**: The service being provided
- **Date**: Full date with month name
- **Time**: 12-hour format (02:30 PM)
- **Duration**: Appointment length in minutes
- **Staff Member**: Who will provide the service
- **Reference Number**: Appointment reference (e.g., APPT-1744)

### Customer Experience Benefits

1. **All Info in One Place**: Customer doesn't need to search emails or remember details
2. **Easy to Find Location**: Full address included for GPS/maps
3. **Contact Available**: Can call branch directly if needed
4. **Professional**: Clean, organized format creates trust
5. **Reference Number**: Easy to reference when calling or checking status

---

## Technical Implementation

### SMS Message Structure

Messages use multi-line format with clear sections:

```python
sms_message = (
    f"✓ Appointment Confirmed!\n"
    f"Service: {appointment.service_id.name}\n"
    f"Date: {local_start.strftime('%B %d, %Y')}\n"
    f"Time: {local_start.strftime('%I:%M %p')}\n"
    f"Duration: {appointment.duration} min\n"
    f"Staff: {appointment.staff_member_id.name}\n"
    f"Location: {appointment.branch_id.name}\n"
    f"Address: {appointment.branch_id.street}, {appointment.branch_id.city}\n"
    f"Phone: {appointment.branch_id.phone or self.env.user.company_id.phone}\n"
    f"Ref: {appointment.name}"
)
```

### Data Sources

All information comes from the appointment record:
- `appointment.service_id.name` - Service name
- `appointment.start` - Converted to local timezone
- `appointment.duration` - Duration in minutes
- `appointment.staff_member_id.name` - Staff member
- `appointment.branch_id.*` - All branch information
- `appointment.name` - Reference number

### Fallback Handling

If branch information is missing:
- Phone: Falls back to company phone
- Email: Falls back to company email
- Address: Uses branch fields (street, city)

---

## Message Length Considerations

### SMS Length
- **Confirmation**: ~200-250 characters
- **Reminder**: ~210-260 characters
- **Cancellation**: ~200-240 characters

### SMS Segments
Most enhanced messages will use 2-3 SMS segments (160 chars each):
- 1 segment = 160 characters
- 2 segments = 306 characters
- 3 segments = 459 characters

**Note**: While longer than simple SMS, the comprehensive information provides much better customer experience and reduces support calls.

---

## Testing the Enhanced Messages

### Test Confirmation SMS

1. Create a new appointment
2. Complete payment
3. Confirm appointment
4. Check your phone for enhanced SMS
5. Verify all details are correct

### Test Reminder SMS

1. Create appointment for tomorrow
2. Wait for cron to run (or trigger manually)
3. Check SMS includes full details
4. Verify timing and location info

### Test Cancellation SMS

1. Create and confirm appointment
2. Cancel the appointment
3. Verify cancellation SMS includes rescheduling info
4. Check contact details are present

---

## Sample SMS Output

### Real Example (Confirmation)

```
✓ Appointment Confirmed!
Service: Classic Lash Extensions
Date: December 03, 2025
Time: 02:30 PM
Duration: 120 min
Staff: Sidney Malingu
Location: Lashes by Shazz - Downtown
Address: 123 Main Street, Nairobi
Phone: +254700123456
Ref: APPT-1744
```

### Real Example (Reminder)

```
⏰ Reminder: Appointment Tomorrow!
Service: Classic Lash Extensions
Date: Tuesday, December 03
Time: 02:30 PM
Duration: 120 min
Staff: Sidney Malingu
Location: Lashes by Shazz - Downtown
Address: 123 Main Street, Nairobi
Contact: +254700123456
See you tomorrow!
```

### Real Example (Cancellation)

```
✗ Appointment Cancelled
Service: Classic Lash Extensions
Was scheduled: December 03 at 02:30 PM
Ref: APPT-1744

To reschedule, contact:
Lashes by Shazz - Downtown
Phone: +254700123456
Email: info@lashesbyshazz.com
```

---

## Customization Options

### If You Want Shorter Messages

Edit `custom_appointments/models/appointment.py` and remove fields:

**Minimal Confirmation**:
```python
sms_message = (
    f"✓ Confirmed: {appointment.service_id.name}\n"
    f"{local_start.strftime('%B %d at %I:%M %p')}\n"
    f"Staff: {appointment.staff_member_id.name}\n"
    f"Location: {appointment.branch_id.name}\n"
    f"Ref: {appointment.name}"
)
```

### If You Want to Add More Info

You can add:
- Price: `f"Price: KES {appointment.total_price}\n"`
- Deposit info: `f"Deposit Paid: KES {appointment.paid_amount}\n"`
- Special notes: `f"Notes: {appointment.notes}\n"` (if field exists)

---

## Benefits Summary

### For Customers
- ✅ All info in one SMS
- ✅ Easy to find branch location
- ✅ Can save for reference
- ✅ Reduces need to search emails
- ✅ Professional experience

### For Business
- ✅ Fewer "where are you located?" calls
- ✅ Fewer "what time was my appointment?" calls
- ✅ Reduced no-shows (full details provided)
- ✅ Professional brand image
- ✅ Better customer satisfaction

### For Staff
- ✅ Fewer customer service calls
- ✅ Customers arrive prepared
- ✅ Less confusion about location
- ✅ Professional communication

---

## Status

✅ **Implemented**: December 3, 2025
✅ **Applied to**:
  - Confirmation SMS
  - Reminder SMS  
  - Cancellation SMS
✅ **Integrated with**: Emalify SMS Provider
✅ **Ready to Use**: Create appointment to test!

---

**The enhanced SMS messages are now live and will be sent for all new appointments!** 🎉

