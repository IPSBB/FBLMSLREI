from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _sales_consumption_count(self):
        for record in self:
            inv_id = self.env['stock.consumption'].search(
                [('sale_order_id', '=', record.id)])
            record.sales_conpt_count = len(inv_id)
        return

    sales_conpt_count = fields.Integer('Consumption', compute="_sales_consumption_count")
    # show_sale_order_field = fields.Boolean(compute='_compute_show_sale_order_field')

    def sales_consumption_list(self):
        return {
            'name': "Consumption",
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(self.env.ref('ts_pos_profit_margin_report.view_consumption_tree').id, 'tree'),
                      (self.env.ref('ts_pos_profit_margin_report.view_consumption_form').id, 'form')],
            'res_model': 'stock.consumption',
            'type': 'ir.actions.act_window',
            'target': 'Current',
            'domain': "[('id', 'in', %s)]" % self.env['stock.consumption'].search(
                [('sale_order_id', '=', self.id)]).ids,
        }

    def action_confirm(self):
        product_list = [];
        location_list = []
        res = super(SaleOrder, self).action_confirm()
        sale_lines = self.order_line
        for f in sale_lines:
            if f.product_id.product_tmpl_id.is_recipe:
                for t in f.product_id.product_tmpl_id.recipe_structure_ids:
                    product_list.append(t.product_id.id)
                    location_list.append(t.location_id.id)
                consumption_id = self.env['stock.consumption'].create(
                    {'location_ids': location_list, 'product_ids': product_list,
                     'sale_order_id': self.id})
                consumption_id.action_start()
                stock_consum_line_ids = self.env['stock.consumption.lines'].search(
                    [('consumption_id', '=', consumption_id.id)])
                for inv in stock_consum_line_ids:
                    for recipe in f.product_id.product_tmpl_id.recipe_structure_ids:
                        if recipe.product_id.id == inv.product_id.id:
                            inv.consume_qty = recipe.qty_to_consum * f.product_uom_qty
                    inv._compute_inventory_quantity()
                consumption_id.action_validate()
        return res
