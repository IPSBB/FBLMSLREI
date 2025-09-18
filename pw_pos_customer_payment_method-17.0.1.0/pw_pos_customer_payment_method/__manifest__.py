# -*- coding: utf-8 -*-
{
    'name': 'POS Customer Payment Method | POS Customer Wise Payment Method | Restrict payment method on pos by customer',
    'version': '1.0',
    'author': 'Preway IT Solutions',
    'category': 'Point of Sale',
    'depends': ['point_of_sale'],
    'summary': 'This module helps you to set payment method on customer to only make payment from allowed methods for the customer | POS Customer Special Method | POS Customer Payment Method | Customer Specific Payment Method on POS | Payment method restriction | POS Payment Restrictions',
    'description': """
  This module is allow add restriction on customers to load on pos screen
    """,
    'data': [
        'views/res_partner_view.xml',
        'views/pos_config_view.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pw_pos_customer_payment_method/static/src/js/models.js',
            'pw_pos_customer_payment_method/static/src/xml/PaymentScreen.xml',
        ],
    },
    'price': 30.0,
    'currency': "EUR",
    'application': True,
    'installable': True,
    "auto_install": False,
    "license": "LGPL-3",
    "images":["static/description/Banner.png"],
}
