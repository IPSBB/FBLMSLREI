# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    pos_sh_pos_switch_view = fields.Boolean(related='pos_config_id.sh_pos_switch_view', string="Enable Product Switch View", readonly=False)
    pos_sh_default_view = fields.Selection([('list_view', 'List View'), (
        'grid_view', 'Grid View')], related='pos_config_id.sh_default_view', string="Default Product View", readonly=False)
    pos_sh_display_product_name = fields.Boolean(related='pos_config_id.sh_display_product_name',
        string="Display Product Name", readonly=False)
    pos_sh_display_product_image = fields.Boolean(related='pos_config_id.sh_display_product_image',
        string="Display Product Image", readonly=False)
    pos_sh_display_product_price = fields.Boolean(related='pos_config_id.sh_display_product_price',
        string="Display Product Price", readonly=False)
    pos_sh_display_product_code = fields.Boolean(related='pos_config_id.sh_display_product_code',
        string="Display Product Code", readonly=False)
    pos_sh_display_product_type = fields.Boolean(related='pos_config_id.sh_display_product_type',string="Display Product Type", readonly=False)
    pos_sh_display_product_onhand = fields.Boolean(related='pos_config_id.sh_display_product_onhand',
        string="Display Product On Hand", readonly=False)
    pos_sh_display_product_forecasted = fields.Boolean(related='pos_config_id.sh_display_product_forecasted',
        string="Display Product Forecasted Quantity", readonly=False)
    pos_sh_display_product_uom = fields.Boolean(related='pos_config_id.sh_display_product_uom',string="Display Product UOM", readonly=False)
    pos_sh_product_image_size = fields.Selection([('small_size', 'Small Size'), ('medium_size', 'Medium Size'), (
        'large_size', 'Large Size')], related='pos_config_id.sh_product_image_size',string="Image Size", require="1", readonly=False)
