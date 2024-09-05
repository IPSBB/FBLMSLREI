# -*- coding: utf-8 -*-
{
    'name': 'POS_Order_Signature | POS Signature',
    'category': 'Point of Sale',
    'summary': 'This module help you to add signature on pos order and receipt | POS Signature | Signature on POS Receipt | POS Order Receipt Signature',
    'description': """
This module help you to add signature on pos order and receipt""",
    'author': 'Preway IT Solutions',
    'version': '1.0',
    'depends': ['point_of_sale'],
    "data": [
        'views/pos_config_view.xml'
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pw_pos_signature/static/src/js/models.js',
            'pw_pos_signature/static/src/lib/jSignature.min.js',
            'pw_pos_signature/static/src/input_popups/signature_popup.js',
            'pw_pos_signature/static/src/js/PaymentScreen.js',
            'pw_pos_signature/static/src/xml/**/*',
        ],
    },
    'price': 10.0,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
    'application': True,
    "license": "LGPL-3",
    "images":["static/description/Banner.png"],
}
