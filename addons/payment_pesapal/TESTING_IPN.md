# PesaPal IPN Testing Guide

This document explains how to test the PesaPal IPN (Instant Payment Notification) implementation.

## Overview

The IPN endpoint is located at: `/payment/pesapal/ipn`

PesaPal sends GET requests to this endpoint with the following parameters:
- `OrderTrackingId`: Unique tracking ID for the transaction
- `OrderMerchantReference`: Merchant reference for the transaction

## IPN URL Configuration

Configure this URL in your PesaPal dashboard:
- **Production**: `https://your-domain.com/payment/pesapal/ipn`
- **Sandbox**: `https://your-sandbox-domain.com/payment/pesapal/ipn`

The URL is automatically computed in Odoo based on your base URL.

## What the IPN Does

1. **Receives notification** from PesaPal when payment status changes
2. **Verifies payment** by calling PesaPal API to get transaction status
3. **Checks for duplicates** to prevent processing same payment twice
4. **Logs all IPNs** in `pesapal.ipn.log` model for audit trail
5. **Updates transaction** state based on payment status
6. **Confirms appointment** if payment is successful
7. **Sends confirmation emails** to customer and staff

## Payment Status Codes

PesaPal uses these status codes:
- `0`: Pending
- `1`: Completed (successful payment)
- `2`: Failed
- `3`: Reversed

## Testing the IPN

### Method 1: Using curl (Basic Test)

Test the endpoint is accessible:

```bash
# Test with missing tracking ID (should return error)
curl -X GET 'http://localhost:8069/payment/pesapal/ipn?OrderMerchantReference=TEST-123'

# Test with non-existent transaction (should log and return "Transaction not found")
curl -X GET 'http://localhost:8069/payment/pesapal/ipn?OrderTrackingId=NONEXISTENT-12345&OrderMerchantReference=TEST-456'
```

### Method 2: Using Python Test Script

A comprehensive test script is provided: `test_pesapal_ipn.py`

```bash
python3 test_pesapal_ipn.py
```

This script tests:
- Successful payment IPN
- Failed payment IPN
- Duplicate IPN detection
- Missing tracking ID handling
- Non-existent transaction handling

### Method 3: Manual Testing with Real Transaction

1. **Create a test appointment** through the booking system
2. **Initiate payment** with PesaPal (use sandbox mode)
3. **Complete payment** on PesaPal's hosted checkout
4. **Check IPN logs** in Odoo:
   - Go to: Settings → Technical → Database Structure → Models
   - Search for: `pesapal.ipn.log`
   - View records to see IPN notifications received

### Method 4: Simulate IPN from PesaPal Sandbox

PesaPal sandbox provides a way to trigger test IPNs:

1. Log into PesaPal sandbox dashboard
2. Go to your transaction
3. Use the "Send IPN" button to manually trigger notification
4. Check Odoo logs and `pesapal.ipn.log` records

## Verifying IPN Processing

### Check IPN Logs

```sql
-- View all IPN logs
SELECT * FROM pesapal_ipn_log ORDER BY create_date DESC LIMIT 10;

-- Check for duplicates
SELECT tracking_id, COUNT(*) as count
FROM pesapal_ipn_log
WHERE processed = true
GROUP BY tracking_id
HAVING COUNT(*) > 1;
```

### Check Transaction State

```sql
-- View transactions with PesaPal tracking IDs
SELECT id, reference, pesapal_order_tracking_id, state, amount
FROM payment_transaction
WHERE pesapal_order_tracking_id IS NOT NULL
ORDER BY create_date DESC
LIMIT 10;
```

### Check Appointment Confirmation

```sql
-- View appointments with payment status
SELECT id, name, state, payment_status, payment_reference
FROM custom_appointment
WHERE payment_transaction_id IS NOT NULL
ORDER BY create_date DESC
LIMIT 10;
```

## Expected Behavior

### Successful Payment Flow

1. Customer completes payment on PesaPal
2. PesaPal sends IPN to `/payment/pesapal/ipn`
3. System verifies payment with PesaPal API
4. IPN log created with status_code=1
5. Transaction state changes to 'done'
6. Appointment state changes to 'confirmed'
7. Confirmation emails sent to customer and staff
8. IPN marked as processed

### Duplicate IPN Handling

1. First IPN: Processes normally
2. Second IPN (duplicate): Detected and returns "OK - Already processed"
3. No duplicate processing occurs
4. Both IPNs logged for audit trail

### Failed Payment Flow

1. Payment fails on PesaPal
2. PesaPal sends IPN with status_code=2
3. Transaction state changes to 'cancel' or 'error'
4. Appointment payment_status set to 'failed'
5. No confirmation emails sent

## Troubleshooting

### IPN Not Received

1. **Check IPN URL** in PesaPal dashboard matches your Odoo URL
2. **Verify firewall** allows incoming requests from PesaPal IPs
3. **Check Odoo logs** for any errors: `docker compose logs odoo | grep -i pesapal`
4. **Test endpoint manually** with curl to ensure it's accessible

### IPN Received but Not Processing

1. **Check Odoo logs** for errors during processing
2. **Verify PesaPal credentials** are correct in payment provider settings
3. **Check transaction exists** with the tracking ID
4. **Review IPN log** for error messages

### Duplicate Processing

1. **Check IPN logs** for duplicate entries
2. **Verify processed flag** is being set correctly
3. **Review appointment state** - should not change on duplicate IPN

## Monitoring

### View IPN Logs in Odoo UI

1. Enable Developer Mode
2. Go to: Settings → Technical → Database Structure → Models
3. Search for: `pesapal.ipn.log`
4. Click "Records" to view all IPN notifications

### Key Fields to Monitor

- `tracking_id`: PesaPal order tracking ID
- `status_code`: Payment status (0=Pending, 1=Success, 2=Failed, 3=Reversed)
- `processed`: Whether IPN has been processed
- `transaction_id`: Related payment transaction
- `appointment_id`: Related appointment
- `error_message`: Any errors during processing
- `raw_data`: Complete IPN data received

## Security Notes

1. **IPN endpoint is public** (auth='public') as required by PesaPal
2. **Payment verification** is done via PesaPal API to ensure authenticity
3. **All IPNs are logged** for audit trail
4. **Duplicate detection** prevents replay attacks
5. **Error handling** prevents information leakage

## Support

For issues with IPN processing:
1. Check Odoo logs: `docker compose logs odoo | grep -i pesapal`
2. Review IPN logs in database
3. Verify PesaPal dashboard shows IPN was sent
4. Test endpoint accessibility with curl
5. Check PesaPal API credentials are valid
