# Part of Odoo. See LICENSE file for full copyright and licensing details.

# The currencies supported by kPay, in ISO 4217 format.
# Last website update: March 2024.
# Last seen online: 16 March 2024.
SUPPORTED_CURRENCIES = [
    'UGX','KES',
]
#APIKEY: 497f1389b452f47218f4eead07f0f357f536b139
#CLEINTID: pHJ3x3K9IJBRHI8Xja5Fi017Oui70w6xL4WZtSddsnK
#PUBLIC_KEY: LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUlJQ0lqQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FnOEFNSUlDQ2dLQ0FnRUEyV0RkMGE5UFVqd25Zekp2QWxHUQowcGpNcGViaWpvQXlHYWxCRVZiNC85N3dpbWFhVTNZbFdmU3FMNkV4Vnpnd3ZlK3NqcnN1czRzQThCbWM0aVZkClFTMlZTbWI1elowbWZNMEZLejFZWjlZSEMrcS9xa01NV05ETGJGYkhaZVNUN0trbXN4d3h5VDF3RVdBc3JETU0KWDVUbEVlNE1MaC92QXFDbGpRWGR0bUdXa09MVWI1WkFxQmhNS3IvSXR4ZmVldGwySXhzMVVzb2xsSEc0djNHRAo2c00zeVhCQ1lQTXlXS0VPYS9BRDlCK1VSSUFkaUdYOHk4RnVqQlhzdnYvNkU2ZU9XWjZnZWIwQkJIUm5ydmIzCjZFMDF0ZVQ4REZDRXdibUl1SXBIdERrSHlFWjNweDhNQmFHeDV1ZHcyWDlVOHlLaXdJOGFHRWxvRmN0bXBya0gKKzdTaTdDMnR1Tm9BY0VOZlNZN1NYd0c0MGlva2Y2L0RNMVJKbXhZajJLaW9nczVlaWIzWHdGZkNKVm1wVWxZVgpqNTd6Zm1ySlNLRUNsU0t1S2VyT0N2RlRDeWJrNjRkckg2N2dicC9pT3FtWDZYUklSR3dyZlR3emdkcVE0SS9lCk50azEyTklMblhvaHVsUkMzV0p5czhNbHkwaFVwSWVoVFdSc1A4bWZQK2MxbGFIT0d3RlF2dTRXdXh1b1BFMEsKYzZEaTZnbFhoOFQ2OHRPN2hwTTd1MUFwY1hhTjJDcmgzTGlpbzRNcVFzak9Ga0lPdEo3NDlza283b2JKemZ2Nwo1VUNSUWx4VWRlZFZwODV2RjJ3Z0VsWmdDaTIxU3hFMDMzN3VESENSYk52d0Q0QzBZaUtLS2JpZlpuQ1ZtRmtKCkcxU014akpUL0FUUDB5WlY3czc4U3hjQ0F3RUFBUT09Ci0tLS0tRU5EIFBVQkxJQyBLRVktLS0tLQo=


# Mapping of transaction states to KPay payment statuses.
PAYMENT_STATUS_MAPPING = {
    'pending': ['pending auth'],
    'done': ['successful'],
    'cancel': ['cancelled'],
    'error': ['failed'],
}

# The codes of the payment methods to activate when KPay is activated.
DEFAULT_PAYMENT_METHODS_CODES = [
    # Primary payment methods.
    'eagle_mtn',
    'eagle_airtel',
    'eagle_mpesa'

]

PAYMENT_METHODS_MAPPING = {
    'bank_transfer': 'banktransfer',
}
