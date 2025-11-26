from odoo import fields, models, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    is_landed_bill = fields.Boolean('Is Landed Costs Bill', default=False)
    
    def button_create_landed_costs(self):
        """Create a `stock.landed.cost` record associated to the account move of `self`, each
        `stock.landed.costs` lines mirroring the current `account.move.line` of self.
        """
        self.ensure_one()
        landed_costs_lines = self.line_ids.filtered(lambda line: line.is_landed_costs_line)
        cost_lines = [(0, 0, {
                'product_id': l.product_id.id,
                'name': l.product_id.name,
                'account_id': l.product_id.product_tmpl_id.get_product_accounts()['stock_input'].id,
                'price_unit': l.currency_id._convert(l.price_subtotal, l.company_currency_id, l.company_id, l.move_id.date),
                'split_method': l.product_id.split_method_landed_cost or 'equal',
            }) for l in landed_costs_lines]
        landed_costs = self.env['stock.landed.cost'].create({
            'vendor_bill_ids': [(6, 0, [self.id])],
        })
        action = self.env["ir.actions.actions"]._for_xml_id("stock_landed_costs.action_stock_landed_cost")
        return dict(action, view_mode='form', res_id=landed_costs.id, views=[(False, 'form')])



class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    harmonized_code_id = fields.Many2one('import_fees.harmonized_code', store=True, readonly=True,
                                     help="Harmonized System Code, used to classify a product in import/export trade.", compute='_compute_harmonized_code_id')

    @api.depends('product_id')
    def _compute_harmonized_code_id(self):
        for record in self:
            record.harmonized_code_id = record.product_id.search_harmonized_code_id()


