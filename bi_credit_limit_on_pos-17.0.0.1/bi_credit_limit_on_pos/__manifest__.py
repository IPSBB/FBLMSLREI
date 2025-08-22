# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    "name": "Point of Sale Credit Limit/Credit Limit on POS",
    "version": "17.0.0.1",
    "category": "Point of Sale",
    'summary': 'POS customer credit limit on point of sale customer credit limit on pos credit limit pos credit amount customer credit on pos customer credit payment pos partial credit pos payment with credit pos partial payment allow customer credit on pos payment limit',
    "description": """

        POS Credit Limit in odoo,
        Allow Credit Limit in odoo,
        Set Amount to Raise Warning in odoo,
        Set Amount to Block Credit Order in odoo,
        Warning if Credit Exceeding Warning Limit in odoo,
        Warning if Credit Exceeding Blocking Limit in odoo,
        Credit for the Customers in odoo,
        Warning or Validation Message in odoo,

    """,
    "author": "BROWSEINFO",
    "price": 39,
    "currency": 'EUR',
    "website": 'https://www.browseinfo.com/demo-request?app=bi_credit_limit_on_pos&version=17&edition=Community',
    "depends": ['base', 'point_of_sale'],
    "data": [
        'views/account_journal.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'bi_credit_limit_on_pos/static/src/js/Screens/PaymentScreen/PaymentScreen.js',
            'bi_credit_limit_on_pos/static/src/js/Screens/ClientScreen/ClientListScreen.js',
            'bi_credit_limit_on_pos/static/src/js/Popups/BiWarningPopup.js',
            'bi_credit_limit_on_pos/static/src/js/Popups/BiWarningBlockingPopup.js',
            'bi_credit_limit_on_pos/static/src/xml/pos.xml',
        ],
    },
    'license': 'OPL-1',
    "auto_install": False,
    "installable": True,
    "live_test_url":'https://www.browseinfo.com/demo-request?app=bi_credit_limit_on_pos&version=17&edition=Community',
    "images":["static/description/Banner.gif"],
}
