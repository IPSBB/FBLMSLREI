{
    'name': 'Create Sales Order From POS',
    'version': '17.0',
    'category': 'Sales/Point of Sale',
    'summary': 'Create sale order from pos screen and view the sales order created fom pos',
    'description': '''
    ''',
    'author': 'Warlock Technologies Pvt Ltd.',
    'website': 'http://warlocktechnologies.com',
    'support': 'support@warlocktechnologies.com',
    'depends': ['point_of_sale', 'sale_management','web','pos_sale'],
    "data": ['views/pos_config.xml'],
    'assets': {
        'point_of_sale._assets_pos': [
            'wt_create_so_from_pos/static/src/js/Screens/ProductScreen/ControlButtons/SaleOrderButton.js',
            'wt_create_so_from_pos/static/src/js/Screens/ProductScreen/ControlButtons/ViewSalesOrderButton.js',
            'wt_create_so_from_pos/static/src/js/Screens/SaleOrderScreen/SaleOrderScreen.js',
            'wt_create_so_from_pos/static/src/js/Popups/SalesOrderPopup.js',
            'wt_create_so_from_pos/static/src/xml/**/*'
        ],
        # 'point_of_sale.assets': [

        # ],
        
    },
    'images': ['static/images/screen_image.png'],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'OPL-1',
    'external_dependencies': {
    },
}
