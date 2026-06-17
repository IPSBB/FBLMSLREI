{
    'name': 'POS Gross Profit Margin Report',
    'version': '17.0.0.1',
    'category': 'pos',
    'summary': 'Pos Gross Profit Margin Report',
    'author': 'TeamUp4Solutions, TaxDotCom',
    'website': 'http://taxdotcom.org/',
    'maintainer': 'Asim Umer',
    'depends': ['base', 'uom', 'sale', 'sale_stock', 'stock', 'point_of_sale', 'report_xlsx'],
    'data': [
        'security/ir.model.access.csv',
        'reports/report.xml',
        'views/menus.xml',

    ],
    'installable': True,
    'auto_install': False,
    'price': 35.00,
    'currency': 'EUR',
    'images': ['static/description/icon.png'],
    'license': 'AGPL-3',
}
