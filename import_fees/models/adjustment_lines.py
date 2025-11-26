from odoo import models, fields, api, _

# Add cost line product to stock valuation adjustment lines

class AdjustmentLines(models.Model):
    _inherit = 'stock.valuation.adjustment.lines'
    cost_line_product_id = fields.Many2one(related='cost_line_id.product_id', string='Cost', readonly=True)

