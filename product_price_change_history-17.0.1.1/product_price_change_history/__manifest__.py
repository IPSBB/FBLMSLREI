# -*- coding: utf-8 -*-

{
    'name': 'Price Changes History',
    'version': '1.1',
    'summary': """Product Price Changes History""",
    'description': """Product Price Changes History""",
    'category': 'Base',
    'author': 'bisolv',
    'website': "www.bisolv.com",
    'license': 'AGPL-3',

    'price': 15.0,
    'currency': 'USD',

    'depends': ['product'],

    'data': [
        'security/ir.model.access.csv',
        'views/product_view.xml',
    ],
    'demo': [

    ],
    'images': ['static/description/banner.png'],
    'qweb': [],

    'installable': True,
    'auto_install': False,
    'application': False,
}
