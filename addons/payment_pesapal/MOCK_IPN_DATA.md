# Mock PesaPal IPN Data Examples

This document provides example IPN data that PesaPal sends to the IPN endpoint.

## IPN Request Format

PesaPal sends IPN notifications as HTTP GET requests with query parameters:

```
GET /payment/pesapal/ipn?OrderTrackingId=<tracking_id>&OrderMerchantReference=<merchant_ref>
```

## Example 1: Successful Payment IPN

```bash
curl -X GET 'https://your-domain.com/payment/pesapal/ipn?OrderTrackingId=d8f4e5c6-1234-5678-90ab-cdef12345678&OrderMerchantReference=ODOO-123-1234567890'
```

**What happens:**
1. System receives IPN with tracking ID
2. Calls PesaPal API to verify transaction status
3. PesaPal API returns:
   ```json
   {
     "order_tracking_id": "d8f4e5c6-1234-5678-90ab-cdef12345678",
     "merchant_reference": "ODOO-123-1234567890",
     "status_code": 1,
     "payment_status_description": "Completed",
     "amount": 1000.00,
     "currency": "KES",
     "payment_method": "Visa Card",
     "created_date": "2025-10-18T14:30:00Z",
     "confirmation_code": "ABC123XYZ"
   }
   ```
4. Transaction state changes to 'done'
5. Appointment confirmed and emails sent
6. IPN logged with status_code=1

## Example 2: Failed Payment IPN

```bash
curl -X GET 'https://your-domain.com/payment/pesapal/ipn?OrderTrackingId=a1b2c3d4-5678-90ab-cdef-1234567890ab&OrderMerchantReference=ODOO-456-1234567890'
```

**PesaPal API Response:**
```json
{
  "order_tracking_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "merchant_reference": "ODOO-456-1234567890",
  "status_code": 2,
  "payment_status_description": "Failed",
  "error": "Insufficient funds"
}
```

**Result:**
- Transaction state changes to 'cancel'
- Appointment payment_status set to 'failed'
- No confirmation emails sent
- IPN logged with status_code=2

## Example 3: Pending Payment IPN

```bash
curl -X GET 'https://your-domain.com/payment/pesapal/ipn?OrderTrackingId=e5f6a7b8-90cd-1234-5678-90abcdef1234&OrderMerchantReference=ODOO-789-1234567890'
```

**PesaPal API Response:**
```json
{
  "order_tracking_id": "e5f6a7b8-90cd-1234-5678-90abcdef1234",
  "merchant_reference": "ODOO-789-1234567890",
  "status_code": 0,
  "payment_status_description": "Pending"
}
```

**Result:**
- Transaction remains in 'pending' state
- Appointment not confirmed yet
- IPN logged with status_code=0

## Example 4: Duplicate IPN (Already Processed)

```bash
# First IPN
curl -X GET 'https://your-domain.com/payment/pesapal/ipn?OrderTrackingId=d8f4e5c6-1234-5678-90ab-cdef12345678&OrderMerchantReference=ODOO-123-1234567890'
# Response: "OK"

# Second IPN (duplicate)
curl -X GET 'https://your-domain.com/payment/pesapal/ipn?OrderTrackingId=d8f4e5c6-1234-5678-90ab-cdef12345678&OrderMerchantReference=ODOO-123-1234567890'
# Response: "OK - Already processed"
```

**Result:**
- Duplicate detected by checking existing processed IPN logs
- No processing occurs
- Returns "OK - Already processed"
- Both IPNs logged for audit trail

## Example 5: Invalid IPN (Missing Tracking ID)

```bash
curl -X GET 'https://your-domain.com/payment/pesapal/ipn?OrderMerchantReference=ODOO-999-1234567890'
```

**Result:**
- Returns "Invalid notification"
- No processing occurs
- Error logged

## Example 6: Transaction Not Found

