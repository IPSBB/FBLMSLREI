{
    'name': 'POS Margin Reports',
    'version': '17.0.1.0.0',
    'category': 'Point of Sale',
    'summary': """Generates POS Margin reporting from
    menu""",
    'description': """Generates POS Margin reporting from
    menu.""",
    'author': 'EGYPOS, Ali Elnagar',
    'price': 30,
    'currency ': 'EUR',
    'support ': 'ali.aa.elnagar@gmail.com',
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/advanced_pos_reports_wizard.xml',
        'wizard/pos_sale_margin_selling_views.xml',
        'report/advanced_pos_reports.xml',
        'report/pos_margin_products_templates.xml',
    ],

    'images': ['static/description/banner.png'],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': False,
}
