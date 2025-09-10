# -*- coding: utf-8 -*-
{
    'name': "Eagle Mpesa Client",
    'summary': "Eagle Mpesa Client",
    'description': """ "Eagle Mpesa Client """,
    'author': "Kola Technologies Limited",
    'website': "https://www.kolapro.com",

    'version': '18.0.0.1',
    'category': 'Accounting/Payment Providers',
    'sequence': 250,
    'support': 'support@kolapro.com',
    'live_test_url': 'https://kolapro.com/contactus',
    'depends': [
        'account','product','hr_expense','point_of_sale',
    ],

    'data': [
        
        #--------security files--------#
        "security/security.xml",
        "security/record_rules.xml",
        "security/ir.model.access.csv",
       
        
        #------data files -------#
        "data/ir_sequence_data.xml",        
        "data/mail_template.xml",        
        "data/notify.xml",        

        #------report files -------#

        #----wizard files -------#
        
        #--------views--------#
        "views/company/res_company.xml",
        "views/company/res_config_settings.xml",
        "views/payments/eagle_payment.xml",
        "views/payments/payment_batch.xml",
        "views/payments/account_journal.xml",
        # "views/payslips/hr_payslip_run.xml",
        "views/wallets/user_wallets.xml",
        "views/wallets/account_request.xml",
        "views/wallets/wallet_transactions.xml",
        # "views/wallets/funds_request.xml",

        #wizards
        "wizards/messages/wizard_wallet.xml",
        "wizards/messages/wizard_payment.xml",
        "wizards/messages/reject_payment.xml",



        #--------menus--------#
        "views/menus.xml",
       
       

    ],

    "assets": {
        "web.assets_backend": [
            'eagle_mpesa_client/static/src/css/verification_code.css',
            
            # 'eagle_mpesa_client/static/src/js/form_view_auto_refresh.js',
            
        ],
        "web.assets_qweb": [
        
        ],
        
    },
    
    'images': ['static/img/FishEagle.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'application': True,
}