```bash
curl -X GET 'https://your-domain.com/payment/pesapal/ipn?OrderTrackingId=nonexistent-tracking-id&OrderMerchantReference=ODOO-999-1234567890'
```

**Result:**
- Returns "Transaction not found"
- IPN logged with error message
- No transaction processing

## PesaPal Status Codes

| Code | Status | Description |
|------|--------|-------------|
| 0 | Pending | Payment initiated but not completed |
| 1 | Completed | Payment successful |
| 2 | Failed | Payment failed |
| 3 | Reversed | Payment was reversed/refunded |

## Testing with Mock Data

### Step 1: Create Test Transaction in Odoo

```python
# In Odoo shell or via API
transaction = env['payment.transaction'].create({
    'provider_id': pesapal_provider_id,
    'reference': 'TEST-REF-001',
    'amount': 1000.0,
    'currency_id': env.ref('base.KES').id,
    'partner_id': partner_id,
    'pesapal_order_tracking_id': 'TEST-TRACK-001',
    'pesapal_merchant_reference': 'ODOO-TEST-001',
})
```

### Step 2: Mock PesaPal API Response

For testing, you can temporarily modify `_get_transaction_status()` to return mock data:

```python
def _get_transaction_status(self, provider, tracking_id):
    # Mock response for testing
    if tracking_id.startswith('TEST-'):
        return {
            'order_tracking_id': tracking_id,
            'status_code': 1,  # Completed
            'payment_status_description': 'Completed',
            'amount': 1000.00,
            'currency': 'KES',
        }
    # ... rest of actual implementation
```

### Step 3: Send Test IPN

```bash
curl -X GET 'http://localhost:8069/payment/pesapal/ipn?OrderTrackingId=TEST-TRACK-001&OrderMerchantReference=ODOO-TEST-001'
```

### Step 4: Verify Results

```sql
-- Check IPN log
SELECT * FROM pesapal_ipn_log WHERE tracking_id = 'TEST-TRACK-001';

-- Check transaction state
SELECT state FROM payment_transaction WHERE pesapal_order_tracking_id = 'TEST-TRACK-001';

-- Check appointment confirmation
SELECT state, payment_status FROM custom_appointment 
WHERE payment_transaction_id = (
    SELECT id FROM payment_transaction WHERE pesapal_order_tracking_id = 'TEST-TRACK-001'
);
```

## Real PesaPal IPN Example

When PesaPal sends a real IPN, it looks like this:

```
GET /payment/pesapal/ipn?OrderTrackingId=d8f4e5c6-1234-5678-90ab-cdef12345678&OrderMerchantReference=ODOO-123-1234567890 HTTP/1.1
Host: your-domain.com
User-Agent: PesaPal-IPN/1.0
Accept: */*
```

The system then:
1. Extracts `OrderTrackingId` and `OrderMerchantReference`
2. Finds the transaction in database
3. Calls PesaPal API to verify status
4. Processes payment based on status_code
5. Logs IPN for audit
6. Returns "OK" or error message

## Debugging Tips

### Enable Detailed Logging

Add to Odoo config:
```ini
log_level = debug
log_handler = :DEBUG,werkzeug:INFO,odoo.addons.payment_pesapal:DEBUG
```

### View IPN Logs

```bash
# Docker
docker compose logs odoo | grep -i "PesaPal IPN"

# Direct
tail -f /var/log/odoo/odoo.log | grep -i "PesaPal IPN"
```

### Check Database Directly

```sql
-- Recent IPNs
SELECT 
    id,
    tracking_id,
    status_code,
    status_description,
    processed,
    create_date
FROM pesapal_ipn_log
ORDER BY create_date DESC
LIMIT 10;

-- Unprocessed IPNs
SELECT * FROM pesapal_ipn_log WHERE processed = false;

-- Duplicate IPNs
SELECT tracking_id, COUNT(*) as count
FROM pesapal_ipn_log
GROUP BY tracking_id
HAVING COUNT(*) > 1;
```
