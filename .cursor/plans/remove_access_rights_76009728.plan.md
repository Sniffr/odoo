---
name: Remove Access Rights
overview: Remove the staff role-based access control (Staff, Supervisor, Manager groups) from the custom_appointments module and restore full editing permissions for all users.
todos: []
isProject: false
---

# Remove Staff Role-Based Access Rights

## Current Situation

The `[addons/custom_appointments](addons/custom_appointments)` module has a three-tier role-based access control system:

1. **Staff Group** - Limited to viewing own appointments only
2. **Supervisor Group** - Can manage appointments within their branch
3. **Manager Group** - Full access to all features

This is implemented through:

- **Security Groups**: Defined in `[security/appointment_security.xml](addons/custom_appointments/security/appointment_security.xml)` (lines 13-33)
- **Record Rules**: 35 record rules restricting data access based on roles (lines 35-196)
- **Access Rights**: CSV file with group-based model access permissions
- **View Restrictions**: Menu items and buttons with `groups=` attributes

## Problem

The access control is preventing users from seeing and editing appointment data as needed. The system needs to be opened up to allow all authenticated users to manage appointments without role restrictions.

## Solution Approach

### 1. Remove Security Groups and Record Rules

**File**: `[addons/custom_appointments/security/appointment_security.xml](addons/custom_appointments/security/appointment_security.xml)`

- **Delete security groups** (lines 10-33): Remove `group_appointment_staff`, `group_appointment_supervisor`, and `group_appointment_manager`
- **Delete all record rules** (lines 35-196): These restrict data access by role
- Keep only the module category definition (lines 3-8) if needed for organization

### 2. Simplify Access Rights CSV

**File**: `[addons/custom_appointments/security/ir.model.access.csv](addons/custom_appointments/security/ir.model.access.csv)`

Replace the 26 role-specific access rules with simple, universal access rights:

- Grant `base.group_user` (all internal users) full CRUD access to all models
- Keep public user access where currently exists (for website booking functionality)
- Remove all references to the custom security groups

### 3. Update Menu and View Access

**Files to update**:

- `[views/appointment_views.xml](addons/custom_appointments/views/appointment_views.xml)` - Remove `groups=` from menu items (lines 274, 281, 288)
- `[views/staff_member_views.xml](addons/custom_appointments/views/staff_member_views.xml)` - Remove group restrictions (lines 118, 125, 132)
- `[views/staff_profile_views.xml](addons/custom_appointments/views/staff_profile_views.xml)` - Remove group restrictions (line 112)
- `[views/staff_dashboard_views.xml](addons/custom_appointments/views/staff_dashboard_views.xml)` - Remove group restrictions (line 128)
- `[views/branch_views.xml](addons/custom_appointments/views/branch_views.xml)` - Remove manager-only restriction (line 165)
- `[views/service_views.xml](addons/custom_appointments/views/service_views.xml)` - Remove manager-only restriction (line 130)
- `[views/service_category_views.xml](addons/custom_appointments/views/service_category_views.xml)` - Remove manager-only restriction (line 89)
- `[views/promo_code_views.xml](addons/custom_appointments/views/promo_code_views.xml)` - Remove manager-only restrictions (lines 182, 190, 207)
- `[views/customer_views.xml](addons/custom_appointments/views/customer_views.xml)` - Remove manager-only restrictions (lines 245, 252)
- `[views/appointment_settings_views.xml](addons/custom_appointments/views/appointment_settings_views.xml)` - Remove manager-only restrictions (lines 99, 107)

### 4. Update Module Manifest

**File**: `[__manifest__.py](addons/custom_appointments/__manifest__.py)`

Update the data files list to reflect the simplified security structure. The security XML file will either be removed or kept with minimal content.

## Integration Notes

### Payment Modules Compatibility

The module integrates with:

- **payment_pesapal**: PesaPal payment gateway with hosted checkout
- **payment_mpesa**: M-Pesa STK Push integration

Both payment modules have their own access controls and won't be affected by this change.

### SMS Integration

The appointments module already integrates with Odoo's native SMS features:

- Uses `sms.sms` model for sending notifications
- SMS sent at confirmation, cancellation, reminders, and follow-ups
- This functionality will continue to work unchanged

## Testing Requirements

After changes are deployed:

1. **Module Upgrade**: Upgrade the module in Odoo to apply security changes
2. **User Access Testing**:
  - Test with regular user account (not admin)
  - Verify can view all appointments
  - Verify can create/edit/delete appointments
  - Verify can access all menu items
3. **Website Booking**: Test public booking flow still works
4. **Payment Flow**: Test PesaPal/M-Pesa payment integration
5. **SMS Notifications**: Verify SMS still sent for appointment events

## Rollback Plan

If issues arise, the original security groups and rules can be restored by reverting the changes to the security XML and CSV files.