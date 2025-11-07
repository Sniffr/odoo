#!/usr/bin/env python3
import odoo
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['-d', 'odoo', '-c', '/etc/odoo/odoo.conf'])
dbname = 'odoo'

registry = odoo.registry(dbname)
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    pesapal_method = env['payment.method'].search([('code', '=', 'pesapal')], limit=1)
    if not pesapal_method:
        pesapal_method = env['payment.method'].create({
            'name': 'PesaPal',
            'code': 'pesapal',
            'sequence': 10,
            'support_tokenization': False,
            'support_express_checkout': False,
            'support_refund': 'none',
        })
        print(f"Created PesaPal payment method: {pesapal_method.id}")
    else:
        print(f"PesaPal payment method already exists: {pesapal_method.id}")

    pesapal_provider = env['payment.provider'].search([('code', '=', 'pesapal')], limit=1)
    if not pesapal_provider:
        pesapal_provider = env['payment.provider'].create({
            'name': 'PesaPal',
            'code': 'pesapal',
            'state': 'test',
        })
        print(f"Created PesaPal provider: {pesapal_provider.id}")
    else:
        print(f"PesaPal provider already exists: {pesapal_provider.id}")

    mpesa_provider = env['payment.provider'].search([('code', '=', 'mpesa')], limit=1)
    if not mpesa_provider:
        mpesa_provider = env['payment.provider'].create({
            'name': 'M-Pesa',
            'code': 'mpesa',
            'state': 'test',
        })
        print(f"Created M-Pesa provider: {mpesa_provider.id}")
    else:
        print(f"M-Pesa provider already exists: {mpesa_provider.id}")

    mpesa_method = env['payment.method'].search([('code', '=', 'mpesa')], limit=1)
    if mpesa_method:
        print(f"M-Pesa payment method exists: {mpesa_method.id}")
    else:
        print("M-Pesa payment method not found!")

    bank_journals = env['account.journal'].search([('type', '=', 'bank')])
    print(f"Found {len(bank_journals)} bank journals")

    for journal in bank_journals:
        if pesapal_provider and pesapal_method:
            existing_line = env['account.payment.method.line'].search([
                ('payment_provider_id', '=', pesapal_provider.id),
                ('payment_method_id', '=', pesapal_method.id),
                ('journal_id', '=', journal.id)
            ], limit=1)
            
            if not existing_line:
                line = env['account.payment.method.line'].create({
                    'name': f'PesaPal - {journal.name}',
                    'payment_provider_id': pesapal_provider.id,
                    'payment_method_id': pesapal_method.id,
                    'journal_id': journal.id,
                })
                print(f"Created PesaPal payment method line for journal {journal.name}: {line.id}")
            else:
                print(f"PesaPal payment method line already exists for journal {journal.name}")
        
        if mpesa_provider and mpesa_method:
            existing_line = env['account.payment.method.line'].search([
                ('payment_provider_id', '=', mpesa_provider.id),
                ('payment_method_id', '=', mpesa_method.id),
                ('journal_id', '=', journal.id)
            ], limit=1)
            
            if not existing_line:
                line = env['account.payment.method.line'].create({
                    'name': f'M-Pesa - {journal.name}',
                    'payment_provider_id': mpesa_provider.id,
                    'payment_method_id': mpesa_method.id,
                    'journal_id': journal.id,
                })
                print(f"Created M-Pesa payment method line for journal {journal.name}: {line.id}")
            else:
                print(f"M-Pesa payment method line already exists for journal {journal.name}")

    cr.commit()
    print("Done!")
