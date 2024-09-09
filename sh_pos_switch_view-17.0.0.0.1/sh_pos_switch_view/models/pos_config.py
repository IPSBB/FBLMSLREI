# Copyright (C) Softhealer Technologies.
# Part of Softhealer Technologies.

from odoo import models, fields


class PosConfig(models.Model):
    _inherit = "pos.config"

    sh_pos_switch_view = fields.Boolean(string="Enable Product Switch View")
    sh_default_view = fields.Selection([('list_view', 'List View'), (
        'grid_view', 'Grid View')], default="grid_view", string="Default Product View")
    sh_display_product_name = fields.Boolean(
        string="Display Product Name", default="true")
    sh_display_product_image = fields.Boolean(
        string="Display Product Image", default="true")
    sh_display_product_price = fields.Boolean(
        string="Display Product Price", default="true")
    sh_display_product_code = fields.Boolean(
        string="Display Product Code", default="true")
    sh_display_product_type = fields.Boolean(string="Display Product Type")
    sh_display_product_onhand = fields.Boolean(
        string="Display Product On Hand", default="true")
    sh_display_product_forecasted = fields.Boolean(
        string="Display Product Forecasted Quantity")
    sh_display_product_uom = fields.Boolean(string="Display Product UOM")
    sh_product_image_size = fields.Selection([('small_size', 'Small Size'), ('medium_size', 'Medium Size'), (
        'large_size', 'Large Size')], default="medium_size", string="Image Size", require="1")
