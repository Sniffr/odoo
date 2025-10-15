# PesaPal Payment Provider for Odoo

This module integrates PesaPal payment gateway with Odoo, enabling secure online payments through PesaPal's hosted checkout.

## Features

- **Hosted Checkout**: Redirects customers to PesaPal's secure payment page
- **Multiple Payment Methods**: Cards, Mobile Money (M-Pesa, Airtel Money, etc.), Bank transfers
- **IPN Support**: Instant Payment Notifications for real-time payment updates
- **Multi-Currency**: Supports multiple African currencies
- **Production & Sandbox**: Test mode for development, production mode for live transactions

## Installation

1. Copy the `payment_pesapal` folder to your Odoo addons directory
2. Update the apps list in Odoo
3. Install the "Payment Provider: PesaPal" module

## Configuration

### 1. Get PesaPal Credentials

- Go to [PesaPal Business Portal](https://www.pesapal.com/)
- Sign up or log in to your account
- Navigate to API Integration section
- Copy your Consumer Key and Consumer Secret

### 2. Configure in Odoo

1. Go to **Settings → Payment Providers**
2. Find **PesaPal** in the list
3. Fill in the following:
   - **Consumer Key**: Your PesaPal consumer key
   - **Consumer Secret**: Your PesaPal consumer secret
   - **IPN URL**: Auto-generated (can be customized if needed)
   - **State**: Set to "Test" for sandbox or "Enabled" for production
4. Click **Published** to make it available to customers
5. Save

### 3. Configure IPN in PesaPal Portal

1. Log in to your PesaPal Business Portal
2. Go to API Settings → IPN Configuration
3. Add your IPN URL (shown in Odoo): `https://yourdomain.com/payment/pesapal/ipn`
4. Save the configuration

## Usage

### For Customers

1. When checking out, select "PesaPal" as the payment method
2. Click "Pay Now"
3. You'll be redirected to PesaPal's secure checkout page
4. Choose your payment method (Card, Mobile Money, etc.)
5. Complete the payment
6. You'll be redirected back to the website automatically

### For Administrators

- View all PesaPal transactions in **Accounting → Payments → Transactions**
- Transaction status updates automatically via IPN
- Check logs for troubleshooting: `docker logs odoo-odoo-1 | grep PesaPal`

## API Endpoints

- **Production**: `https://pay.pesapal.com/v3`
- **Sandbox**: `https://cybqa.pesapal.com/pesapalv3`

The module automatically uses the correct endpoint based on the provider state.

## Payment Flow

1. Customer initiates payment
2. Odoo authenticates with PesaPal API
3. Odoo registers IPN URL (if needed)
4. Odoo submits order to PesaPal
5. Customer redirected to PesaPal hosted checkout
6. Customer completes payment on PesaPal
7. PesaPal sends IPN to Odoo
8. Customer redirected back to Odoo
9. Order confirmed automatically

## Troubleshooting

### Payment Not Completing

- Check that IPN URL is correctly configured in PesaPal portal
- Verify Consumer Key and Secret are correct
- Check Odoo logs for errors
- Ensure your domain is accessible from the internet (not localhost)

### IPN Not Working

- Verify IPN URL is publicly accessible
- Check firewall settings
- Test IPN URL manually: `curl https://yourdomain.com/payment/pesapal/ipn`
- Check logs: `docker logs odoo-odoo-1 | grep "PesaPal IPN"`

### Authentication Failures

- Verify credentials are correct
- Check if you're using production credentials with test mode (or vice versa)
- Ensure credentials don't have extra spaces

## Support

For issues with:
- **Odoo Integration**: Check Odoo logs and transaction records
- **PesaPal API**: Contact PesaPal support at support@pesapal.com
- **Credentials/Account**: Log in to PesaPal Business Portal

## License

LGPL-3
