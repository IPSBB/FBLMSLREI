# Part of Softhealer Technologies.
{
    "name": "Point Of Sale Product Switch View",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Point of Sale",
    "license": "OPL-1",
    "summary": "POS Product Switch View Point Of Sale Switch Product View POS Switch Product View POS Product View Switch Point Of Sale Product View Switch POS Change Product View POS Change View list view grid view POS Switch View switch product screen Odoo Point Of Sale Product List View Point Of Sale Product Grid View POS Product List View POS product Grid View Switch Product List View Switch Product Grid View Odoo POS View POS Product Views Point of Sale View POS List View POS Grid View Point of sale Views Point of Sale List View Point Of Sale Product Views POS View Switch POS View Point of Sale Switch View POS Product Views",
    "description": """This module facilitates POS user to change product view in the POS product screen. POS user can set default view or can switch between grid view and list view during the running POS Session. In the list view, we provide the option to select the product details to show in the list view, such as product name, price, code, type, on-hand quantity, forecasted quantity, UOM & image with flexible size like small, medium & large.""",
    "version": "0.0.1",
    "depends": ["point_of_sale"],
    "application": True,
    "data": [
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'sh_pos_switch_view/static/src/**/*',
        ],
    },
    "auto_install": False,
    "installable": True,
    "images": ["static/description/background.png", ],
    "price": 20,
    "currency": "EUR"
}
