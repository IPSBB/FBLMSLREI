{
    'name': 'POS Gross Profit Margin Report',
    'version': '18.0.0.1',
    'category': 'pos',
    'summary': 'Pos Gross Profit Margin Report',
    'author': 'TeamUp4Solutions, TaxDotCom',
    'website': 'http://taxdotcom.org/',
    'maintainer': 'Asim Umer',
    'depends': ['base', 'uom', 'sale', 'sale_stock', 'stock', 'point_of_sale', 'report_xlsx'],  # ,'stock_account'
    'data': [
        # 'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/update_recipe_product_wizard.xml',
        'reports/report.xml',
        'views/pos_assets.xml',
        'views/stock_move_line.xml',
        'views/menus.xml',
        'data/ir_sequence.xml',
        'data/stock_location_data.xml',

    ],
    # 'assets': {
    #     'point_of_sale.assets': [
    #         'ts_pos_profit_margin_report/static/src/js/pos.js'
    #     ]
    # },
    'installable': True,
    'auto_install': False,
    'price': 35.00,
    'currency': 'EUR',
    'images': ['static/description/icon.png'],
    'license': 'AGPL-3',
}
